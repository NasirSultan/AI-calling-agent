from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/voice_agent"

    admin_username: str = "admin"
    admin_password: str = "admin123"
    jwt_secret: str = "change-this-secret"
    jwt_expire_minutes: int = 720

    vapi_api_key: str = ""
    vapi_public_key: str = ""
    # When set, calls use this saved dashboard assistant (assistantId) instead of the
    # transient inline assistant built from assistant_prompt.py.
    vapi_assistant_id: str = ""
    vapi_phone_number_id: str = ""
    vapi_webhook_secret: str = ""
    vapi_server_url: str = ""

    # LiveKit (WebRTC room infra + SIP dial-out) + the OpenAI Realtime model that
    # runs inside the agent worker (app/livekit_agent.py).
    openai_api_key: str = ""
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    livekit_sip_trunk_id: str = ""
    livekit_agent_name: str = "nit-reactivation-agent"

    # Twilio: only needed to run `python -m app.twilio_setup` once to provision the
    # outbound SIP trunk; not read at normal app runtime.
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_trunk_domain: str = ""

    crm_webhook_url: str = ""

    calling_start_hour: int = 10
    calling_end_hour: int = 19
    max_concurrent_calls: int = 5
    max_retries: int = 3
    retry_gap_hours: int = 3
    timezone: str = "Asia/Karachi"
    qa_sample_rate: float = 0.05
    eligibility_baseline_description: str = (
        "a CGPA of 2.0 out of 4.0, 50% marks, or an equivalent pass grade or higher"
    )

    class Config:
        env_file = ".env"


settings = Settings()
