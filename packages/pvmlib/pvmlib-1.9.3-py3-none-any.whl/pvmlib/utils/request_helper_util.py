from urllib.parse import urlencode

class RequestHelperUtil:
    @staticmethod
    def form_url_with_params(base_url: str, endpoint: str, params: dict) -> str:
        """
        Constructs a URL by combining a base URL, an endpoint, and URL parameters.

        Args:
            base_url (str): The base URL of the service.
            endpoint (str): The specific endpoint to access.
            params (dict): A dictionary containing the parameters to be included in the URL's query string.

        Returns:
            str: The complete URL with encoded parameters.

        Example:
            >>> RequestHelperUtil.form_url_with_params(
            ...     "https://example.com/api/", "users", {"page": 1, "per_page": 10}
            ... )
            'https://example.com/api/users?page=1&per_page=10'
        """
        query_string = urlencode(params)
        return f"{base_url}{endpoint}?{query_string}"