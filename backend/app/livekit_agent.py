"""LiveKit agent worker process. Runs separately from the FastAPI app (spawned as
a child process by app/main.py's lifespan via `python -m app.livekit_agent start`)
— joins each dispatched room, runs the conversation through OpenAI's Realtime
model, and at shutdown extracts structured data and writes the call result
straight to the DB (no webhook receiver, unlike the old Vapi integration).
"""
import asyncio
import json
import logging
from datetime import datetime

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, RoomInputOptions
from livekit.plugins import noise_cancellation, openai as lk_openai
from openai.types.beta.realtime.session import TurnDetection

from app.config.database import SessionLocal
from app.config.settings import settings
from app.services import qualification_service
from app.services.analysis_service import extract_structured_data
from app.services.assistant_prompt import build_system_prompt

logger = logging.getLogger("livekit_agent")

server = AgentServer(
    # Passed explicitly rather than relying on OS env vars — the CLI worker only
    # reads LIVEKIT_URL/API_KEY/API_SECRET from the real process environment, not
    # from backend/.env (only our own pydantic-settings-based settings.py reads
    # that file).
    ws_url=settings.livekit_url,
    api_key=settings.livekit_api_key,
    api_secret=settings.livekit_api_secret,
)


@server.rtc_session(agent_name=settings.livekit_agent_name)
async def entrypoint(ctx: agents.JobContext):
    metadata = json.loads(ctx.job.metadata or "{}")
    lead_id = metadata.get("lead_id")
    full_name = metadata.get("full_name") or None

    system_prompt, first_message = build_system_prompt(full_name)
    started_at = datetime.utcnow()

    session = AgentSession(
        llm=lk_openai.realtime.RealtimeModel(
            model="gpt-realtime-mini",
            voice="marin",
            temperature=0.3,
            # Passed explicitly for the same reason as ws_url/api_key above — the
            # openai SDK client inside this plugin also defaults to reading
            # OPENAI_API_KEY from the process environment.
            api_key=settings.openai_api_key,
            turn_detection=TurnDetection(
                type="server_vad",
                threshold=0.5,
                prefix_padding_ms=300,
                silence_duration_ms=1500,
                create_response=True,
                interrupt_response=True,
            ),
        ),
    )

    result_written = False

    async def write_result(ended_reason: str):
        nonlocal result_written
        if result_written or lead_id is None:
            return
        result_written = True

        transcript_lines = []
        caller_spoke = False
        for item in session.history.items:
            role = getattr(item, "role", None)
            text = getattr(item, "text_content", None) or ""
            if role == "user" and text:
                caller_spoke = True
                transcript_lines.append(f"User: {text}")
            elif role == "assistant" and text:
                transcript_lines.append(f"Assistant: {text}")
        transcript = "\n".join(transcript_lines)

        structured = {}
        if caller_spoke:
            structured = await extract_structured_data(transcript)

        db = SessionLocal()
        try:
            qualification_service.process_call_result(
                db,
                lead_id=lead_id,
                room_name=ctx.room.name,
                ended_reason=ended_reason,
                transcript=transcript,
                structured=structured,
                duration_seconds=(datetime.utcnow() - started_at).total_seconds(),
                recording_url=None,  # LiveKit Egress not wired up — always None for now
            )
        except Exception:
            logger.exception("Failed to write call result for lead_id=%s room=%s", lead_id, ctx.room.name)
        finally:
            db.close()

    @ctx.room.on("disconnected")
    def _on_disconnected():
        asyncio.create_task(write_result("completed"))

    agent = Agent(instructions=system_prompt)
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # BVCTelephony (not plain BVC) is tuned for narrow/compressed phone-call
            # audio, applied agent-side only per LiveKit's own guidance (don't also
            # enable it at the trunk level).
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )
    await session.generate_reply(instructions=f"Say exactly, word for word: {first_message}")


if __name__ == "__main__":
    agents.cli.run_app(server)
