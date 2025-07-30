from pvmlib.schemas.success_schema import ResponseGeneralSchema, ResponseMetaSchema
from pvmlib.context.request_context import RequestContext
from datetime import datetime
from time import time
from typing import Any

class TypeSuccess:
    """
    A class to map HTTP success status codes to status strings.
    """
    success = {
        200: "SUCCESS",
        201: "CREATED",
        202: "ACCEPTED",
        204: "NO_CONTENT",
        206: "PARTIAL_CONTENT",
        207: "MULTI_STATUS",
        208: "ALREADY_REPORTED",
        226: "IM_USED"
    }

class SuccessResponse(ResponseGeneralSchema):
    """
    Custom class for handling successful API responses.

    This class extends ResponseGeneralSchema and automatically formats the response
    for successful operations. It includes metadata such as the transaction ID, status,
    status code, timestamp, and message.
    """
    def __init__(
            self,
            status_code: int = 200,
            data: Any = None,
            message: str = "Request processed successfully"
    ):
        """
        Initializes the SuccessResponse.

        Args:
            status_code (int): The HTTP status code for the success response. Defaults to 200 (OK).
            data (Any, optional): The data payload of the response. Defaults to None.
            message (str): A custom success message. Defaults to "Request processed successfully".
        """
        context = RequestContext()
        start_time = context.get_start_time()
        time_elapsed = time() - start_time if start_time else 0.0
        transaction_id = context.get_tracing_id()

        super().__init__(
            data=data,
            meta=ResponseMetaSchema(
                transactionID=transaction_id,
                status=TypeSuccess.success.get(status_code),
                statusCode=status_code,
                timestamp=datetime.now().isoformat(),
                message=message,
                time_elapsed=f"{time_elapsed:.2f}"
            )
        )