import hashlib
import importlib.resources
import logging
import math
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

from tqdm import tqdm

from .file import File
from .function import Function
from .method import Method
from .project import CPPProject, CProject, JavaProject, JavaScriptProject, PythonProject

__all__ = [
    "File",
    "Function",
    "Method",
    "CProject",
    "CPPProject",
    "JavaProject",
    "JavaScriptProject",
    "PythonProject",
]

_l = logging.getLogger(__name__)

JOERN_VERSION = "v4.0.340"
JOERN_ZIP_HASH = "3c1757f862e6c58db4b527f2ac51c77c3f91db22091cc4a2b8bd1e3427f3485ab70a45b633806ddf4390149c864cb8f69a2fb8e2a531c0e6daf6e6c4c2224c77"
JOERN_BIN_DIR_PATH = Path(
    Path(str(importlib.resources.files("scubatrace"))) / "bin/joern-cli"
).absolute()
JOERN_SERVER_PATH = JOERN_BIN_DIR_PATH / "joern"
JOERN_EXPORT_PATH = JOERN_BIN_DIR_PATH / "joern-export"
JOERN_PARSE_PATH = JOERN_BIN_DIR_PATH / "joern-parse"


def _download_and_save_joern_zip(save_location: Path, verify=True) -> Path:
    # XXX: hacked code for non-ssl verification
    import ssl

    ssl._create_default_https_context = ssl._create_unverified_context

    url = f"https://github.com/joernio/joern/releases/download/{JOERN_VERSION}/joern-cli.zip"
    with urllib.request.urlopen(url) as response:
        total_size = response.length
        if response.status != 200:
            raise Exception(f"HTTP error {response.status}: {response.reason}")

        hasher = hashlib.sha512()
        chunk_size = 8192
        mb_size = int(total_size / 1000000)
        with open(save_location, "wb") as f:
            for _ in tqdm(
                range(math.ceil(total_size / chunk_size)),
                desc=f"Downloading Joern bytes (~{mb_size} MB)...",
            ):
                chunk = response.read(chunk_size)
                hasher.update(chunk)
                if not chunk:
                    break

                f.write(chunk)

        # hash for extra security
        download_hash = hasher.hexdigest()
        if verify and download_hash != JOERN_ZIP_HASH:
            raise Exception(
                f"Joern files corrupted in download: {download_hash} != {JOERN_ZIP_HASH}"
            )
    return save_location


def _download_joern():
    joern_binary = JOERN_BIN_DIR_PATH / "joern"
    if joern_binary.exists():
        return

    # download joern
    if not JOERN_BIN_DIR_PATH.parent.exists():
        os.mkdir(JOERN_BIN_DIR_PATH.parent)
    joern_zip_file = _download_and_save_joern_zip(
        JOERN_BIN_DIR_PATH.parent / "joern-cli.zip", verify=True
    )

    # unzip joern
    with zipfile.ZipFile(joern_zip_file, "r") as zip_ref:
        zip_ref.extractall(JOERN_BIN_DIR_PATH.parent)

    # remove zip file
    joern_zip_file.unlink()

    if not joern_binary.exists():
        raise Exception("Failed to download Joern!")


def joern_exists() -> bool:
    """
    Check if Joern is installed on the system.
    If not, download Joern.
    """
    if JOERN_BIN_DIR_PATH.exists():
        os.environ["PATH"] = str(JOERN_BIN_DIR_PATH) + os.pathsep + os.environ["PATH"]
        assert shutil.which("joern") == JOERN_BIN_DIR_PATH / "joern"
        return True
    return shutil.which("joern") is not None


if not joern_exists():
    _download_joern()
    if not joern_exists():
        raise Exception(
            "Failed to install Joern! You can install it manually via https://docs.joern.io/installation"
        )
