from pydantic import BaseModel
from typing import Any, Dict
from .response_meta_schema import ResponseMetaSchema

class ResponseGeneralSchema(BaseModel):
    """
    Schema for a general API response.

    This schema defines the structure of a common API response, including metadata
    about the request and the actual data returned.
    """
    meta: ResponseMetaSchema
    data: Any

type_content = "application/json"

success_general_schema = {
    "definitions": {
        "ResponseGeneralSchema": {
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

success_response_example = {
    "description": "Successful API Response",
    "content": {
        type_content: {
            "schema": success_general_schema["definitions"]["ResponseGeneralSchema"],
            "examples": {
                "SuccessExample": {
                    "value": ResponseGeneralSchema(
                        meta=ResponseMetaSchema(
                            transactionID="bdae4708-72fd-49a8-8f73-646605101072",
                            status="SUCCESS",
                            statusCode=200,
                            timestamp="2025-02-19T00:00:00Z",
                            message="Success",
                            time_elapsed=0.0
                        ),
                        data={"dns": "https://example.com/puntodeventa/api/v1/"},
                    ).model_dump()
                }
            }
        }
    }
}