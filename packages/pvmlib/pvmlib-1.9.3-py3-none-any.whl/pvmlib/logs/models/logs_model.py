from typing import Any, Dict, Optional
from pydantic import BaseModel

class Application(BaseModel):
    """
    Represents the application information for logging.

    This model holds details about the application that is generating the log message,
    such as its name, version, environment, and kind.
    """
    name: str
    version: str
    env: str
    kind: str

class Measurement(BaseModel):
    """
    Represents performance measurements associated with a log event.

    This model captures timing and performance-related data, such as the method being executed
    and the time taken for its execution.
    """
    method: str
    elapsed_time: float    

class ExceptionModel(BaseModel):
    """
    Represents exception information for error logs.

    This model holds details about an exception that occurred, including its name,
    message, and stack trace.
    """
    name: str
    message: str
    stackTrace: str

class DataLogger(BaseModel):
    """
    Represents the complete structure of a log message.

    This model combines various data points to form a comprehensive log entry.  It includes
    information about the log level, source, context, application, performance,
    and any associated exceptions.
    """
    level: str
    schema_version: str
    log_type: str
    source_ip: str
    status: str
    message: str
    log_origin: str
    timestamp: str
    tracing_id: str
    hostname: str
    event_type: str
    application: Application
    measurement: Measurement
    destination_ip: str
    additional_info: Optional[Dict[str, Any]] = None
    exception: Optional[ExceptionModel] = None
    source_file: Optional[str] = None
