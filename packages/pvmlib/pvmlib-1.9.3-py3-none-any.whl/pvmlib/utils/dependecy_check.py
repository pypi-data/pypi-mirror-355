from typing import List, Dict, Callable
from fastapi import HTTPException
from pvmlib.database import database_manager
from aiohttp import ClientSession
from urllib.parse import urlparse

class DependencyChecker:
    """
    A class for checking the status of various dependencies required by the application.

    This class allows you to define a list of functions, each responsible for checking
    a specific dependency (e.g., database connection, external service availability).
    It then provides a method to execute these checks and return a dictionary of results.
    """
    def __init__(self, dependencies: List[Callable[[], Dict[str, str]]]):
        """
        Initializes the DependencyChecker with a list of dependency check functions.

        Args:
            dependencies (List[Callable[[], Dict[str, str]]]): A list of functions, where each function
                takes no arguments and returns a dictionary with a single key-value pair.
                The key represents the dependency name (e.g., "mongodb", "external_api")
                and the value is a string indicating its status ("UP" or "DOWN").
        """
        self.dependencies = dependencies

    async def check_dependencies(self) -> Dict[str, str]:
        """
        Executes all dependency checks and returns a dictionary of their statuses.

        This method iterates through the list of dependency check functions, executes
        each one, and aggregates the results into a single dictionary.  If any check
        raises an exception, it raises an HTTPException with a 500 status code.

        Returns:
            Dict[str, str]: A dictionary containing the status of each dependency,
                where the key is the dependency name and the value is its status ("UP" or "DOWN").

        Raises:
            HTTPException: If any dependency check function raises an exception.
        """
        results = {}
        for check in self.dependencies:
            try:
                result = await check()
                results.update(result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Dependency check failed: {str(e)}")
        return results

async def check_mongo() -> Dict[str, str]:
    """
    Checks the status of the MongoDB connection.

    This function attempts to ping the MongoDB server using the provided DatabaseManager.

    Args:
        database_manager (DatabaseManager): An instance of the DatabaseManager, which provides
            the connection to MongoDB.

    Returns:
        Dict[str, str]: A dictionary with the key "mongodb" and the value "UP" if the ping is
            successful, or "DOWN" if it fails.
    """
    try:
        # Verificar si ya hay una conexión existente
        if not database_manager.mongo_client:
            await database_manager.connect_to_mongo()
        
        await database_manager.mongo_database.command("ping")
        return {"mongodb": "UP"}
    except Exception as e:
        return {"mongodb": "DOWN"}

async def check_external_service(url: str) -> Dict[str, str]:
    """
    Checks the status of an external service by making an HTTP GET request.

    This function makes an asynchronous GET request to the specified URL and determines
    the service status based on the response status code.

    Args:
        url (str): The URL of the external service to check.

    Returns:
        Dict[str, str]: A dictionary with the service name (derived from the URL) as the key
            and "UP" if the response status code is 200, or "DOWN" otherwise.
    """
    try:
        async with ClientSession() as session:
            async with session.get(url) as response:
                parsed_url = urlparse(url)
                service_name = f"{parsed_url.hostname}{parsed_url.path.rsplit('/', 1)[0]}"
                if response.status == 200:
                    return {service_name: "UP"}
                else:
                    return {service_name: "DOWN"}
    except Exception as e:
        parsed_url = urlparse(url)
        service_name = f"{parsed_url.hostname}{parsed_url.path.rsplit('/', 1)[0]}"
        return {service_name: "DOWN"}