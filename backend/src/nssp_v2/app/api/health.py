from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def get_health():
    return {"status": "ok"}


@router.get("/ready")
def get_ready():
    return {"status": "ready"}
