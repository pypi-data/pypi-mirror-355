import sys

print(f"SYS.PATH IN APP.PY: {sys.path}")
import os
import logging

from fastapi import FastAPI
from service.registry import list_supported_env_types, register_environment
from service.core_routes import api_router
from service.external_registry import ExternalRegistryConfig, load_external_environments

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register built-in environments at import time
import examples.sokoban.environment as sok

register_environment("Sokoban", sok.SokobanEnvironment)
import examples.crafter_classic.environment as cc

register_environment("CrafterClassic", cc.CrafterClassicEnvironment)
import examples.math.environment as me

register_environment("HendryksMath", me.HendryksMathEnv)
import examples.verilog.environment as ve

register_environment("Verilog", ve.VerilogEnvironment)

app = FastAPI(title="Environment Service")


@app.on_event("startup")
async def startup_event():
    """Load external environments on startup."""
    # Support configuration-based loading for external environments
    # You can set EXTERNAL_ENVIRONMENTS env var with JSON config
    external_config = os.getenv("EXTERNAL_ENVIRONMENTS")
    if external_config:
        try:
            import json

            config_data = json.loads(external_config)
            config = ExternalRegistryConfig(
                external_environments=config_data.get("external_environments", [])
            )
            load_external_environments(config)
        except Exception as e:
            logger.error(f"Failed to load external environment config: {e}")

    # Log all registered environments
    logger.info(f"Registered environments: {list_supported_env_types()}")


# Mount the main API router
app.include_router(api_router, tags=["environments"])
