import json
from pathlib import Path

DATA_PATH = Path(__file__).parent / "patients.json"

_PATIENTS: list[dict] | None = None

def load_patients() -> list[dict]:
    global _PATIENTS
    if _PATIENTS is None:
        with open(DATA_PATH, encoding="utf-8") as f:
            _PATIENTS = json.load(f)
    return _PATIENTS


def get_patient_data(patient_id: str) -> dict:
    """
    Retrieve structured patient data for a given patient ID.

    Args:
        patient_id (str): The unique patient identifier (e.g., "PT-101").

    Returns:
        dict:
            - If found: A dictionary containing the patient's clinical data
              (age, gender, smoking history, symptoms, symptom duration).
            - If not found: A dictionary with at least:
              {
                  "patient_id": "<requested id>",
                  "found": False
              }
    """
    patients = load_patients()

    for p in patients:
        if p.get("patient_id") == patient_id:
            return p

    return {
        "patient_id": patient_id,
        "found": False
    }
