from os import PathLike
from tempfile import TemporaryDirectory
from pathlib import Path
from subprocess import run


class ZipMount:

    def __init__(self, zip_path: PathLike | str):
        self.zip_path = zip_path
        self.tmp_dir = TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp_path = Path(self.tmp_dir.name)

        run([
            "mount-zip",
            zip_path, self.tmp_path
        ])

    def __del__(self):
        run(["umount", self.tmp_path])
        self.tmp_dir.cleanup()
