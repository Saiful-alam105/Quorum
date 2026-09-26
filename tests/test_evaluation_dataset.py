import json

import pytest

from evaluation.dataset import DATASET_DIR, load_dataset, load_entry


class TestDatasetLoader:
    def test_loads_sample_dataset_sorted(self) -> None:
        entries = load_dataset()
        ids = [entry["id"] for entry in entries]
        assert ids == sorted(ids)
        assert len(entries) >= 2
        for entry in entries:
            for field in ("id", "repository", "pr_number", "files", "labeled_findings"):
                assert field in entry

    def test_sample_entry_file_content_present(self) -> None:
        entry = load_entry(DATASET_DIR / "pr-0001.json")
        assert "subprocess.call" in entry["files"]["run_cmd.py"]
        assert entry["labeled_findings"][0]["file"] == "run_cmd.py"
        assert entry["labeled_findings"][0]["line"] == 5

    def test_invalid_entry_raises(self, tmp_path) -> None:
        path = tmp_path / "bad.json"
        path.write_text(
            json.dumps({"id": "bad", "files": {}}), encoding="utf-8"
        )
        with pytest.raises(ValueError):
            load_entry(path)

    def test_custom_directory(self, tmp_path) -> None:
        path = tmp_path / "x.json"
        path.write_text(
            json.dumps(
                {
                    "id": "x",
                    "repository": "r",
                    "pr_number": 1,
                    "files": {"a.py": "code"},
                    "labeled_findings": [],
                }
            ),
            encoding="utf-8",
        )
        entries = load_dataset(tmp_path)
        assert len(entries) == 1
        assert entries[0]["id"] == "x"