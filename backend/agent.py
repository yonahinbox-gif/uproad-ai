"""
Claude-powered RoadsideDispatchAgent.
Receives job context -> uses tools to coordinate dispatch.
"""
import anthropic
import json
import time
import logging
from datetime import datetime, timezone
from services.twilio_svc import send_sms, make_outbound_call
from services.vendors import find_vendors_for_problem
from config import ANTHROPIC_API_KEY, BASE_URL

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are the Uproad AI Dispatch Agent -- an autonomous coordinator for commercial fleet roadside assistance.

When you receive a breakdown job, you MUST:
1. Send an immediate SMS to the driver confirming you're on it
2. Analyze the problem to determine what type of vendor is needed
3. Find vendors using find_vendors tool
4. Send SMS to the best vendor(s) describing the job
5. Make a voice call to the top vendor to confirm dispatch and get ETA
6. Send a follow-up SMS to the driver with the vendor name and ETA
7. Update the job status to IN_PROGRESS

Rules:
- Always confirm with driver first (they're stranded and stressed)
- Use professional, clear language in all messages
- Be specific: include vehicle info, location, and job reference in every vendor contact
- If first vendor doesn't respond to call, try the next one
- Update job status when vendor confirms dispatch

You have access to these tools: send_sms, make_voice_call, find_vendors, update_job."""

TOOLS = [
    {
        "name": "send_sms",
        "description": "Send an SMS message to a phone number",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Phone number (E.164 format, e.g. +15551234567)"},
                "message": {"type": "string", "description": "The SMS message content"}
            },
            "required": ["to", "message"]
        }
    },
    {
        "name": "make_voice_call",
        "description": "Make a realistic AI voice call to a vendor to coordinate dispatch. The AI agent (Alex) will handle the full conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_phone": {"type": "string", "description": "Vendor phone number"},
                "vendor_name": {"type": "string", "description": "Vendor business name"},
                "job_id": {"type": "string", "description": "Job reference ID"},
                "problem": {"type": "string", "description": "What's wrong with the truck"},
                "vehicle": {"type": "string", "description": "Vehicle description"},
                "location": {"type": "string", "description": "Breakdown location"}
            },
            "required": ["vendor_phone", "vendor_name", "job_id", "problem", "vehicle", "location"]
        }
    },
    {
        "name": "find_vendors",
        "description": "Find the best vendors for a given problem type near a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "problem_description": {"type": "string", "description": "Description of the problem (e.g. 'blown tire', 'engine fault', 'out of fuel')"},
                "location": {"type": "string", "description": "Location of the breakdown"}
            },
            "required": ["problem_description"]
        }
    },
    {
        "name": "update_job",
        "description": "Update job status and assigned vendor information",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["IN_PROGRESS", "NEEDS_APPROVAL", "RESOLVED"],
                    "description": "New job status"
                },
                "assigned_vendor_name": {"type": "string", "description": "Name of vendor dispatched"},
                "assigned_vendor_phone": {"type": "string", "description": "Vendor phone number"},
                "vendor_eta_minutes": {"type": "number", "description": "Estimated arrival time in minutes"},
                "notes": {"type": "string", "description": "Any additional notes"}
            },
            "required": ["status"]
        }
    }
]


def execute_tool(tool_name: str, tool_input: dict, job: dict, dispatch_agent_id: str) -> dict:
    """Execute a tool call and return the result."""

    if tool_name == "send_sms":
        result = send_sms(to=tool_input["to"], message=tool_input["message"])
        return result

    elif tool_name == "find_vendors":
        vendors = find_vendors_for_problem(
            problem_description=tool_input["problem_description"],
            limit=3
        )
        return {"vendors": vendors, "count": len(vendors)}

    elif tool_name == "make_voice_call":
        # Build the TwiML URL that connects Twilio -> ElevenLabs
        import urllib.parse
        params = urllib.parse.urlencode({
            "agent_id": dispatch_agent_id,
            "job_id": tool_input["job_id"],
            "vendor_name": tool_input["vendor_name"],
            "problem": tool_input["problem"],
            "vehicle": tool_input["vehicle"],
            "location": tool_input["location"],
        })
        twiml_url = f"{BASE_URL}/webhook/voice/outbound?{params}"
        call_result = make_outbound_call(
            to=tool_input["vendor_phone"],
            twiml_url=twiml_url
        )
        # Simulate a positive outcome for demo (real outcome comes via webhook)
        call_result["outcome"] = "queued"
        call_result["summary"] = f"Alex from Uproad Fleet called {tool_input['vendor_name']} regarding {tool_input['problem']} at {tool_input['location']}. Call initiated."
        return call_result

    elif tool_name == "update_job":
        # Return the update -- caller applies it to the DB
        return {"updated": True, **tool_input}

    return {"error": f"Unknown tool: {tool_name}"}


def run_dispatch_agent(job: dict, dispatch_agent_id: str = "") -> dict:
    """
    Run the dispatch agent for a job.
    Returns: {actions: [...], agent_run: {...}, job_updates: {...}}
    """
    start_time = time.time()
    run_id = f"run_{int(start_time)}"
    actions = []
    job_updates = {}
    total_tokens = 0

    # Build initial user message
    user_message = f"""New breakdown job received. Please coordinate dispatch immediately.

JOB ID: {job['id']}
STATUS: {job.get('status', 'OPEN')}
SOURCE: {job.get('source', 'sms')}

DRIVER: {job.get('driver_name', 'Unknown')} | PHONE: {job.get('driver_phone', 'Unknown')}
VEHICLE: {job.get('vehicle_info', 'Unknown vehicle')}
LOCATION: {job.get('location', 'Unknown location')}
PROBLEM: {job.get('raw_message', job.get('summary', 'Breakdown reported'))}

Please handle this end to end: confirm with driver, find vendor, call vendor, update driver with ETA."""

    messages = [{"role": "user", "content": user_message}]

    logger.info(f"[{run_id}] Starting dispatch agent for job {job['id']}")

    # Agentic loop -- keep going until model stops using tools
    iteration = 0
    max_iterations = 10

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        total_tokens += response.usage.input_tokens + response.usage.output_tokens

        # Add assistant response to message history
        messages.append({"role": "assistant", "content": response.content})

        # Check if done
        if response.stop_reason == "end_turn":
            logger.info(f"[{run_id}] Agent finished after {iteration} iterations")
            break

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            timestamp = datetime.now(timezone.utc).isoformat()

            logger.info(f"[{run_id}] Tool call: {tool_name} with {json.dumps(tool_input)[:200]}")

            result = execute_tool(tool_name, tool_input, job, dispatch_agent_id)

            # Record action
            action = {
                "run_id": run_id,
                "agent": "RoadsideDispatchAgent",
                "action_type": tool_name,
                "payload": tool_input,
                "result": result,
                "timestamp": timestamp,
            }
            actions.append(action)

            # Capture job updates
            if tool_name == "update_job":
                job_updates.update(result)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })

        # Feed tool results back
        messages.append({"role": "user", "content": tool_results})

    duration = round(time.time() - start_time, 1)
    agent_run = {
        "run_id": run_id,
        "agent": "RoadsideDispatchAgent",
        "status": "completed",
        "duration_s": duration,
        "tools_used": len(actions),
        "tokens": total_tokens,
        "iterations": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(f"[{run_id}] Done. {len(actions)} actions, {total_tokens} tokens, {duration}s")

    return {
        "actions": actions,
        "agent_run": agent_run,
        "job_updates": job_updates,
    }
