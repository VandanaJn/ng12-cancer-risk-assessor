from google.adk.agents import Agent
from google.adk.apps.app import App, EventsCompactionConfig
import vertexai
from app.config import GCP_PROJECT, GCP_REGION
import os
from app.tools.nice_guideline_tool import search_nice_ng12_guidelines
from app.prompts import load_system_prompt
from pydantic import BaseModel
from google.adk.plugins.logging_plugin import LoggingPlugin
from typing import List
from app.vertexai_utils import init_vertexai

rag_prompt = load_system_prompt("NG12_AGENT")

class Citation(BaseModel):
    source: str
    page: int
    chunk_id: str
    excerpt: str

class NG12Response(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation] = []  # Empty array if no results found

init_vertexai()



ng12_agent = Agent(
    name="ng12_agent",
    model="gemini-2.5-flash-lite",
    instruction=rag_prompt,
    description="Agent to search NICE NG12 guidelines for relevant information.",
    tools=[search_nice_ng12_guidelines],
    output_schema=NG12Response,
)

ng12_app = App( name="ng12_agent_compacting_app",
    root_agent=ng12_agent, events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Trigger compaction every 3 invocations for managing context size
        overlap_size=1,  # Keep 1 previous turn for context
    ), 
    plugins=[
        LoggingPlugin()# adds logging capabilities for obervabilities
    ])

