import json
from pathlib import Path

import pytest

from app.tools import patient_data_tool as pdt


def test_get_existing_patient_returns_record(monkeypatch):
    sample = [{"patient_id": "PT-101", "name": "Alice"}]
    monkeypatch.setattr(pdt, "_PATIENTS", sample)

    result = pdt.get_patient_data("PT-101")

    assert result["patient_id"] == "PT-101"
    assert result["name"] == "Alice"


def test_get_missing_patient_returns_not_found(monkeypatch):
    sample = [{"patient_id": "PT-200", "name": "Bob"}]
    monkeypatch.setattr(pdt, "_PATIENTS", sample)

    result = pdt.get_patient_data("PT-999")

    assert result.get("found") is False
    assert result.get("patient_id") == "PT-999"


def test_load_patients_reads_file(tmp_path, monkeypatch):
    data = [{"patient_id": "PT-300", "name": "Carol"}]
    file_path = tmp_path / "patients.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    # Point the module to the temp file and clear cache
    monkeypatch.setattr(pdt, "DATA_PATH", file_path)
    monkeypatch.setattr(pdt, "_PATIENTS", None)

    loaded = pdt.load_patients()

    assert isinstance(loaded, list)
    assert loaded[0]["patient_id"] == "PT-300"
