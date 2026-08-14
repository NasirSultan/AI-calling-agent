import asyncio
import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import Base, engine
from app.api import auth, leads, campaign, webhooks, export, crm, assistant
from app.workers.dialer_worker import dialer_loop
import app.models

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("main")

BACKEND_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(dialer_loop())

    # Runs the LiveKit agent (app/livekit_agent.py) as a real child OS process
    # rather than an in-process task — livekit-agents' own worker process model
    # (registration, job dispatch handling, graceful drain) expects to own its
    # process, not share the FastAPI event loop.
    agent_process = subprocess.Popen(
        [sys.executable, "-m", "app.livekit_agent", "start"],
        cwd=str(BACKEND_DIR),
    )
    logger.info("Spawned LiveKit agent worker process (pid=%d)", agent_process.pid)

    yield

    task.cancel()
    agent_process.terminate()
    try:
        agent_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        agent_process.kill()


app = FastAPI(title="AI Voice Calling Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(campaign.router)
app.include_router(webhooks.router)
app.include_router(export.router)
app.include_router(crm.router)
app.include_router(assistant.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
