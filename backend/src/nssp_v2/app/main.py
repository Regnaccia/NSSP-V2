from fastapi import FastAPI

from nssp_v2.app.api import health

app = FastAPI(
    title="ODE OMR V2",
    version="0.1.0",
    description="Operational Decision Engine — OMR V2",
)

app.include_router(health.router)
