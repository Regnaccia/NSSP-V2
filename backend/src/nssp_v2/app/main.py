from fastapi import FastAPI

from nssp_v2.app.api import admin, auth, health, logistica, produzione, sync

app = FastAPI(
    title="ODE OMR V2",
    version="0.1.0",
    description="Operational Decision Engine — OMR V2",
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(logistica.router, prefix="/api")
app.include_router(produzione.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
