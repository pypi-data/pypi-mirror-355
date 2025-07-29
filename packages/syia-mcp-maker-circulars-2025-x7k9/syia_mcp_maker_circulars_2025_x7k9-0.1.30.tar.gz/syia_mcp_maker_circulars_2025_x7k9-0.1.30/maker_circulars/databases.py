import typesense
from motor.motor_asyncio import AsyncIOMotorClient

from .constants import *

from maker_circulars import logger


class MongoDBClient:
    '''
    An async client for the MongoDB database using Motor (AsyncIOMotorClient).
    '''
    def __init__(self):
        try:
            self.client = AsyncIOMotorClient(MONGODB_URI)
            self.db = self.client[MONGODB_DB_NAME]
            self.enabled = True
        except Exception as e:
            logger.warning("MongoDB client initialization failed: %s", e)
            self.enabled = False

        logger.info("MongoDB client initialized with database %s", MONGODB_DB_NAME)


    

class TypesenseClient:
    '''
    A client for the Typesense search engine.
    '''
    def __init__(self):
        try:
            self.client = typesense.Client({
                'api_key': TYPESENSE_API_KEY,
                'nodes': [{
                    'host': TYPESENSE_HOST,
                    'port': TYPESENSE_PORT,
                    'protocol': TYPESENSE_PROTOCOL
                }],
                'connection_timeout_seconds': 2
            })
            
            self.enabled = True

        except Exception as e:
            logger.warning("Typesense client initialization failed: %s", e)
            self.enabled = False

        logger.info("Typesense client initialized")
        
    @property
    def collections(self):
        return self.client.collections
    


__all__ = ["MongoDBClient", "TypesenseClient"]