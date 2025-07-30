import os
import json
import functools
from fastapi import Request
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from urllib.parse import urlencode

class MsManager:
    """
    Utility class for managing microservice interactions.

    Provides static methods to simplify the process of making requests to other
    microservices within an application architecture.
    """
    @staticmethod
    def Forks(func):
        """
        A decorator that simply wraps a function.  (Intended for future use or extension).

        This decorator currently doesn't add any functionality.  It's a placeholder that
        could be expanded to add cross-cutting concerns, such as logging or authentication,
        to the decorated function.

        Args:
            func (Callable): The function to wrap.

        Returns:
            Callable: The wrapped function.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def Create(configs, ctx=[]):
        """
        A decorator that handles calling other microservices.

        This decorator simplifies the process of making requests to other microservices.
        It constructs the URL, makes the request, handles errors, and merges the response
        data.

        Args:
            configs (list): A list of dictionaries, where each dictionary describes a
                microservice call to be made.  Each dictionary should contain the following keys:
                - 'fork':  The name of the microservice.
                - 'action': The HTTP method to use (e.g., 'POST', 'GET').
                - 'fnc': The name of a function to process the response (optional).
                Additional optional keys may include 'Query'
            ctx (list, optional):  Unused, likely a placeholder. Defaults to [].

        Returns:
            Callable: A decorator that wraps the original function.  The wrapped function
                will make the microservice calls and merge the results before calling
                the original function.
        """
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(request: Request, data, *args, **kwargs):
                
                data = {}
                response = {}
                headers = {}

                for key, value in request.headers.items():
                    headers.pop("host", None)
                    headers.update({key: value})

                body_bytes = await request.body()
                if body_bytes:
                    body_json = json.loads(body_bytes)
                    data.update(body_json)
                
                if request.query_params:
                    data.update(request.query_params)

                async with ClientSession() as session:
                    for config in configs:
                        fork_conf = func.__globals__['confFork']().get(config['fork'])
                        if fork_conf:
                            app = fork_conf['App']
                            endpoint = fork_conf['EndPoint']
                            version = fork_conf['Version']
                            url_base = os.environ.get('URL_ENDPOINT_SERVICES', None)
                            url = f"{url_base}/{app}/api/{version}/{endpoint}"
                            query = fork_conf.get('Query', None)
                            
                            action_map = {
                                Actions.POST: lambda: session.post(url, json=data, headers=headers),
                                Actions.GET: lambda: session.get(format_query_params(data, query, url), headers=headers),
                                Actions.UPDATE: lambda: session.put(url, json=data, headers=headers),
                                Actions.DELETE: lambda: session.delete(url, headers=headers)
                            }
                            
                            action = action_map.get(config['action'])
                            if action is None:
                                continue

                            async with action() as response:
                                if response is None:
                                    continue

                                data_response = await response.json()

                                if response.status != 200:
                                    return JSONResponse(status_code=response.status, content=data_response)

                                fnc_name = config['fnc']
                                if fnc_name in func.__globals__:
                                    fnc = func.__globals__[fnc_name]
                                    data = fnc(data, data_response)
                                
                                data.update(data_response['data'])

                    return await func(request, data, *args, **kwargs)
            return wrapper
        return decorator

def format_query_params(data, keys, url):
    """
    Formats URL query parameters from a dictionary.

    Args:
        data (dict): A dictionary containing the parameters.
        keys (str): A comma-separated string of keys to extract from the data dictionary.
        url (str): The base URL to append the query parameters to.

    Returns:
        str: The URL with the formatted query parameters, or the original URL if no
            valid keys are found in the data dictionary.
    """
    query_params = []
    for key in keys.split(","):
        if key in data:
            query_params.append(f"{key}={data[key]}")
    
    if query_params:
        url += "?" + "&".join(query_params)
    return url
