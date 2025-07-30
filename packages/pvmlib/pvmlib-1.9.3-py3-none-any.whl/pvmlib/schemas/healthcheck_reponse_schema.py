from pydantic import BaseModel
from typing import Dict

class LivenessResponse(BaseModel):
    """
    Schema for a liveness probe response.

    Indicates whether the application itself is running and healthy.
    """
    status: str
    code: int
    dependencies: Dict[str, str]

class ReadinessResponse(BaseModel):
    """
    Schema for a readiness probe response.

    Indicates whether the application is ready to handle traffic.  This may depend on
    the status of other services or dependencies.
    """
    status: str
    code: int
    dependencies: Dict[str, str]

responses_liveness = {
    200: {
        "description": "Successful Liveness Check Response",
        "content": {
            "application/json": {
                "schema": {
                    "$ref": "#/components/schemas/LivenessResponse"
                },
                "example": {
                    "status": "UP",
                    "code": 200,
                    "dependencies": {
                        "mongodb": "UP",
                        "auth-service": "UP",
                        "payment-service": "UP",
                        "notification-service": "DOWN"
                    }
                }
            }
        }
    }
}

responses_readiness = {
    200: {
        "description": "Successful Readiness Check Response",
        "content": {
            "application/json": {
                "schema": {
                    "$ref": "#/components/schemas/ReadinessResponse"
                },
                "example": {
                    "status": "ready",
                    "code": 200,
                    "dependencies": {
                        "mongodb": "UP",
                        "auth-service": "UP",
                        "payment-service": "UP",
                        "notification-service": "DOWN"
                    }
                }
            }
        }
    }
}
