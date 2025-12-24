from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.ng12_agent import ng12_app
from google.genai import types
from app.assess_agent import assess_app
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
import logging

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

@app.post("/knowledge_chat")
async def knowledge_chat(req: KnowledgeRequest):
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
        parts=[types.Part.from_text(text=f"answer this: {req.message} using top_n: {req.top_k}")]
    )

    async def event_generator():
        try:
            async for event in runner.run_async(
                session_id=session.id,
                user_id=user_id,
                new_message=formatted_message,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            yield part.text
                
                    
        except Exception as e:
            logger.exception("ERROR in Runner: %s", e)
            yield f"Internal Error"

    return StreamingResponse(event_generator(), media_type="text/plain")


