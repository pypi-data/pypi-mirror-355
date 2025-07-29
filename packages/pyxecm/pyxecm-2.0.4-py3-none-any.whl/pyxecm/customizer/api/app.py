"""API Implemenation for the Customizer to start and control the payload processing."""

__author__ = "Dr. Marc Diefenbruch"
__copyright__ = "Copyright (C) 2024-2025, OpenText"
__credits__ = ["Kai-Philip Gatzweiler"]
__maintainer__ = "Dr. Marc Diefenbruch"
__email__ = "mdiefenb@opentext.com"

import logging
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from importlib.metadata import version

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from pyxecm.customizer.api.auth.router import router as auth_router
from pyxecm.customizer.api.common.functions import PAYLOAD_LIST
from pyxecm.customizer.api.common.metrics import payload_logs_by_payload, payload_logs_total
from pyxecm.customizer.api.common.router import router as common_router
from pyxecm.customizer.api.settings import api_settings
from pyxecm.customizer.api.terminal.router import router as terminal_router
from pyxecm.customizer.api.v1_csai.router import router as v1_csai_router
from pyxecm.customizer.api.v1_maintenance.router import router as v1_maintenance_router
from pyxecm.customizer.api.v1_otcs.router import router as v1_otcs_router
from pyxecm.customizer.api.v1_payload.functions import import_payload
from pyxecm.customizer.api.v1_payload.router import router as v1_payload_router
from pyxecm.maintenance_page import run_maintenance_page

# Check if Temp dir exists
if not os.path.exists(api_settings.temp_dir):
    os.makedirs(api_settings.temp_dir)

# Check if Logfile and folder exists and is unique
if os.path.isfile(os.path.join(api_settings.logfolder, api_settings.logfile)):
    customizer_start_time = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d_%H-%M",
    )
    api_settings.logfile = f"customizer_{customizer_start_time}.log"
elif not os.path.exists(api_settings.logfolder):
    os.makedirs(api_settings.logfolder)

handlers = [
    logging.FileHandler(os.path.join(api_settings.logfolder, api_settings.logfile)),
    logging.StreamHandler(sys.stdout),
]

logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s] [%(threadName)s] %(message)s",
    datefmt="%d-%b-%Y %H:%M:%S",
    level=api_settings.loglevel,
    handlers=handlers,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,  # noqa: ARG001
) -> AsyncGenerator:
    """Lifespan Method for FASTAPI to handle the startup and shutdown process.

    Args:
        app (FastAPI):
            The application.

    """

    logger.debug("Settings -> %s", api_settings)

    if api_settings.import_payload:
        logger.info("Importing filesystem payloads...")

        # Base Payload
        import_payload(payload=api_settings.payload)

        # External Payload
        import_payload(payload_dir=api_settings.payload_dir, dependencies=True)

        # Optional Payload
        import_payload(payload_dir=api_settings.payload_dir_optional)

    logger.info("Starting maintenance_page thread...")
    run_maintenance_page()

    logger.info("Starting processing thread...")
    PAYLOAD_LIST.run_payload_processing(concurrent=api_settings.concurrent_payloads)

    yield
    logger.info("Shutdown")
    PAYLOAD_LIST.stop_payload_processing()


app = FastAPI(
    docs_url="/api",
    title=api_settings.title,
    description=api_settings.description,
    openapi_url=api_settings.openapi_url,
    root_path=api_settings.root_path,
    lifespan=lifespan,
    version=version("pyxecm"),
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication Endpoint - Users are authenticated against Opentext Directory Services",
        },
        {
            "name": "payload",
            "description": "Get status and manipulate payload objects ",
        },
        {
            "name": "maintenance",
            "description": "Enable, disable or alter the maintenance mode.",
        },
    ],
)

## Add all Routers
app.include_router(router=common_router)
app.include_router(router=auth_router)
app.include_router(router=v1_maintenance_router)
app.include_router(router=v1_otcs_router)
app.include_router(router=v1_payload_router)
if api_settings.ws_terminal:
    app.include_router(router=terminal_router)
if api_settings.csai:
    app.include_router(router=v1_csai_router)

logger = logging.getLogger("CustomizerAPI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.trusted_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if api_settings.metrics:
    # Add Prometheus Instrumentator for /metrics
    instrumentator = Instrumentator().instrument(app).expose(app)
    instrumentator.add(payload_logs_by_payload(PAYLOAD_LIST))
    instrumentator.add(payload_logs_total(PAYLOAD_LIST))


def run_api() -> None:
    """Start the FASTAPI Webserver."""

    uvicorn.run(
        "pyxecm.customizer.api:app",
        host=api_settings.bind_address,
        port=api_settings.bind_port,
        workers=api_settings.workers,
    )
