import djclick as click

import hashlib
import requests

from django.conf import settings

from versions.models import Version
from versions.releases import (
    download_sourceforge_files_for_release,
)


@click.command()
@click.option("--release", is_flag=False, help="Release name")
def command(release):
    """
    Import release data from SourceForge, and copy the files to S3.

    This command will download and host release files from SourceForge for the
    specified release. If no release is specified, it will import the release data
    for all releases included in Artifactory.
    """
    last_release = settings.MIN_ARTIFACTORY_RELEASE

    if release:
        versions = Version.objects.filter(name__icontains=release)
    else:
        versions = Version.objects.filter(name__lt=last_release)

    for v in versions:
        try:
            print(f"Gathering download file data for {v}")
            sourceforge_file_data = download_sourceforge_files_for_release(v)
        except requests.exceptions.HTTPError:
            print(f"Skipping {v}, error retrieving release data")
            continue

        for file in sourceforge_file_data:
            try:
                print(f"Downloading {file.file}")
                file.sha256 = download_and_compute_sha256(file.download_link)
            except requests.exceptions.HTTPError:
                print(f"Skipping {file.file}, error retrieving file")
                continue

            print(file.to_json())


def download_and_compute_sha256(url, chunk_size=65536):  # Default to 64 KB
    sha256_hash = hashlib.sha256()

    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=chunk_size):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()
