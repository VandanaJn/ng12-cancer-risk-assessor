
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from app.ng12_agent import ng12_app
from google.genai import types
from app.assess_agent import assess_app
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
import logging
import json
import json

from pathlib import Path

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)



app = FastAPI(
    title="NG12 Cancer Risk Assessor",
    version="1.0.0"
)

ng12_session_service = InMemorySessionService() 
runner = Runner(
    app=ng12_app,
    session_service=ng12_session_service 
)

class AssessmentRequest(BaseModel):
    patient_id: str
    user_id: str

class KnowledgeRequest(BaseModel):
    message: str
    session_id: str
    top_k: int = 5

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"

@app.get("/")
def home():
    return FileResponse(UI_DIR / "index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/assess")
async def assess_patient(req: AssessmentRequest):
    async def generate_response():
        try:
            async for event in assess_app.async_stream_query(
                user_id=req.user_id, 
                message=f"Assess patient with ID: {req.patient_id}"
            ):
                if "content" in event:
                    # content contains the text/json string
                    text_part = event["content"]["parts"][0].get("text", "")
                    if text_part:
                        yield text_part # This is already a string, no dict error!
        except Exception as e:
            logger.exception("ERROR in assess_patient: %s", e)
            yield "Internal Error"

    return StreamingResponse(generate_response(), media_type="application/json")

@app.post("/chat")
async def chat(req: KnowledgeRequest):
    session_id = str(req.session_id)
    user_id = str(req.session_id) 
    
    app_name = ng12_app.name

    try:
        session = await ng12_session_service.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
    except:
        logger.info("creating new session for app: %s, user: %s, session: %s", app_name, user_id, session_id)
        session = await ng12_session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    formatted_message = types.Content(
        role="user", 
        parts=[types.Part.from_text(text=f"answer this: {req.message} using top_n: {req.top_k} for session_id: {session_id}")]
    )

    text_parts = []
    try:
        async for event in runner.run_async(
            session_id=session.id,
            user_id=user_id,
            new_message=formatted_message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        text_parts.append(part.text)
    except Exception as e:
        logger.exception("ERROR in Runner: %s", e)
        return StreamingResponse(
            json.dumps({"error": "Internal Error"}),
            media_type="application/json"
        )

    response_content = "".join(text_parts)
    return StreamingResponse(response_content, media_type="application/json")


@app.get("/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    """Return conversation history for the given session (best-effort)."""
    user_id = str(session_id)
    app_name = ng12_app.name
    try:
        session = await ng12_session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    except Exception as e:
        logger.exception("Error fetching session %s: %s", session_id, e)
        return {"error": "session not found or session service error"}

    # Prefer the session events (ADK sessions store events)
    try:
        events = getattr(session, "events", None)
        if events:
            serialized = []
            for ev in events:
                try:
                    if hasattr(ev, "to_dict"):
                        ev_dict = ev.to_dict()
                    else:
                        ev_dict = ev.__dict__
                except Exception:
                    ev_dict = str(ev)
                serialized.append(ev_dict)

            return {"session_id": session_id, "events": serialized, "state": getattr(session, "state", {})}

        # No events — return session state if available
        return {"session_id": session_id, "state": getattr(session, "state", {})}
    except Exception as e:
        logger.exception("Unable to serialize session %s: %s", session_id, e)
        return {"error": "unable to retrieve session history"}


@app.delete("/chat/{session_id}")
async def delete_chat_session(session_id: str):
    """Clear stored history for the given session (best-effort)."""
    user_id = str(session_id)
    app_name = ng12_app.name
    # Try known session-service deletion methods
    try:
        # Memory/session service supports deletion API
        await ng12_session_service.delete_session(app_name=app_name, user_id=user_id, session_id=session_id)
        return {"status": "deleted"}
    except Exception as e:
        logger.exception("Error deleting/clearing session %s: %s", session_id, e)
        return {"error": "unable to delete session"}
    


