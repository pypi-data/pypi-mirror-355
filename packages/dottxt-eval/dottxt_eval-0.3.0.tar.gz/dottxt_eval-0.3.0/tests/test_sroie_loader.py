"""Tests for SROIE dataset loader."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from doteval.datasets.base import _registry
from doteval.datasets.sroie import SROIE


def test_sroie_dataset_attributes():
    """Test SROIE dataset has correct attributes."""
    assert SROIE.name == "sroie"
    assert SROIE.splits == []  # No splits available
    assert SROIE.columns == ["image", "expected_info"]


def test_sroie_auto_registration():
    """Test SROIE dataset is automatically registered."""
    assert "sroie" in _registry.list_datasets()
    dataset_class = _registry.get_dataset_class("sroie")
    assert dataset_class == SROIE


@patch("urllib.request.urlretrieve")
@patch("zipfile.ZipFile")
def test_sroie_download_and_extract(mock_zipfile, mock_urlretrieve):
    """Test SROIE dataset download and extraction."""
    # Create a mock directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock directory structure
        base_path = Path(temp_dir) / "ICDAR-2019-SROIE-master"
        img_dir = base_path / "data" / "img"
        key_dir = base_path / "data" / "key"
        img_dir.mkdir(parents=True)
        key_dir.mkdir(parents=True)

        # Create test files
        test_img = img_dir / "test_001.jpg"
        test_json = key_dir / "test_001.json"

        # Create a simple test image
        test_image = Image.new("RGB", (100, 100), color="white")
        test_image.save(test_img)

        # Create test JSON
        test_data = {
            "company": "Test Company",
            "date": "2024-01-01",
            "address": "123 Test St",
            "total": "10.00",
        }
        with open(test_json, "w") as f:
            json.dump(test_data, f)

        # Mock the download and extraction
        def mock_urlretrieve_side_effect(url, path):
            # Create an empty file to simulate download
            with open(path, "wb") as f:
                f.write(b"mock zip content")

        mock_urlretrieve.side_effect = mock_urlretrieve_side_effect

        # Mock the zipfile extraction
        def mock_extractall(path):
            # The extraction would create the directory structure
            pass

        mock_zip_instance = MagicMock()
        mock_zip_instance.extractall = mock_extractall
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        # Patch the temp directory creation to use our test directory
        with patch("tempfile.mkdtemp", return_value=temp_dir):
            dataset = SROIE()

            # Check that download was called
            mock_urlretrieve.assert_called_once()
            assert (
                "github.com/zzzDavid/ICDAR-2019-SROIE"
                in mock_urlretrieve.call_args[0][0]
            )

            # Check dataset attributes
            assert dataset.num_rows == 1
            assert len(dataset.files) == 1

            # Test iteration
            results = list(dataset)
            assert len(results) == 1

            image, expected_info = results[0]
            assert isinstance(image, Image.Image)
            assert image.size == (100, 100)

            assert expected_info["company"] == "Test Company"
            assert expected_info["date"] == "2024-01-01"
            assert expected_info["address"] == "123 Test St"
            assert expected_info["total"] == "10.00"


@patch("urllib.request.urlretrieve")
@patch("zipfile.ZipFile")
def test_sroie_missing_json(mock_zipfile, mock_urlretrieve):
    """Test SROIE behavior when JSON file is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock directory structure
        base_path = Path(temp_dir) / "ICDAR-2019-SROIE-master"
        img_dir = base_path / "data" / "img"
        key_dir = base_path / "data" / "key"
        img_dir.mkdir(parents=True)
        key_dir.mkdir(parents=True)

        # Create test image but no JSON
        test_img = img_dir / "test_002.jpg"
        test_image = Image.new("RGB", (100, 100), color="white")
        test_image.save(test_img)

        # Mock the download and extraction
        def mock_urlretrieve_side_effect(url, path):
            # Create an empty file to simulate download
            with open(path, "wb") as f:
                f.write(b"mock zip content")

        mock_urlretrieve.side_effect = mock_urlretrieve_side_effect

        # Mock the zipfile extraction
        def mock_extractall(path):
            # The extraction would create the directory structure
            pass

        mock_zip_instance = MagicMock()
        mock_zip_instance.extractall = mock_extractall
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        with patch("tempfile.mkdtemp", return_value=temp_dir):
            dataset = SROIE()
            results = list(dataset)

            assert len(results) == 1
            image, expected_info = results[0]

            # Should return empty fields when JSON is missing
            assert expected_info["company"] == ""
            assert expected_info["date"] == ""
            assert expected_info["address"] == ""
            assert expected_info["total"] == ""


@patch("urllib.request.urlretrieve", side_effect=Exception("Download failed"))
def test_sroie_download_failure(mock_urlretrieve):
    """Test SROIE behavior when download fails."""
    with pytest.raises(RuntimeError, match="Failed to download SROIE dataset"):
        SROIE()


@patch("urllib.request.urlretrieve")
@patch("zipfile.ZipFile")
def test_sroie_cleanup(mock_zipfile, mock_urlretrieve):
    """Test that SROIE cleans up temporary directory."""
    # Create a temporary directory for testing
    test_temp_dir = tempfile.mkdtemp()

    # Setup mock directory structure
    base_path = Path(test_temp_dir) / "ICDAR-2019-SROIE-master"
    img_dir = base_path / "data" / "img"
    key_dir = base_path / "data" / "key"
    img_dir.mkdir(parents=True)
    key_dir.mkdir(parents=True)

    # Mock the download
    def mock_urlretrieve_side_effect(url, path):
        with open(path, "wb") as f:
            f.write(b"mock zip content")

    mock_urlretrieve.side_effect = mock_urlretrieve_side_effect

    # Mock the zipfile extraction
    mock_zip_instance = MagicMock()
    mock_zip_instance.extractall = MagicMock()
    mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

    # Patch mkdtemp to return our test directory
    with patch("tempfile.mkdtemp", return_value=test_temp_dir):
        # Create a dataset instance
        dataset = SROIE()
        temp_dir = dataset.temp_dir

        # Directory should exist
        assert os.path.exists(temp_dir)

        # Delete the dataset
        del dataset

        # Directory should be cleaned up
        assert not os.path.exists(temp_dir)


@patch("urllib.request.urlretrieve")
@patch("zipfile.ZipFile")
def test_sroie_json_format(mock_zipfile, mock_urlretrieve):
    """Test SROIE JSON format consistency."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup mock directory structure
        base_path = Path(temp_dir) / "ICDAR-2019-SROIE-master"
        img_dir = base_path / "data" / "img"
        key_dir = base_path / "data" / "key"
        img_dir.mkdir(parents=True)
        key_dir.mkdir(parents=True)

        # Create test files with various JSON formats
        test_cases = [
            {
                "company": "ABC Corp",
                "date": "2024-01-01",
                "address": "123 St",
                "total": "10.00",
            },
            {"company": "XYZ Ltd"},  # Missing fields
            {"company": 123, "date": None},  # Non-string values
        ]

        for i, test_data in enumerate(test_cases):
            test_img = img_dir / f"test_{i:03d}.jpg"
            test_json = key_dir / f"test_{i:03d}.json"

            # Create image
            test_image = Image.new("RGB", (100, 100), color="white")
            test_image.save(test_img)

            # Create JSON
            with open(test_json, "w") as f:
                json.dump(test_data, f)

        # Mock the download and extraction
        def mock_urlretrieve_side_effect(url, path):
            # Create an empty file to simulate download
            with open(path, "wb") as f:
                f.write(b"mock zip content")

        mock_urlretrieve.side_effect = mock_urlretrieve_side_effect

        # Mock the zipfile extraction
        def mock_extractall(path):
            # The extraction would create the directory structure
            pass

        mock_zip_instance = MagicMock()
        mock_zip_instance.extractall = mock_extractall
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        with patch("tempfile.mkdtemp", return_value=temp_dir):
            dataset = SROIE()
            results = list(dataset)

            assert len(results) == 3

            # Check that all results have consistent format
            for _, expected_info in results:
                assert isinstance(expected_info, dict)
                assert set(expected_info.keys()) == {
                    "company",
                    "date",
                    "address",
                    "total",
                }
                # All values should be strings
                for value in expected_info.values():
                    assert isinstance(value, str)
