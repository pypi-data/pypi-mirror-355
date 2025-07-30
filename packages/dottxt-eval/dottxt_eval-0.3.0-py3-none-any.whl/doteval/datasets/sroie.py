import json
import os
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterator

from PIL import Image

from doteval.datasets.base import Dataset


class SROIE(Dataset):
    """SROIE dataset for receipt information extraction

    This dataset tests the ability of models to extract key information
    from digitized receipts including company name, address, date, and total amount.
    """

    name = "sroie"
    splits = []  # No splits available
    columns = ["image", "expected_info"]

    def __init__(self, **kwargs):
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()

        # Download the repository as a zip file
        repo_url = (
            "https://github.com/zzzDavid/ICDAR-2019-SROIE/archive/refs/heads/master.zip"
        )
        zip_path = os.path.join(self.temp_dir, "sroie.zip")

        try:
            print(f"Downloading SROIE dataset from {repo_url}...")
            urllib.request.urlretrieve(repo_url, zip_path)

            # Extract the zip file
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.temp_dir)

            # Remove the zip file to save space
            os.remove(zip_path)

        except Exception as e:
            import shutil

            shutil.rmtree(self.temp_dir)
            raise RuntimeError(f"Failed to download SROIE dataset: {e}")

        # Set paths based on the repository structure
        # The extracted folder will be named ICDAR-2019-SROIE-master
        self.base_path = Path(self.temp_dir) / "ICDAR-2019-SROIE-master"
        self.img_dir = self.base_path / "data" / "img"
        self.key_dir = self.base_path / "data" / "key"

        # Get list of files
        if self.img_dir.exists():
            self.files = sorted([f.stem for f in self.img_dir.glob("*.jpg")])
            self.num_rows = len(self.files)
        else:
            self.files = []
            self.num_rows = 0

    def __del__(self):
        """Clean up temporary directory"""
        import shutil

        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _read_key_info(self, file_id: str) -> dict:
        """Read the ground truth key information for a given file"""
        json_file = self.key_dir / f"{file_id}.json"

        if not json_file.exists():
            return {"company": "", "date": "", "address": "", "total": ""}

        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        return {
            "company": str(data.get("company", "")),
            "date": str(data.get("date", "")),
            "address": str(data.get("address", "")),
            "total": str(data.get("total", "")),
        }

    def __iter__(self) -> Iterator[tuple[Image.Image, dict]]:
        for file_id in self.files:
            image_path = self.img_dir / f"{file_id}.jpg"
            image = Image.open(image_path).convert("RGB")

            expected_info = self._read_key_info(file_id)

            yield (image, expected_info)


from doteval.datasets.base import _registry  # noqa: E402

_registry.register(SROIE)
