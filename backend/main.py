"""
Uproad AI — FastAPI Backend
Handles: inbound SMS/calls from drivers, outbound voice via ElevenLabs,
         Claude dispatch agent, REST API for dashboard.
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream, Gather, Say
from twilio.twiml.messaging_response import MessagingResponse
from pydantic import BaseModel
import json
import asyncio
import websockets
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from database import get_db, engine
from models import Base, Job, Vendor
from agent import run_dispatch_agent
from services.elevenlabs_svc import get_signed_url, ensure_agents_exist
from config import ELEVENLABS_INTAKE_AGENT_ID, ELEVENLABS_DISPATCH_AGENT_ID, BASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Uproad AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Runtime agent IDs (set on startup)
INTAKE_AGENT_ID = ELEVENLABS_INTAKE_AGENT_ID
DISPATCH_AGENT_ID = ELEVENLABS_DISPATCH_AGENT_ID


# ============================================================
# STARTUP — ensure ElevenLabs agents exist
# ============================================================

@app.on_event("startup")
async def startup():
    global INTAKE_AGENT_ID, DISPATCH_AGENT_ID
    logger.info("Uproad AI starting up...")
    try:
        INTAKE_AGENT_ID, DISPATCH_AGENT_ID = await ensure_agents_exist(
            INTAKE_AGENT_ID, DISPATCH_AGENT_ID
        )
        logger.info(f"Intake agent: {INTAKE_AGENT_ID}")
        logger.info(f"Dispatch agent: {DISPATCH_AGENT_ID}")
    except Exception as e:
        logger.warning(f"Could not set up ElevenLabs agents: {e}. Voice calls may not work.")
    try:
        seed_vendors(next(get_db()))
    except Exception as e:
        logger.warning(f"seed_vendors failed: {e}")


def seed_vendors(db: Session):
    if db.query(Vendor).count() == 0:
        from services.vendors import VENDORS
        for v in VENDORS:
            db.add(Vendor(
                id=v["id"], name=v["name"], phone=v["phone"],
                service_types=json.dumps(v["types"]), coverage_area=v["coverage"],
                rating=v["rating"], avg_response_min=v["eta_min"]
            ))
        db.commit()
        logger.info("Seeded vendor database")


# ============================================================
# TWILIO WEBHOOKS — Inbound SMS
# ============================================================

@app.post("/webhook/sms/inbound")
async def inbound_sms(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Driver texts the Twilio number -> create job -> run agent."""
    form = await request.form()
    from_number = form.get("From", "")
    body = form.get("Body", "").strip()
    logger.info(f"Inbound SMS from {from_number}: {body}")

    # Create job
    job = Job(
        status="OPEN",
        type="ROADSIDE",
        summary=body[:200],
        raw_message=body,
        driver_phone=from_number,
        source="sms",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Run agent in background
    background_tasks.add_task(run_agent_for_job, job.id)

    # Immediate Twilio reply
    resp = MessagingResponse()
    resp.message("Uproad Fleet: We received your report and our AI dispatch team is on it. You'll get an update shortly. Stay safe and keep your hazards on.")
    return Response(content=str(resp), media_type="application/xml")


# ============================================================
# TWILIO WEBHOOKS — Inbound Voice (driver calls)
# ============================================================

@app.post("/webhook/voice/inbound")
async def inbound_voice(request: Request):
    """
    Driver calls the Twilio number.
    Gets a signed URL from ElevenLabs and connects the call directly.
    """
    global INTAKE_AGENT_ID
    form = await request.form()
    call_sid = form.get("CallSid", "")
    from_number = form.get("From", "")
    logger.info(f"Inbound call from {from_number}, CallSid={call_sid}")

    resp = VoiceResponse()

    if not INTAKE_AGENT_ID:
        resp.say("Thank you for calling Uproad Fleet roadside assistance. Please text us your location and problem and we will dispatch help immediately.")
        return Response(content=str(resp), media_type="application/xml")

    try:
        # Get a signed WebSocket URL and stream directly to ElevenLabs
        signed_url = await get_signed_url(INTAKE_AGENT_ID)
        connect = Connect()
        stream = Stream(url=signed_url)
        connect.append(stream)
        resp.append(connect)
    except Exception as e:
        logger.error(f"ElevenLabs signed URL error: {e}")
        resp.say("Thank you for calling Uproad Fleet. Our AI agent is temporarily unavailable. Please text this number with your location and problem and we will dispatch help immediately.")

    return Response(content=str(resp), media_type="application/xml")


@app.post("/webhook/voice/outbound")
async def outbound_voice_twiml(request: Request):
    """
    TwiML for outbound vendor calls.
    Twilio calls vendor -> connects directly to ElevenLabs dispatch agent.
    """
    global DISPATCH_AGENT_ID
    params = dict(request.query_params)
    agent_id = params.get("agent_id", DISPATCH_AGENT_ID)
    job_id = params.get("job_id", "")
    vendor_name = params.get("vendor_name", "vendor")
    problem = params.get("problem", "")
    vehicle = params.get("vehicle", "")
    location = params.get("location", "")

    resp = VoiceResponse()

    if not agent_id:
        resp.say(f"Hello, this is Uproad Fleet Management calling about a roadside assistance request for job {job_id}. Please call us back at your earliest convenience.")
        return Response(content=str(resp), media_type="application/xml")

    try:
        signed_url = await get_signed_url(agent_id, dynamic_variables={
            "vendor_name": vendor_name,
            "job_id": job_id,
            "problem": problem,
            "vehicle": vehicle,
            "location": location,
        })
        connect = Connect()
        stream = Stream(url=signed_url)
        connect.append(stream)
        resp.append(connect)
    except Exception as e:
        logger.error(f"ElevenLabs dispatch signed URL error: {e}")
        resp.say(f"Hello, this is Uproad Fleet Management. We have an urgent dispatch for job {job_id}. The vehicle is {vehicle} at {location} with the following issue: {problem}. Please call us back.")

    return Response(content=str(resp), media_type="application/xml")


@app.post("/webhook/voice/status")
async def voice_status_callback(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Twilio call status webhook -- update job when call completes."""
    form = await request.form()
    call_sid = form.get("CallSid", "")
    call_status = form.get("CallStatus", "")
    logger.info(f"Call {call_sid} status: {call_status}")
    return {"ok": True}


# ============================================================
# WEBSOCKET — ElevenLabs <-> Twilio audio proxy
# ============================================================

@app.websocket("/ws/voice/{call_type}")
async def voice_websocket(websocket: WebSocket, call_type: str):
    """
    Bidirectional audio proxy between Twilio Media Streams and ElevenLabs Conversational AI.
    call_type: 'intake' (driver -> us) or 'dispatch' (us -> vendor)
    """
    await websocket.accept()
    params = dict(websocket.query_params)
    agent_id = params.get("agent_id", "")
    call_sid = params.get("call_sid", "")
    from_number = params.get("from", "")
    job_id = params.get("job_id", "")
    vendor_name = params.get("vendor_name", "")

    logger.info(f"WebSocket opened: {call_type}, agent={agent_id}, call={call_sid}")
    stream_sid = None
    transcript_chunks = []

    if not agent_id:
        await websocket.close()
        return

    try:
        # Get signed URL from ElevenLabs
        signed_url = await get_signed_url(agent_id)

        async with websockets.connect(signed_url) as el_ws:

            # Send initial context to ElevenLabs
            context_msg = {
                "type": "conversation_initiation_client_data",
                "conversation_config_override": {
                    "tts": {"audio_encoding": "ulaw_8000"},
                    "asr": {"user_input_audio_format": "ulaw_8000"},
                }
            }
            if call_type == "dispatch" and vendor_name:
                context_msg["dynamic_variables"] = {
                    "vendor_name": vendor_name,
                    "job_id": job_id,
                    "problem": params.get("problem", ""),
                    "vehicle": params.get("vehicle", ""),
                    "location": params.get("location", ""),
                }
            await el_ws.send(json.dumps(context_msg))

            async def twilio_to_elevenlabs():
                nonlocal stream_sid
                try:
                    while True:
                        raw = await websocket.receive_text()
                        msg = json.loads(raw)
                        event = msg.get("event")

                        if event == "start":
                            stream_sid = msg.get("streamSid") or msg.get("start", {}).get("streamSid")
                            logger.info(f"Stream started: {stream_sid}")

                        elif event == "media":
                            payload = msg.get("media", {}).get("payload", "")
                            if payload:
                                await el_ws.send(json.dumps({"user_audio_chunk": payload}))

                        elif event == "stop":
                            logger.info(f"Twilio stream stopped: {stream_sid}")
                            break

                except (WebSocketDisconnect, Exception) as e:
                    logger.info(f"Twilio WS closed: {e}")

            async def elevenlabs_to_twilio():
                nonlocal stream_sid
                try:
                    async for raw in el_ws:
                        msg = json.loads(raw)
                        msg_type = msg.get("type")

                        if msg_type == "audio":
                            audio_b64 = msg.get("audio_event", {}).get("audio_base_64", "")
                            if audio_b64 and stream_sid:
                                twilio_msg = {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {"payload": audio_b64}
                                }
                                await websocket.send_text(json.dumps(twilio_msg))

                        elif msg_type == "interruption":
                            if stream_sid:
                                await websocket.send_text(json.dumps({
                                    "event": "clear",
                                    "streamSid": stream_sid
                                }))

                        elif msg_type == "agent_response":
                            text = msg.get("agent_response_event", {}).get("agent_response", "")
                            if text:
                                transcript_chunks.append(f"Agent: {text}")

                        elif msg_type == "user_transcript":
                            text = msg.get("user_transcription_event", {}).get("user_transcript", "")
                            if text:
                                transcript_chunks.append(f"Caller: {text}")

                        elif msg_type == "conversation_initiation_metadata":
                            conv_id = msg.get("conversation_initiation_metadata_event", {}).get("conversation_id")
                            logger.info(f"ElevenLabs conversation: {conv_id}")

                except Exception as e:
                    logger.info(f"ElevenLabs WS closed: {e}")

            await asyncio.gather(twilio_to_elevenlabs(), elevenlabs_to_twilio())

    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
    finally:
        # If it was an inbound driver call, create a job from the transcript
        if call_type == "intake" and transcript_chunks and from_number:
            transcript = "\n".join(transcript_chunks)
            logger.info(f"Inbound call transcript:\n{transcript}")
            # Schedule job creation from transcript
            asyncio.create_task(create_job_from_call(from_number, transcript))

        try:
            await websocket.close()
        except:
            pass


async def create_job_from_call(driver_phone: str, transcript: str):
    """Create a job from an inbound driver call transcript, then run agent."""
    db = next(get_db())
    job = Job(
        status="OPEN",
        type="ROADSIDE",
        summary=transcript[:200] if transcript else "Inbound call — no transcript",
        raw_message=transcript,
        driver_phone=driver_phone,
        source="call",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(f"Created job {job.id} from inbound call")
    await asyncio.get_event_loop().run_in_executor(None, lambda: _run_agent_sync(job.id))


# ============================================================
# AGENT BACKGROUND TASK
# ============================================================

def _parse_list(val):
    """Safely parse a value that should be a list -- handles JSON strings from SQLite."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def _run_agent_sync(job_id: str):
    """Synchronous wrapper for run_dispatch_agent (for use in thread executor)."""
    db = next(get_db())
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return

    job_dict = {
        "id": job.id,
        "status": job.status,
        "driver_phone": job.driver_phone,
        "driver_name": job.driver_name,
        "vehicle_info": job.vehicle_info,
        "location": job.location,
        "raw_message": job.raw_message,
        "summary": job.summary,
        "source": job.source,
    }

    result = run_dispatch_agent(job_dict, dispatch_agent_id=DISPATCH_AGENT_ID)

    # Apply updates to DB -- parse stored values in case SQLite returns JSON as strings
    job.actions = _parse_list(job.actions) + result["actions"]
    job.agent_runs = _parse_list(job.agent_runs) + [result["agent_run"]]

    updates = result.get("job_updates", {})
    if updates.get("status"):
        job.status = updates["status"]
    if updates.get("assigned_vendor_name"):
        job.assigned_vendor_name = updates["assigned_vendor_name"]
    if updates.get("assigned_vendor_phone"):
        job.assigned_vendor_phone = updates["assigned_vendor_phone"]
    if updates.get("vendor_eta_minutes"):
        job.vendor_eta_minutes = updates["vendor_eta_minutes"]

    db.commit()
    logger.info(f"Job {job_id} agent run complete")


async def run_agent_for_job(job_id: str):
    """Async wrapper -- runs sync agent in thread pool."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: _run_agent_sync(job_id))


# ============================================================
# REST API — Dashboard
# ============================================================

@app.get("/api/v1/jobs")
def list_jobs(db: Session = Depends(get_db), status: Optional[str] = None, limit: int = 50):
    q = db.query(Job).order_by(Job.created_at.desc())
    if status:
        q = q.filter(Job.status == status)
    jobs = q.limit(limit).all()
    return {"items": [job_to_dict(j) for j in jobs], "total": len(jobs)}


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_to_dict(job, full=True)


class CreateJobRequest(BaseModel):
    driver_phone: Optional[str] = None
    driver_name: Optional[str] = None
    vehicle_info: Optional[str] = None
    location: Optional[str] = None
    message: str
    source: str = "manual"


@app.post("/api/v1/jobs")
async def create_job(req: CreateJobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually create a job (fleet manager UI)."""
    job = Job(
        status="OPEN",
        type="ROADSIDE",
        summary=req.message[:200],
        raw_message=req.message,
        driver_phone=req.driver_phone,
        driver_name=req.driver_name,
        vehicle_info=req.vehicle_info,
        location=req.location,
        source=req.source,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(run_agent_for_job, job.id)
    return job_to_dict(job)


@app.patch("/api/v1/jobs/{job_id}")
def update_job(job_id: str, data: dict, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for key, val in data.items():
        if hasattr(job, key):
            setattr(job, key, val)
    if data.get("status") == "RESOLVED":
        job.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return job_to_dict(job)


@app.get("/api/v1/vendors")
def list_vendors(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).all()
    return [{"id": v.id, "name": v.name, "phone": v.phone,
             "types": v.service_types, "rating": v.rating,
             "eta_min": v.avg_response_min} for v in vendors]


@app.get("/api/v1/stats")
def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.query(func.count(Job.id)).scalar()
    by_status = db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
    return {
        "total": total,
        "by_status": {s: c for s, c in by_status}
    }


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "Uproad AI"}


def job_to_dict(job: Job, full: bool = False) -> dict:
    d = {
        "id": job.id,
        "status": job.status,
        "type": job.type,
        "summary": job.summary,
        "source": job.source,
        "driver_phone": job.driver_phone,
        "driver_name": job.driver_name,
        "vehicle_info": job.vehicle_info,
        "location": job.location,
        "assigned_vendor_name": job.assigned_vendor_name,
        "assigned_vendor_phone": job.assigned_vendor_phone,
        "vendor_eta_minutes": job.vendor_eta_minutes,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "resolved_at": job.resolved_at.isoformat() if job.resolved_at else None,
    }
    if full:
        d["actions"] = _parse_list(job.actions)
        d["agent_runs"] = _parse_list(job.agent_runs)
        d["raw_message"] = job.raw_message
    return d


# ============================================================
# SERVE REACT FRONTEND (production)
# ============================================================

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("webhook/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404)
        index_path = os.path.join(frontend_dist, "index.html")
        with open(index_path) as f:
            return HTMLResponse(f.read())
