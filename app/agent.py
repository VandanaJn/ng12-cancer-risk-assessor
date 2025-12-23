from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

import vertexai
from app.config import GCP_PROJECT, GCP_REGION
import os

from app.tools.medical_guideline_tool import search_medical_guidelines
def init_vertexai():
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT
    os.environ["GOOGLE_CLOUD_LOCATION"] = GCP_REGION

    vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
    # Tell the ADK to use Vertex AI and provide the project details

init_vertexai()
# --- STEP 1: Define the Tool ---
# Initialize embedding model once (module-level)


# 1. Define the Brain (The Agent)
root_agent = Agent(
    name="MedicalHelper",
    model="gemini-2.5-flash-lite",
    instruction="You are a medical assistant. Use the provided tools to find referral criteria.",
    tools=[search_medical_guidelines] # Your ChromaDB function
)

# 2. Define the Body (The App)
# This 'app' is what you actually run or deploy.
app = AdkApp(agent=root_agent)

