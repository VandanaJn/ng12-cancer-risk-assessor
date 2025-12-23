from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

import vertexai
from app.config import GCP_PROJECT, GCP_REGION
import os
from app.tools.nice_guideline_tool import search_nice_ng12_guidelines
from app.tools.patient_data_tool import get_patient_data
from app.prompts import load_system_prompt
system_prompt = load_system_prompt()

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
    instruction="""
You are a clinical decision support agent.

You MUST:
- Use get_patient_data to retrieve patient info
- Use search_nice_ng12_guidelines to find relevant NICE NG12 guideline sections
- Use NICE NG12 guidelines only, no other sources
- Assess cancer risk based on age, symptoms, and duration
- Decide between:
  - urgent referral
  - urgent investigation
  - no urgent action
- Cite the guideline text verbatim

OUTPUT RULES (STRICT):
- Respond with ONLY a single valid JSON object
- Do NOT include any text outside the JSON
- Do NOT add explanations, apologies, or validation messages
- Do NOT mention formatting errors

JSON FORMAT (EXACT):

{
  "recommendation": "<urgent referral | urgent investigation | no urgent action>",
  "justification": "<verbatim NICE NG12 text>",
  "references": [
    {
      "page": <number>,
      "chunk_id": "<string>"
    }
  ]
}
""",
    tools=[search_nice_ng12_guidelines, get_patient_data] 
)

# 2. Define the Body (The App)
# This 'app' is what you actually run or deploy.
app = AdkApp(agent=root_agent)

