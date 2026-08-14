import logging
import uuid
from livekit import api
from app.config.settings import settings

logger = logging.getLogger("livekit")


def _client() -> api.LiveKitAPI:
    return api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )


class CallSetupError(Exception):
    """Raised when dispatching the agent or dialing the SIP participant fails
    after the agent has already joined the room — the agent's own shutdown
    callback (livekit_agent.py) is the sole source of truth for the lead's
    outcome in that case, this is log-only for the dialer."""


async def start_call(phone: str, lead_id: int, full_name: str | None) -> str:
    """Dispatches the agent to a fresh room, then dials the lead into it over the
    configured Twilio SIP trunk. Blocks until the call is answered or fails
    (wait_until_answered=True), so callers should fire this as an independent task
    rather than awaiting it serially for concurrent dialing."""
    room_name = f"call-{lead_id}-{uuid.uuid4().hex[:8]}"
    metadata = {"lead_id": lead_id, "full_name": full_name or ""}
    lkapi = _client()
    try:
        import json

        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=settings.livekit_agent_name,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )
        try:
            await lkapi.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=settings.livekit_sip_trunk_id,
                    sip_call_to=phone,
                    room_name=room_name,
                    participant_identity=f"lead-{lead_id}",
                    wait_until_answered=True,
                )
            )
        except Exception as exc:
            # The agent has already been dispatched and joined the (now-empty) room —
            # its own shutdown callback will independently classify/write the outcome.
            # Don't double-write the result here; just log and let the caller know.
            raise CallSetupError(str(exc)) from exc
    finally:
        await lkapi.aclose()
    return room_name


def classify_dial_error(message: str) -> str:
    """Best-effort bucket of a SIP dial failure message into 'invalid' or
    'no_answer' — there's no clean disconnect-reason enum like Vapi's endedReason
    for SIP failures, so this matches on the exception text."""
    lowered = message.lower()
    if any(s in lowered for s in ("invalid", "not found", "unallocated", "malformed")):
        return "invalid"
    return "no_answer"
