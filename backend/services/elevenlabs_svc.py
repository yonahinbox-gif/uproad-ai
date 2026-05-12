"""
ElevenLabs Conversational AI integration.
Handles:
 - Creating intake agent (for inbound driver calls)
 - Creating dispatch agent (for outbound vendor calls)
 - Getting signed WebSocket URLs with per-call context injection
"""
import httpx
import logging
from config import ELEVENLABS_API_KEY

logger = logging.getLogger(__name__)
BASE = "https://api.elevenlabs.io/v1"
HEADERS = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}

# Best ElevenLabs voice for realistic professional calls
# "Charlie" - natural, conversational, very human
VOICE_ID = "IKne3meq5aSn9XLyUdCD"

# -------------------------------------------------------------------------
# Agent creation
# -------------------------------------------------------------------------

INTAKE_SYSTEM_PROMPT = """You are Alex, a professional fleet dispatch coordinator at Uproad Fleet Management.
A truck driver is calling because their vehicle has broken down or needs roadside assistance.

Your job:
1. Greet them warmly and professionally.
2. Ask for their name and what vehicle they're driving (make, model, year if they know it).
3. Ask exactly what the problem is -- be specific (tire flat? engine warning light? out of fuel? stuck?).
4. Ask for their exact location -- highway name, exit number, nearest mile marker, or address.
5. Tell them: "Got it. I'm dispatching help right now and you'll get a text confirmation shortly. Stay with your vehicle and keep your hazards on."
6. Thank them and end the call professionally.

Keep it under 2 minutes. Be calm, confident, and reassuring. Don't over-explain."""

DISPATCH_SYSTEM_PROMPT = """You are Alex, a professional fleet coordinator at Uproad Fleet Management.
You are calling a roadside service vendor to request emergency dispatch for one of our trucks.

Context will be injected via dynamic variables:
- {{vendor_name}}: the vendor's business name
- {{problem}}: what's wrong with the truck
- {{vehicle}}: the truck description
- {{location}}: where the truck is
- {{job_id}}: our job reference number

Your job:
1. Introduce yourself: "Hi, this is Alex calling from Uproad Fleet Management."
2. State the situation clearly: vehicle, problem, location.
3. Ask if they can dispatch immediately and get an ETA.
4. Confirm the job reference number.
5. Get their technician's name or callback number if possible.
6. Thank them and end professionally.

Be direct and efficient. This is time-sensitive."""


async def create_agent(name: str, system_prompt: str, first_message: str) -> str:
    """Create an ElevenLabs Conversational AI agent. Returns agent_id."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE}/convai/agents/create",
            headers=HEADERS,
            json={
                "name": name,
                "conversation_config": {
                    "agent": {
                        "prompt": {
                            "prompt": system_prompt,
                            "llm": "claude-3-5-sonnet",
                            "temperature": 0.4,
                            "max_tokens": 1024,
                        },
                        "first_message": first_message,
                        "language": "en",
                    },
                    "tts": {
                        "voice_id": VOICE_ID,
                        "model_id": "eleven_turbo_v2_5",
                        "audio_encoding": "ulaw_8000",
                        "optimize_streaming_latency": 3,
                    },
                    "asr": {
                        "quality": "high",
                        "provider": "elevenlabs",
                        "user_input_audio_format": "ulaw_8000",
                    },
                    "turn": {
                        "turn_timeout": 7,
                        "silence_end_call_timeout": 20,
                    },
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        agent_id = resp.json()["agent_id"]
        logger.info(f"Created ElevenLabs agent '{name}': {agent_id}")
        return agent_id


async def get_signed_url(agent_id: str, dynamic_variables: dict = None) -> str:
    """
    Get a one-time signed WebSocket URL for a conversation.
    Optionally inject dynamic variables for context-specific calls.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE}/convai/conversation/get_signed_url",
            headers=HEADERS,
            params={"agent_id": agent_id},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["signed_url"]


async def get_conversation_transcript(conversation_id: str) -> dict:
    """Fetch transcript + analysis for a completed conversation."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE}/convai/conversations/{conversation_id}",
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
        return {}


async def list_agents() -> list:
    """List all ElevenLabs agents for this account."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE}/convai/agents", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("agents", [])
        return []


async def ensure_agents_exist(intake_id: str, dispatch_id: str) -> tuple[str, str]:
    """
    Check if agents exist; create them if not.
    Returns (intake_agent_id, dispatch_agent_id).
    """
    # Verify or create intake agent
    if not intake_id:
        intake_id = await create_agent(
            name="Uproad Intake Agent",
            system_prompt=INTAKE_SYSTEM_PROMPT,
            first_message="Hi, you've reached Uproad Fleet roadside assistance. This is Alex -- what's happening with your truck today?"
        )

    # Verify or create dispatch agent
    if not dispatch_id:
        dispatch_id = await create_agent(
            name="Uproad Dispatch Agent",
            system_prompt=DISPATCH_SYSTEM_PROMPT,
            first_message="Hi, this is Alex calling from Uproad Fleet Management. I have an urgent dispatch request."
        )

    return intake_id, dispatch_id
