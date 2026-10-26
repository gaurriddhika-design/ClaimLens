from fastapi import APIRouter
from ..core.config import settings
from ..schemas import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Report API health and safe provider-configuration status."""
    return HealthResponse(
        status="healthy",
        llm_provider_configured=bool(
            settings.llm_provider and (settings.llm_api_key or settings.llm_base_url)
        ),
        search_provider_configured=bool(settings.search_provider and settings.search_api_key),
        database_configured=bool(settings.database_url),
    )
