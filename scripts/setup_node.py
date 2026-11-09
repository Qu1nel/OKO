"""Install Node and npm in .tools with checksum verification, leaving global tools unchanged."""

import base64
import hashlib
import io
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

if __package__:
    from .node import NODE_VERSION, NPM_VERSION, ROOT, paths
else:
    from node import NODE_VERSION, NPM_VERSION, ROOT, paths

NODE_SHA256 = {
    "win-x64.zip": "dcc60d59a0746999f99064a01c020445d54d84228c691cdbf25b49ac3b59150a",
    "linux-x64.tar.xz": "d28a96af6c38596f6d9d97c0ee531c13d238d757742387d1928de822d959e997",
}
NPM_SHA512 = "dF3EDFwbYN+N5RUip+ZYDe0NeURK5BgqKOcvT1iNtUYhTMTl0FwWhBuXrS7KtXyduqyTMS5aaQaregnHDAxNgw=="


@contextmanager
def bootstrap_lock(tools: Path) -> Generator[None]:
    lock = tools / ".setup-node.lock"
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise RuntimeError(
            f"Node bootstrap is already running. If interrupted, verify no setup process remains before removing {lock}"
        ) from error
    try:
        yield
    finally:
        lock.rmdir()


def download(url: str) -> bytes:
    print(f"Downloading {url}", flush=True)
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def check_digest(data: bytes, algorithm: str, expected: str) -> None:
    actual = hashlib.new(algorithm, data).digest()
    wanted = bytes.fromhex(expected) if algorithm == "sha256" else base64.b64decode(expected)
    if actual != wanted:
        raise ValueError("Downloaded archive checksum mismatch")


def extract(data: bytes, target: Path, *, zipped: bool = False) -> None:
    """Reject paths outside the destination before extracting the archive."""
    target = target.resolve()
    if zipped:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in archive.infolist():
                if not (target / member.filename).resolve().is_relative_to(target):
                    raise ValueError("Unsafe archive path")
            archive.extractall(target)
    else:
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(target, filter="data")


def main() -> None:
    node, npm = paths()
    tools = (ROOT / ".tools").resolve()
    tools.mkdir(exist_ok=True)
    if not tools.is_relative_to(ROOT.resolve()):
        raise ValueError("Tool directory escapes the project")
    # Keep temporary files and all moves within the project's tools directory
    with bootstrap_lock(tools), tempfile.TemporaryDirectory(prefix="setup-", dir=tools) as temporary:
        stage = Path(temporary)
        if not node.is_file():
            suffix = "win-x64.zip" if sys.platform == "win32" else "linux-x64.tar.xz"
            filename = f"node-v{NODE_VERSION}-{suffix}"
            data = download(f"https://nodejs.org/dist/v{NODE_VERSION}/{filename}")
            check_digest(data, "sha256", NODE_SHA256[suffix])
            extract(data, stage, zipped=suffix.endswith(".zip"))
            folder = filename.removesuffix(".zip").removesuffix(".tar.xz")
            destination = tools / folder
            if destination.exists():
                raise RuntimeError(f"Incomplete installation: remove {destination} before retrying")
            shutil.move(str(stage / folder), destination)
        if not npm.is_file():
            data = download(f"https://registry.npmjs.org/npm/-/npm-{NPM_VERSION}.tgz")
            check_digest(data, "sha512", NPM_SHA512)
            extract(data, stage)
            destination = tools / f"npm-{NPM_VERSION}"
            if destination.exists():
                raise RuntimeError(f"Incomplete installation: remove {destination} before retrying")
            shutil.move(str(stage / "package"), destination)
    print(f"Ready: Node {NODE_VERSION}, npm {NPM_VERSION}")


if __name__ == "__main__":
    main()
