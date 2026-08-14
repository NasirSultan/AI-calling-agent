import asyncio
import logging
from app.config.database import SessionLocal
from app.models import Lead, LeadStatus
from app.services import campaign_service, livekit_service, crm_service, qualification_service

logger = logging.getLogger("dialer")

LOOP_INTERVAL_SECONDS = 15


async def dialer_loop():
    while True:
        try:
            await _tick()
        except Exception as exc:
            logger.exception("Dialer tick failed: %s", exc)
        await asyncio.sleep(LOOP_INTERVAL_SECONDS)


async def _place_call(lead_id: int, phone: str, full_name: str | None) -> None:
    try:
        room_name = await livekit_service.start_call(phone, lead_id, full_name)
        logger.info("Call started: lead_id=%d phone=%s room_name=%s", lead_id, phone, room_name)
    except livekit_service.CallSetupError as exc:
        # SIP dial failed AFTER the agent already joined the (now-empty) room — its
        # own shutdown callback independently classifies and writes the outcome via
        # qualification_service.process_call_result. Log only, don't double-write.
        logger.warning("SIP dial failed for lead_id=%d phone=%s (agent will record outcome): %s", lead_id, phone, exc)
    except Exception as exc:
        # Dispatch itself failed — no agent job was ever created, so there's no
        # shutdown callback to write the result instead; the dialer must do it.
        logger.error("Failed to dispatch call for lead_id=%d phone=%s: %s", lead_id, phone, exc)
        db = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                qualification_service.mark_dispatch_failed(db, lead)
        finally:
            db.close()


async def _tick():
    db = SessionLocal()
    try:
        campaign = campaign_service.get_campaign(db)
        campaign = campaign_service.apply_due_schedule(db, campaign)
        if not campaign.is_running:
            logger.debug("Tick skipped: campaign is not running")
            return
        if not campaign_service.has_leads_remaining(db):
            campaign_service.set_running(db, False)
            logger.info("Campaign auto-stopped: no pending, in-flight, or retry-due leads remain")
            return
        if not campaign_service.within_calling_hours(campaign):
            logger.debug("Tick skipped: outside calling hours")
            return
        active = campaign_service.count_active_calls(db)
        slots = campaign.max_concurrent_calls - active
        if slots <= 0:
            logger.debug("Tick skipped: no free slots (%d/%d active)", active, campaign.max_concurrent_calls)
            return
        leads = campaign_service.pick_next_leads(db, slots)
        logger.info(
            "Tick: %d active call(s), %d slot(s) free, %d lead(s) picked to call",
            active, slots, len(leads),
        )
        # Mark picked leads `calling` up front, then fire each dial as an independent
        # task — livekit_service.start_call's wait_until_answered=True blocks for the
        # whole ring duration, so awaiting these serially would ring calls one at a
        # time instead of concurrently.
        for lead in leads:
            lead.status = LeadStatus.calling
        db.commit()
        for lead in leads:
            asyncio.create_task(_place_call(lead.id, lead.phone, lead.full_name))

        synced = await crm_service.sync_finished_leads(db)
        if synced:
            logger.info("CRM sync: %d lead(s) synced", synced)
    finally:
        db.close()
