import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from livekit import api
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.services.lead_service import get_or_reset_test_lead
from app.utils.security import require_admin

router = APIRouter(prefix="/api/assistant", tags=["assistant"], dependencies=[Depends(require_admin)])


@router.get("/preview")
async def preview_assistant(db: Session = Depends(get_db)):
    # Reuse a single fixed "Nasir Sultan" lead so a browser test call goes through the exact
    # same agent -> qualification pipeline as a real call, letting you verify data
    # actually lands in the database (check /leads/<test_lead_id> after the call) —
    # reset to a clean pending state on every preview fetch so stale data from a
    # previous test doesn't linger.
    if not (settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret):
        raise HTTPException(status_code=400, detail="LiveKit is not configured (LIVEKIT_URL/API_KEY/API_SECRET)")

    test_lead = get_or_reset_test_lead(db)
    room_name = f"preview-{test_lead.id}-{uuid.uuid4().hex[:8]}"
    metadata = {"lead_id": test_lead.id, "full_name": test_lead.full_name or ""}

    lkapi = api.LiveKitAPI(
        url=settings.livekit_url, api_key=settings.livekit_api_key, api_secret=settings.livekit_api_secret
    )
    try:
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=settings.livekit_agent_name,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )
    finally:
        await lkapi.aclose()

    identity = f"browser-{test_lead.id}"
    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name(test_lead.full_name or "Test caller")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    return {
        "livekit_url": settings.livekit_url,
        "token": token,
        "room_name": room_name,
        "test_lead_id": test_lead.id,
    }
