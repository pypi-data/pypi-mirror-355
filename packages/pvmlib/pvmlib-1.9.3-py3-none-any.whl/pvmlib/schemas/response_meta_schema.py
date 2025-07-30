from pydantic import BaseModel

class ResponseMetaSchema(BaseModel):
    """
    Schema for the metadata included in API responses.

    This schema defines the structure of the metadata that accompanies the actual data
    returned by the API. It provides information about the request, its status,
    and any errors that may have occurred.
    """
    transactionID: str
    status: str
    statusCode: int
    timestamp: str
    message: str
    time_elapsed: float