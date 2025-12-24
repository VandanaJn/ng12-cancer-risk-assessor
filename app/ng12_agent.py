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
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.plugins.logging_plugin import LoggingPlugin

rag_prompt = load_system_prompt("RAG_AGENT")

def init_vertexai():
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT
    os.environ["GOOGLE_CLOUD_LOCATION"] = GCP_REGION

    vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
    # Tell the ADK to use Vertex AI and provide the project details

init_vertexai()



ng12_agent = Agent(
    name="ng12_agent",
    model="gemini-2.5-flash-lite",
    instruction=rag_prompt,
    description="Agent to search NICE NG12 guidelines for relevant information.",
    tools=[search_nice_ng12_guidelines],
)

ng12_app = App( name="ng12_agent_compacting_app",
    root_agent=ng12_agent, events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Trigger compaction every 3 invocations
        overlap_size=1,  # Keep 1 previous turn for context
    ), 
    plugins=[
        LoggingPlugin()
    ])

