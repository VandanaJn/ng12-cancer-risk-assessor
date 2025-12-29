"""Vertex AI initialization utilities for NG12 Cancer Risk Assessor."""

import vertexai
import os
from app.config import GCP_PROJECT, GCP_REGION


def init_vertexai():
    """Initialize Vertex AI with GCP project and region settings."""
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT
    os.environ["GOOGLE_CLOUD_LOCATION"] = GCP_REGION

    vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
