from fastapi import APIRouter
from pvmlib.schemas.healthcheck_reponse_schema import responses_liveness, LivenessResponse

liveness_router = APIRouter()

@liveness_router.get(
    "/healthcheck/liveness", 
    responses=responses_liveness, 
    summary="Status del servicio",
    response_model=LivenessResponse
)
async def liveness() -> LivenessResponse:
    """ Comprueba que el servicio este operando """
    return LivenessResponse(
        status="UP",
        code=200,
        dependencies={}
    )