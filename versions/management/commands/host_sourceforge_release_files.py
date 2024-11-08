from dataclasses import asdict, dataclass
from datetime import datetime
from io import BytesIO
import json

import hashlib
import requests
from requests.adapters import HTTPAdapter, Retry

from bs4 import BeautifulSoup
import djclick as click
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

from versions.models import Version

# TODO: change to actual bucket and key used for archives.boost.io and modify
#   AWS credential settings to match.
BUCKET_NAME = "stage-rob.boost.org.v2"
S3_KEY_PREFIX = "test/boost-archives/release"

session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=1,  # Exponential backoff (e.g., 1, 2, 4, 8 seconds)
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)


@click.command()
@click.option("--release", is_flag=False, help="Release name")
def command(release):
    """
    Import release data from SourceForge, and copy the files to S3.

    This command will download and host release files from SourceForge for the
    specified release. If no release is specified, it will import the release data
    for all releases included in Artifactory.
    """
    settings.LOCAL_DEVELOPMENT = False  # must turn off to use S3
    last_release_needed = "1.61.0"

    if release:
        versions = Version.objects.filter(name__icontains=release)
    else:
        versions = Version.objects.filter(name__lte=last_release_needed)

    for v in versions:
        try:
            print(f"\nGathering download file data for {v}")
            sourceforge_file_data = gather_sourceforge_files_for_release(v)
        except requests.exceptions.HTTPError:
            print(f"Skipping {v}, error retrieving file data")
            continue

        for file in sourceforge_file_data:
            try:
                download_and_upload_with_metadata(file)
            except requests.exceptions.HTTPError:
                print(f"Skipping {file.file}, error retrieving file")
                continue


@dataclass
class SourceForgeFile:
    commit: str
    file: str
    created: str
    download_link: str
    release: str  # e.g. 1.62.0
    sha256: str = ""  # calculated later

    def to_json(self):
        # Exclude 'download_link' and 'release' when converting to JSON
        data_dict = asdict(self)
        data_dict.pop("download_link")
        data_dict.pop("release")
        return json.dumps(data_dict, indent=4)


def gather_sourceforge_files_for_release(version: Version) -> list[SourceForgeFile]:
    file_extensions = [".tar.bz2", ".tar.gz", ".7z", ".zip"]

    commit = version.data["commit"]["sha"]
    release = version.name.strip("boost-")
    sf_release_path = f"{settings.SOURCEFORGE_URL}/{release}/"

    resp = session.get(sf_release_path)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    file_table = soup.find(id="files_list")
    file_rows = file_table.select("tr.file")

    data = []

    for row in file_rows:
        file_name = row["title"]
        if not any(file_name.endswith(ext) for ext in file_extensions):
            print(f"Skipping file {file_name} due to unsupported extension")
            continue

        download_link = row.select_one("th a")["href"]

        date_str = row.select_one("td[headers='files_date_h'] abbr")["title"]
        # Convert date to ISO format
        created = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S UTC").strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        # Create a FileData instance and append it to the list
        data.append(
            SourceForgeFile(
                commit=commit,
                file=file_name,
                created=created,
                release=release,
                download_link=download_link,
            )
        )

    return data


def download_and_upload_with_metadata(source_file: SourceForgeFile):
    """
    Download file from SourceForge, then upload the release file and
    a json metadata file to S3.
    """

    sha256_hash = hashlib.sha256()
    storage = S3Boto3Storage(bucket_name=BUCKET_NAME)

    print(f"\nDownloading {source_file.file}")
    response = session.get(source_file.download_link)
    response.raise_for_status()

    # Read the entire file content into memory
    file_content = response.content

    # Calculate SHA256 hash and update the SourceForgeFile instance
    sha256_hash.update(file_content)
    source_file.sha256 = sha256_hash.hexdigest()

    # Construct the S3 key (path) for the file and the JSON metadata
    s3_key = f"{S3_KEY_PREFIX}/{source_file.release}/source/{source_file.file}"
    json_s3_key = f"{s3_key}.json"

    # Use BytesIO to upload the file to S3
    file_buffer = BytesIO(file_content)

    print(f"Uploading {source_file.file} to S3")
    storage.save(s3_key, file_buffer)

    # Save the metadata as a JSON file in S3
    metadata_json = source_file.to_json()
    json_buffer = BytesIO(metadata_json.encode("utf-8"))

    print("Uploading metadata json file")
    storage.save(json_s3_key, json_buffer)

    print("\nSHA256 Hash:", source_file.sha256)
    print(f"File uploaded to S3 with key '{s3_key}'")
    print(f"Metadata JSON uploaded to S3 with key '{json_s3_key}'")
