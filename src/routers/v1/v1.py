from fastapi import APIRouter
from .automation.automation import router as automation_router
#from .CHANGEME_infrastructure.CHANGEME_infrastructure import router as CHANGEME_infrastructure_router

router = APIRouter()
router.include_router(automation_router, prefix="/automation")
#No longer needed
#router.include_router(CHANGEME_infrastructure_router, prefix="/CHANGEME_infrastructure")
