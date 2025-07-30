import threading

class RequestContext:
    """
    A thread-safe singleton class for managing request-specific context.

    This class provides a way to store and access information related to a single
    request, such as tracing IDs, user information, and request timing.  It uses a
    threading.Lock to ensure thread safety, as web applications often handle
    multiple requests concurrently.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Ensures only one instance of RequestContext exists (thread-safe singleton).
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(RequestContext, cls).__new__(cls)
                    cls._instance.reset()  # Initialize the instance
        return cls._instance

    def reset(self):
        """
        Resets all context variables to their default values.

        This method clears the stored information for a request, preparing the
        context for a new request.  It should be called at the beginning of each
        request lifecycle.
        """
        self.start_time = None
        self.tracing_id = None
        self.user_id = None
        self.session_id = None
        self.client_ip = None
        self.user_agent = None
        self.request_path = None

    def set_start_time(self, start_time):
        """
        Sets the start time of the request.

        Args:
            start_time: The time when the request started.
        """
        self.start_time = start_time

    def get_start_time(self):
        """
        Gets the start time of the request.

        Returns:
            The start time of the request.
        """
        return self.start_time

    def set_tracing_id(self, tracing_id):
        """
        Sets the tracing ID for the request.

        Args:
            tracing_id: The unique ID for tracing the request.
        """
        self.tracing_id = tracing_id

    def get_tracing_id(self):
        """
        Gets the tracing ID for the request.

        Returns:
            The tracing ID for the request.
        """
        return self.tracing_id

    def set_user_id(self, user_id):
        """
        Sets the user ID associated with the request.

        Args:
            user_id: The ID of the user making the request.
        """
        self.user_id = user_id

    def get_user_id(self):
        """
        Gets the user ID associated with the request.

        Returns:
            The ID of the user making the request.
        """
        return self.user_id

    def set_session_id(self, session_id):
        """
        Sets the session ID for the request.

        Args:
            session_id: The ID of the user's session.
        """
        self.session_id = session_id

    def get_session_id(self):
        """
        Gets the session ID for the request.

        Returns:
            The ID of the user's session.
        """
        return self.session_id

    def set_client_ip(self, client_ip):
        """
        Sets the client IP address of the request.

        Args:
            client_ip: The IP address of the client making the request.
        """
        self.client_ip = client_ip

    def get_client_ip(self):
        """
        Gets the client IP address of the request.

        Returns:
            The IP address of the client making the request.
        """
        return self.client_ip

    def set_user_agent(self, user_agent):
        """
        Sets the user agent string of the request.

        Args:
            user_agent: The user agent string from the request headers.
        """
        self.user_agent = user_agent

    def get_user_agent(self):
        """
        Gets the user agent string of the request.

        Returns:
            The user agent string from the request headers.
        """
        return self.user_agent

    def set_request_path(self, request_path):
        """
        Sets the path of the requested URL.

        Args:
            request_path: The path part of the URL.
        """
        self.request_path = request_path

    def get_request_path(self):
        """
        Gets the path of the requested URL.

        Returns:
            The path part of the URL.
        """
        return self.request_path
