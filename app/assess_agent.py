from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp
from google.adk.apps.app import App, EventsCompactionConfig
import vertexai
from app.config import GCP_PROJECT, GCP_REGION
import os
from app.tools.nice_guideline_tool import search_nice_ng12_guidelines
from app.tools.patient_data_tool import get_patient_data
from app.prompts import load_system_prompt
from pydantic import BaseModel
from google.adk.apps.app import App
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner


assess_prompt = load_system_prompt("ASSESSMENT_AGENT")

def init_vertexai():
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT
    os.environ["GOOGLE_CLOUD_LOCATION"] = GCP_REGION

    vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
    # Tell the ADK to use Vertex AI and provide the project details

init_vertexai()

class AssessmentResponse(BaseModel):
    recommendation: str
    justification: str
    references: list


assess_agent=Agent(
    name="assess_agent",
    model="gemini-2.5-flash-lite",
    instruction=assess_prompt,
    description="Agent to assess cancer risk based on NICE NG12 guidelines and patient data.",
    tools=[search_nice_ng12_guidelines, get_patient_data],
    output_schema=AssessmentResponse
)


assess_app=AdkApp(agent=assess_agent, plugins=[
    LoggingPlugin()])
   

