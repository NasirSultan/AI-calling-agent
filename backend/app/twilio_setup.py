"""One-time, idempotent provisioning script: creates (or reuses) a Twilio Elastic
SIP Trunk wired to LiveKit as the outbound calling path.

Run manually, NOT at app startup:
    python -m app.twilio_setup

Only reads backend/.env (via app.config.settings) — never writes it. Prints the
resulting LIVEKIT_SIP_TRUNK_ID for you to paste into .env by hand.
"""
import asyncio
import secrets

from twilio.rest import Client
from livekit import api

from app.config.settings import settings

TRUNK_NAME = "nit-reactivation"
CREDENTIAL_USERNAME = "livekit"


def _get_or_create_trunk(client: Client):
    for trunk in client.trunking.v1.trunks.list():
        if trunk.friendly_name == TRUNK_NAME:
            return trunk
    return client.trunking.v1.trunks.create(friendly_name=TRUNK_NAME)


def _get_or_create_credential_list(client: Client, password: str):
    for cl in client.sip.credential_lists.list():
        if cl.friendly_name == TRUNK_NAME:
            credential_list = cl
            break
    else:
        credential_list = client.sip.credential_lists.create(friendly_name=TRUNK_NAME)

    existing_creds = client.sip.credential_lists(credential_list.sid).credentials.list()
    for cred in existing_creds:
        client.sip.credential_lists(credential_list.sid).credentials(cred.sid).delete()
    client.sip.credential_lists(credential_list.sid).credentials.create(
        username=CREDENTIAL_USERNAME, password=password
    )
    return credential_list


def _ensure_trunk_credential_list(client: Client, trunk_sid: str, credential_list_sid: str):
    # NOTE: the trunk-level subresource is "credentials_lists" (extra "s"), NOT
    # "credential_lists" like the top-level client.sip.credential_lists resource.
    existing = client.trunking.v1.trunks(trunk_sid).credentials_lists.list()
    if not any(cl.sid == credential_list_sid for cl in existing):
        client.trunking.v1.trunks(trunk_sid).credentials_lists.create(
            credential_list_sid=credential_list_sid
        )


def _ensure_phone_number(client: Client, trunk_sid: str, phone_number: str):
    numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
    if not numbers:
        raise RuntimeError(
            f"Phone number {phone_number} not found on this Twilio account — "
            "buy/import it in the Twilio console first."
        )
    phone_number_sid = numbers[0].sid
    existing = client.trunking.v1.trunks(trunk_sid).phone_numbers.list()
    if not any(pn.sid == phone_number_sid for pn in existing):
        client.trunking.v1.trunks(trunk_sid).phone_numbers.create(phone_number_sid=phone_number_sid)


async def _sync_livekit_trunk(trunk_domain: str, phone_number: str, password: str) -> str:
    lkapi = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )
    try:
        existing = await lkapi.sip.list_outbound_trunk(api.ListSIPOutboundTrunkRequest())
        for trunk in existing.items:
            if trunk.name == TRUNK_NAME:
                # Delete and recreate so the stored auth password stays in sync with
                # the one just (re)generated on the Twilio credential list above.
                await lkapi.sip.delete_trunk(api.DeleteSIPTrunkRequest(sip_trunk_id=trunk.sip_trunk_id))

        created = await lkapi.sip.create_outbound_trunk(
            api.CreateSIPOutboundTrunkRequest(
                trunk=api.SIPOutboundTrunkInfo(
                    name=TRUNK_NAME,
                    address=trunk_domain,
                    numbers=[phone_number],
                    auth_username=CREDENTIAL_USERNAME,
                    auth_password=password,
                )
            )
        )
        return created.sip_trunk_id
    finally:
        await lkapi.aclose()


def main():
    required = {
        "TWILIO_ACCOUNT_SID": settings.twilio_account_sid,
        "TWILIO_AUTH_TOKEN": settings.twilio_auth_token,
        "TWILIO_PHONE_NUMBER": settings.twilio_phone_number,
        "TWILIO_TRUNK_DOMAIN": settings.twilio_trunk_domain,
        "LIVEKIT_URL": settings.livekit_url,
        "LIVEKIT_API_KEY": settings.livekit_api_key,
        "LIVEKIT_API_SECRET": settings.livekit_api_secret,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise SystemExit(f"Missing required .env values: {', '.join(missing)}")

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    password = secrets.token_urlsafe(24)

    trunk = _get_or_create_trunk(client)
    print(f"Twilio SIP trunk: {trunk.sid} ({trunk.friendly_name})")

    credential_list = _get_or_create_credential_list(client, password)
    print(f"Twilio credential list: {credential_list.sid} (username={CREDENTIAL_USERNAME})")

    _ensure_trunk_credential_list(client, trunk.sid, credential_list.sid)
    _ensure_phone_number(client, trunk.sid, settings.twilio_phone_number)
    print(f"Phone number {settings.twilio_phone_number} associated with trunk.")

    sip_trunk_id = asyncio.run(
        _sync_livekit_trunk(settings.twilio_trunk_domain, settings.twilio_phone_number, password)
    )
    print()
    print("Done. Paste this into backend/.env:")
    print(f"LIVEKIT_SIP_TRUNK_ID={sip_trunk_id}")


if __name__ == "__main__":
    main()
