from pydantic import BaseModel
from typing import Any
from .response_meta_schema import ResponseMetaSchema

class ErrorGeneralSchema(BaseModel):
    """
    Schema for a general error response.

    This schema defines the structure of a common error response, including metadata
    about the error and an optional data field for additional information.
    """
    meta: ResponseMetaSchema
    data: Any

type_content = "application/json"

error_general_schema = {
    "definitions": {
        "ErrorGeneralSchema": {
            "type": "object",
            "properties": {
                "meta": {
                    "type": "object",
                    "properties": {
                        "transactionID": {"type": "string"},
                        "status": {"type": "string"},
                        "statusCode": {"type": "integer"},
                        "timestamp": {"type": "string"},
                        "message": {"type": "string"},
                        "time_elapsed": {"type": "float"}
                    }
                },
                "data": {"type": "any"},
            },
        }
    }
}

error_response_general_405 = {
    "description": "Method Not Allowed",
    "content": {
        type_content: {
            "schema": error_general_schema["definitions"]["ErrorGeneralSchema"],
            "examples": {
                "MethodNotAllowed": {
                    "value": ErrorGeneralSchema(
                        data={"user_message": "Method Not Allowed"},
                        meta=ResponseMetaSchema(
                            transactionID="unknown",
                            status="error",
                            statusCode=405,
                            timestamp="2025-02-19T00:00:00Z",
                            message="Method Not Allowed",
                            time_elapsed=0.0
                        )
                    ).model_dump()
                }
            }
        }
    }
}