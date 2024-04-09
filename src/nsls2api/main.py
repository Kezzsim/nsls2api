import os
from pathlib import Path

import fastapi
import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from starlette.staticfiles import StaticFiles

from nsls2api.api.v1 import admin_api as admin_api_v1
from nsls2api.api.v1 import beamline_api as beamline_api_v1
from nsls2api.api.v1 import facility_api as facility_api_v1
from nsls2api.api.v1 import proposal_api as proposal_api_v1
from nsls2api.api.v1 import stats_api as stats_api_v1
from nsls2api.api.v1 import user_api as user_api_v1
from nsls2api.infrastructure import app_setup, mongodb_setup
from nsls2api.infrastructure.config import get_settings
from nsls2api.infrastructure.logging import logger
from nsls2api.middleware import ProcessTimeMiddleware
from nsls2api.views import diagnostics, home

settings = get_settings()

current_file = Path(__file__)
current_file_dir = current_file.parent
current_file_dir_absolute = current_file_dir.absolute()
project_root = current_file_dir.parent
project_root_absolute = project_root.resolve()
static_root_absolute = current_file_dir_absolute / "static"


development_mode = True
app_setup.development_mode = development_mode


middleware = [Middleware(ProcessTimeMiddleware)]

app = fastapi.FastAPI(
    title="NSLS-II API", middleware=middleware, lifespan=app_setup.app_lifespan
)


app.add_middleware(CorrelationIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["X-Requested-With", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


def configure_routing():
    app.include_router(proposal_api_v1.router, prefix="/v1", tags=["proposal"])
    app.include_router(stats_api_v1.router, prefix="/v1")
    app.include_router(beamline_api_v1.router, prefix="/v1", tags=["beamline"])
    app.include_router(facility_api_v1.router, prefix="/v1", tags=["facility"])
    app.include_router(user_api_v1.router, prefix="/v1", tags=["user"])
    app.include_router(admin_api_v1.router, prefix="/v1", tags=["admin"])

    # Just log the current working directory - useful is some of the static files are not found.
    logger.info(f"Current working directory: {os.getcwd()}")

    # Also include our webpages
    app.include_router(home.router)
    app.include_router(diagnostics.router)
    app.mount("/static", StaticFiles(directory=static_root_absolute), name="static")
    app.mount(
        "/assets",
        StaticFiles(directory=static_root_absolute / "assets"),
        name="assets",
    )


def main():
    configure_routing()
    uvicorn.run(app, port=8081, log_config="uvicorn_log_config.yml")


if __name__ == "__main__":
    main()
else:
    configure_routing()
