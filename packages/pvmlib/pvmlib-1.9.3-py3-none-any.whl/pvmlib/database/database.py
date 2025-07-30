import abc
import os
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from pvmlib.logs import LoggerSingleton
from pymongo.errors import PyMongoError
from pvmlib.context import RequestContext

class Session:
    pass

class Database:
    """
    Abstract base class for database management.

    This class defines the interface for interacting with a database,
    specifically the `session` method, which should provide an asynchronous context manager
    for database sessions.
    """
    @abc.abstractmethod
    @asynccontextmanager
    async def session(self):
        """
        Provides an asynchronous context manager for a database session.

        This method should be implemented by subclasses to manage the lifecycle of a
        database session (e.g., starting and closing transactions).
        """
        yield None

class DatabaseManager(Database):
    """
    Manages connections to a MongoDB database using motor.

    This class is a singleton, ensuring only one instance exists per application.
    It handles connecting to and disconnecting from MongoDB, and provides an asynchronous context
    manager for database sessions, including support for transactions.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Ensures only one instance of DatabaseManager is created (singleton pattern).
        """
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """
        Initializes the DatabaseManager.

        If the manager has not been previously initialized, it sets up the MongoDB client,
        and obtains an instance of the application's logger.
        """
        if not hasattr(self, 'initialized'):
            self.mongo_client = None
            self.initialized = True
            self.log = LoggerSingleton().logger
            self.context = RequestContext()

    async def connect_to_mongo(self):
        """
        Establishes a connection to the MongoDB database.

        Reads connection parameters from environment variables (MONGO_URI, MONGO_TIMEOUT_MS,
        MONGO_MAX_POOL_SIZE, MONGO_DB_NAME) and creates an AsyncIOMotorClient.

        Raises:
            ValueError: If MONGO_URI or MONGO_DB_NAME are not set.
            Exception: For any other error during connection.
        """
        try:
            self.context.set_tracing_id("N/A")
            mongo_uri = os.getenv("MONGO_URI", "localhost:27017")
            mongo_timeout_ms = os.getenv("MONGO_TIMEOUT_MS", "5000")
            mongo_max_pool_size = os.getenv("MONGO_MAX_POOL_SIZE", "100")
            mongo_db_name = os.getenv("MONGO_DB_NAME")

            if not mongo_uri or not mongo_db_name:
                self.log.error(
                    "MONGO_URI and MONGO_DB_NAME must be set in environment variables",
                    log_type="SYSTEM",
                    event_type="CONFIG_ERROR",
                    status="ERROR",
                )
                raise ValueError(
                    "MONGO_URI and MONGO_DB_NAME must be set in environment variables"
                )

            self.mongo_client = AsyncIOMotorClient(
                mongo_uri,
                serverSelectionTimeoutMS=int(mongo_timeout_ms),
                maxPoolSize=int(mongo_max_pool_size),
            )
            self.mongo_database = self.mongo_client[mongo_db_name]
            self.log.info(f"Connected to MongoDB: {mongo_db_name}")

        except Exception as e:
            self.log.error(
                message=f"Error connecting to MongoDB: {e}",
                log_type="SYSTEM",
                event_type="DB_CONNECTION_ERROR",
                status="FAILED",
            )
            raise e

    async def disconnect_from_mongo(self):
        """
        Closes the connection to the MongoDB database.
        """
        if self.mongo_client:
            self.log.info("Disconnecting from MongoDB")
            self.mongo_client.close()
            self.log.info("Disconnected from MongoDB")

    @asynccontextmanager
    async def session(self):
        """
        Provides an asynchronous context manager for a MongoDB database session,
        including support for transactions.

        Yields:
            The MongoDB database object.
        """
        s = None
        try:
            s = await self.mongo_client.start_session()
            async with s.start_transaction():
                self.log.debug("Starting MongoDB transaction")
                yield self.mongo_database
                await s.commit_transaction()
                self.log.info("MongoDB transaction committed")
        except PyMongoError as e:
            if s:
                await s.abort_transaction()
                self.log.warning(
                    "MongoDB transaction aborted due to PyMongoError",
                    log_type="SYSTEM",
                    event_type="DB_TRANSACTION_ERROR",
                    status="FAILED",
                )
            raise
        except Exception as e:
            if s:
                await s.abort_transaction()
                self.log.error(
                    f"MongoDB transaction aborted due to unexpected error {str(e)}",
                    log_type="SYSTEM",
                    event_type="DB_TRANSACTION_ERROR",
                    status="FAILED",
                )
            raise
        finally:
            if s:
                s.close()
                self.log.debug("MongoDB session closed")

database_manager = DatabaseManager()