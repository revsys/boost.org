from dataclasses import asdict, dataclass
from datetime import datetime
from io import BytesIO
import json
from xml.etree import ElementTree

import hashlib
import requests
from requests.adapters import HTTPAdapter, Retry

import djclick as click
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

from versions.models import Version

SOURCEFORGE_RSS_URL = "https://sourceforge.net/projects/boost/rss?path=/boost/{release}"

# Note: S3 credentials must be set correctly in your environment / Django settings
# for the bucket you use below
BUCKET_NAME = "stage-rob.boost.org.v2"  # TODO: change for "production" run
S3_KEY_PREFIX = "test/boost-archives/release"  # TODO: change for "production" run


LAST_VERSION_NEEDED = "1.62.0"

session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=1,  # Exponential backoff (e.g., 1, 2, 4, 8 seconds)
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)


@click.command()
@click.option("--release", is_flag=False, help="Release name")
@click.option("--dry-run", is_flag=True, help="Skip actual import")
def command(release, dry_run):
    """
    Import release data from SourceForge, and copy the files to S3.

    This command will download and host release files from SourceForge for the
    specified release. If no release is specified, it will import the release data
    for all releases included in Artifactory.
    """
    settings.LOCAL_DEVELOPMENT = False  # must turn off to use S3

    if release:
        versions = Version.objects.filter(name__icontains=release)
    else:
        versions = Version.objects.filter(
            name__lte=f"boost-{LAST_VERSION_NEEDED}"
        ).order_by("-name")

    num_versions = len(versions)

    for idx, v in enumerate(versions, start=1):
        try:
            suffix = f" ({idx}/{num_versions})" if num_versions > 1 else ""
            print(f"\nGathering download file data for {v}{suffix}")
            sourceforge_file_data = gather_sourceforge_files_for_release(v)
        except requests.exceptions.HTTPError:
            print(f"Skipping {v}, error retrieving file data")
            continue

        for file in sourceforge_file_data:
            try:
                if dry_run:
                    print(f"Dry run: skipping import of {file.file}")
                    continue
                download_and_upload_with_metadata(file)
            except requests.exceptions.HTTPError:
                print(f"Skipping {file.file}, error downloading file")
                continue


@dataclass
class SourceForgeFile:
    commit: str
    file: str
    created: str
    download_link: str
    release: str  # e.g. 1.62.0
    md5: str
    sha256: str = ""  # calculated later

    def to_json(self):
        # Exclude `download_link`, `release`, and `md5` when converting to JSON
        data_dict = asdict(self)
        data_dict.pop("download_link")
        data_dict.pop("release")
        data_dict.pop("md5")
        return json.dumps(data_dict, indent=4)


def gather_sourceforge_files_for_release(version: Version) -> list[SourceForgeFile]:
    file_extensions = [".tar.bz2", ".tar.gz", ".7z", ".zip"]

    commit = version.data["commit"]["sha"]
    release = version.name.lstrip("boost-")
    rss_url = SOURCEFORGE_RSS_URL.format(release=release)

    resp = session.get(rss_url)
    resp.raise_for_status()

    root = ElementTree.fromstring(resp.content)
    namespaces = {"media": "http://video.search.yahoo.com/mrss/"}

    data = []

    for item in root.findall("channel/item"):
        title = item.find("title").text
        download_link = item.find("link").text
        pub_date = item.find("pubDate").text

        if not any(title.endswith(ext) for ext in file_extensions):
            continue

        file_name = title.split("/")[-1]  # (e.g., boost_1_60_0.zip)
        created = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S UT").strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        media_content = item.find("media:content", namespaces)
        md5_hash = media_content.find("media:hash", namespaces).text

        data.append(
            SourceForgeFile(
                commit=commit,
                file=file_name,
                created=created,
                release=release,
                download_link=download_link,
                md5=md5_hash,
            )
        )

    return data


def download_and_upload_with_metadata(source_file: SourceForgeFile):
    """
    Download file from SourceForge, then upload the release file and
    a json metadata file to S3.
    """

    sha256_hash = hashlib.sha256()
    md5_hash = hashlib.md5()
    storage = S3Boto3Storage(bucket_name=BUCKET_NAME)

    print(f"\nDownloading {source_file.file}")
    response = session.get(source_file.download_link)
    response.raise_for_status()

    # Read the entire file content into memory
    file_content = response.content

    # Validate checksum
    md5_hash.update(file_content)
    if md5_hash.hexdigest() != source_file.md5:
        print("⛔️ File checksum validation failed!")
        print(f"Expected: {source_file.md5}")
        print(f"Computed: {md5_hash}")
        return

    print("✅ Checksum validation passed")

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

    print(f"File uploaded to S3 at key '{s3_key}'")
    print(f"Metadata JSON uploaded to S3 at key '{json_s3_key}'")
