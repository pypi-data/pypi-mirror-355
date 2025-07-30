from typing import Optional, Callable, Dict, Pattern
import re
import json

class LogSanitizer:
    """
    Class for sanitizing sensitive information in logs.

    Provides methods to mask potentially sensitive information in log strings,
    including emails, phone numbers, credit card numbers, and other identifiable data.
    """

    def __init__(self, patterns: Optional[Dict[str, Pattern]] = None):
        """
        Initializes the LogSanitizer with sensitive information patterns.

        Args:
            patterns (Optional[Dict[str, Pattern]]): An optional dictionary of pre-compiled
                regular expression patterns. If not provided, default patterns will be used.
        """
        if patterns:
            self.sensitive_patterns = patterns
        else:
            self.sensitive_patterns = {
            "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"),
            "phone_mx": re.compile(r"\b(?:\d{3}[-.\s]?)?\d{3}[-.\s]?\d{4}\b"), # Ejemplo para teléfono MX
            "credit_card": re.compile(r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b"),
            "digits10": re.compile(r"\b\d{10}\b"),
            "generic": re.compile(r"(?i)password|auth|token|credit_card|ssn|secret|key"),
            "nss_mx": re.compile(r"\b\d{11}\b"),
            "curp_mx": re.compile(r"^[A-Z]{4}\d{6}[HM][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[A-Z\d]\d$"),
            "bank_account_clabe_mx": re.compile(r"\b\d{18}\b"),
        }
            
    def _mask_string(self, text: str, pattern: Pattern) -> str:
        """
        Masks occurrences of a regular expression pattern in a string.

        Args:
            text (str): The string in which to find occurrences.
            pattern (Pattern): The pre-compiled regular expression pattern to use.

        Returns:
            str: The string with the masked occurrences.
        """
        def _mask_half(match: re.Match) -> str:
            """
            Internal function to mask half of a matched string.

            Args:
                match (re.Match): The matched object.

            Returns:
                str: The masked string.
            """
            match_str = match.group(0)
            half_length = len(match_str) // 2
            return match_str[:half_length] + "****"

        return pattern.sub(_mask_half, text)

    def sanitize_log_message(self, log_message: str) -> str:
        """
        Sanitizes a log message string, masking sensitive information.

        Args:
            log_message (str): The log message string to sanitize.

        Returns:
            str: The sanitized log message string.
        """
        for pattern in self.sensitive_patterns.values():
            log_message = self._mask_string(log_message, pattern)
        return log_message

    def sanitize_json_log_message(self, log_json: str) -> str:
        """
        Sanitizes a string containing a log message in JSON format.

        Args:
            log_json (str): The JSON string to sanitize.

        Returns:
            str: The sanitized JSON string.
        """
        try:
            log_data = json.loads(log_json)
            sanitized_data = {
                key: self.sanitize_log_message(str(value))
                for key, value in log_data.items()
            }
            return json.dumps(sanitized_data)
        except json.JSONDecodeError:
            return log_json

    def sanitize_decorator(self, func: Callable) -> Callable:
        """
        Decorator to apply log sanitization to the result of a function.

        This decorator attempts to parse the function's result as JSON and, if successful,
        sanitizes the values within the JSON. If JSON parsing fails, it sanitizes the
        result as plain text.

        Args:
            func (Callable): The function to decorate.

        Returns:
            Callable: The wrapped function.
        """
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, str):
                try:
                    json.loads(result)
                    result = self.sanitize_json_log_message(result)
                except json.JSONDecodeError:
                    result = self.sanitize_log_message(result)
            return result
        return wrapper