from typing import Optional
from datetime import datetime
from pvmlib.logs.models import Application, Measurement, DataLogger, ExceptionModel
from pvmlib.logs.utils import LogType
from pvmlib.context.request_context import RequestContext
from pvmlib.patterns.decorator import LogSanitizer
from time import time
from google.cloud.logging import Client
from google.cloud import logging as gcp_logging
import os
import logging
import socket
import sys
import inspect
import traceback
import uuid

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # Define a constant for the date format.

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_message = super().format(record)
        if hasattr(record, 'json_fields'):
            return f"{log_message} - Extra: {record.json_fields}"
        return log_message
    
class LogData:
    """
    A singleton class responsible for collecting and formatting log data.
    It gathers information about the application, environment, and the specific log event.
    """
    _instance = None  # Class variable to hold the single instance.

    def __new__(cls, *args, **kwargs):
        """
        Ensures only one instance of LogData exists (singleton pattern).
        Initializes the instance if it doesn't exist.
        """
        if cls._instance is None:
            cls._instance = super(LogData, cls).__new__(cls)  # Call the superclass's __new__ method.
            cls._instance.__initialize(*args, **kwargs)  # Initialize the instance.
        return cls._instance

    def __initialize(self, origin: str = "INTERNAL"):
        """
        Initializes the LogData instance with default values and environment information.

        Args:
            origin (str): The origin of the log event (e.g., "INTERNAL", "REQUEST"). Defaults to "INTERNAL".
        """
        self.schema_version = os.getenv("VERSION_LOG", "1.0.0")
        self.log_origin = origin 
        self.tracing_id = "N/A"
        self.hostname = socket.gethostname()
        self.appname = os.getenv("APP_NAME", "default_app")
        self.source_ip = socket.gethostbyname(self.hostname)
        self.destination_ip = "N/A"
        self.additional_info = {}
        self.app = Application(
            name=os.getenv("APP_NAME", "default"),
            version=os.getenv("API_VERSION", "default"),
            env=os.getenv("ENV", "default"),
            kind=os.getenv("APP_KIND", "default"))
        self.console_formatter = logging.Formatter(
            '%(levelname)s: %(asctime)s - %(message)s',
            datefmt=DATE_FORMAT)
        try:
            self.gcp_client = Client()
            self.gcp_logger = self.gcp_client.logger(f"{self.appname}-pvm")
            self.gcp_client.setup_logging()
        
        except Exception as e:
            print(f"Error initializing GCP Logging: {e}. Logging to GCP will be disabled.")
            self.gcp_client = None
            self.gcp_logger = None
            self.in_cluster = False

        self.logger = logging.getLogger(f"{self.appname}-pvm")
        self.log_sanitizer = LogSanitizer()
        self.initialized = True 
        ch = logging.StreamHandler(sys.stdout)
        formatter = JsonFormatter('%(levelname)s: %(asctime)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.setLevel(logging.INFO)

    def log_to_gcp(self, severity, log_entry):
        if self.gcp_logger:
            resource_labels = {
                "project_id": self.gcp_client.project,
                "pod_name": self.hostname,
                "container_name": f"{self.appname}-pvm"
            }
            resource = gcp_logging.Resource(
                type="k8s_container",
                labels=resource_labels
            )
            self.gcp_logger.log_struct(
                info=log_entry,
                severity=severity,
                resource=resource
            )

    def _format_exception_info(self) -> tuple[Optional[ExceptionModel], str]:
        """
        Formats exception information if an exception occurred.

        Returns:
            tuple[Optional[ExceptionModel], str]: A tuple containing the ExceptionModel (if an exception exists)
                                                and the source file where the exception occurred.
        """
        exception_model = None
        source_file = "N/A"
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type and exc_value and exc_traceback:
            exception_model = ExceptionModel(
                name=exc_type.__name__,
                message=str(exc_value),
                stackTrace=''.join(traceback.format_tb(exc_traceback))
            )
        tb = traceback.extract_tb(exc_traceback)
        if tb:
            source_file = tb[-1].filename
        return exception_model, source_file

    def _format_filename(self, full_path: str):
        """
        Extracts a cleaner, more readable filename from a full path.
        Tries to get the path relative to 'src' or 'site-packages' directories.

        Args:
            full_path (str): The full file path.

        Returns:
            str: A formatted filename.
        """
        parts = full_path.split(os.sep)
        try:
            start_index = 0
            if 'src' in full_path:
                start_index = parts.index("src")
            if 'site-packages' in full_path:
                start_index = parts.index("site-packages")
            filename_with_py = ".".join(parts[start_index:])
            filename_without_ext, _ = os.path.splitext(filename_with_py)
            return filename_without_ext.replace(os.sep, ".") + ".py"
        except ValueError:
            return full_path

    def log(
            self,
            level: int,
            message: str,
            log_type: str = LogType.INTERNAL,
            event_type: str = "EVENT",
            status: str = "INPROCESS",
            destination_ip: str = None,
            additional_info: Optional[dict] = None
    ) -> None:
        """
        Logs a message with the specified level and additional information.

        Args:
            level (int): The logging level (e.g., logging.INFO, logging.ERROR).
            message (str): The log message.
            log_type (str): The type of log (e.g., "INTERNAL", "REQUEST", "RESPONSE").
                          Defaults to "INTERNAL".
            event_type (str): A specific event type within the log type (e.g., "START", "END", "FAILURE").
                            Defaults to "EVENT".
            status (str): The status of the operation being logged (e.g., "INPROCESS", "SUCCESS", "FAILED").
                            Defaults to "INPROCESS".
            destination_ip (str, optional): The destination IP address if applicable. Defaults to None.
            additional_info (Optional[dict], optional): A dictionary containing extra information to include in the log.
                                                        Defaults to None.
        """
        context = RequestContext()

        if destination_ip is not None:
            self.destination_ip = destination_ip

        frame_info = inspect.stack()[2]
        method_name = frame_info.function 

        exception_model, source_file = self._format_exception_info()

        elapsed_time = time() - context.get_start_time() if context.get_start_time() else 0.00
        log_entry = DataLogger(
            level=logging.getLevelName(level),
            schema_version=self.schema_version,
            log_type=log_type,
            source_ip=self.source_ip,
            status=status,
            message=message,
            log_origin=self.log_origin,
            timestamp=datetime.now().strftime(DATE_FORMAT),
            tracing_id=context.get_tracing_id(),
            hostname=self.hostname,
            event_type=f"{log_type}_{event_type.upper()}",
            application=self.app,
            measurement=Measurement(
                method=method_name,
                elapsed_time=f"{elapsed_time:.2f}"
            ),
            destination_ip=self.destination_ip,
            additional_info=additional_info or self.additional_info,
            exception=exception_model,
            source_file=source_file
        )
        log_entry_json = self._format_log(log_entry)
        if self.gcp_client:
            self.logger.log(level, msg=log_entry.message, extra={"json_fields":log_entry_json})
            self.log_to_gcp(log_entry.level, log_entry=log_entry_json)
        else:
            self.logger.log(level, msg=log_entry.message, extra={"json_fields":log_entry_json})

    def _format_log(
            self,
            log_entry: DataLogger
    ):
        """
        Formats the log message for console and GCP Logging.

        Args:
            log_entry (DataLogger): The structured log data.
            filename (str): The source filename of the log call.
            method_name (str): The source method name of the log call.
            tracing_id (str): The current tracing ID.

        Returns:
            tuple[str, dict]: A tuple containing the formatted log message for console output and the payload
                            for Google Cloud Logging.
        """
        @self.log_sanitizer.sanitize_decorator
        def format_log_message(log_data: DataLogger) -> dict:
            """
            Formats the log message, potentially including the full DataLogger data.
            This function is decorated with the log sanitizer.

            Args:
                log_data: the log entry
            Returns:
                The formatted log message
            """
            return log_data.model_dump()

        log_sanitize = format_log_message(log_entry)

        gcp_log_payload = {
            "severity": log_entry.level,
            "message": log_entry.message,
            "timestamp": log_entry.timestamp,
            "jsonPayload": log_sanitize,
            "labels": {
                "app_name": log_entry.application.name,
                "environment": log_entry.application.env,
            }
        }
        return gcp_log_payload

    def info(self, *args, **kwargs):
        """Logs a message at the INFO level.

        Args:
            *args:  Positional arguments passed to the underlying log method.
            **kwargs: Keyword arguments passed to the underlying log method.
        """
        self.log(logging.INFO, *args, **kwargs)  # Call the log method with INFO level.

    def error(self, *args, **kwargs):
        """
        Logs a message at the ERROR level.

        Args:
            *args:  Positional arguments passed to the underlying log method.
            **kwargs: Keyword arguments passed to the underlying log method.
        """
        self.log(logging.ERROR, *args, **kwargs)

    def warning(self, *args, **kwargs):
        """
        Logs a message at the WARNING level.
        Args:
            *args:  Positional arguments passed to the underlying log method.
            **kwargs: Keyword arguments passed to the underlying log method.
        """
        self.log(logging.WARNING, *args, **kwargs)

    def debug(self, *args, **kwargs):
        """
        Logs a message at the DEBUG level.
        Args:
            *args:  Positional arguments passed to the underlying log method.
            **kwargs: Keyword arguments passed to the underlying log method.
        """
        self.log(logging.DEBUG, *args, **kwargs)

    def critical(self, *args, **kwargs):
        """
        Logs a message at the CRITICAL level.
        Args:
            *args:  Positional arguments passed to the underlying log method.
            **kwargs: Keyword arguments passed to the underlying log method.
        """
        self.log(logging.CRITICAL, *args, **kwargs) 

class LoggerSingleton:
    """
    A singleton class that provides a single instance of the LogData class.
    This ensures that all logging within the application uses the same configuration.
    """
    _instance = None  # Class variable to hold the single instance.

    def __new__(cls, *args, **kwargs):
        """
        Ensures only one instance of LoggerSingleton exists.
        Initializes the LogData instance within it if it doesn't exist.
        Assigns a unique ID to the logger instance.
        """
        if cls._instance is None:
            cls._instance = super(LoggerSingleton, cls).__new__(cls)
            cls._instance.__initialize(*args, **kwargs) 
            cls._instance._id = str(uuid.uuid4())
        return cls._instance

    def __initialize(self):
        """Initializes the LogData instance."""
        self.logger = LogData()

    def get_instance_id(self):
        """Returns the unique ID of this logger instance."""
        return self._id