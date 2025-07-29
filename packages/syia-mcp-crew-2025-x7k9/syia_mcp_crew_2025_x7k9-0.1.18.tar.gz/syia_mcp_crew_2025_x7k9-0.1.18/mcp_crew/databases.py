import uuid
from typing import List, Dict, Any, Optional, TypedDict, Union
import typesense
from pymongo import MongoClient
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient

from .constants import *

from . import logger


import sys
import argparse
import os
import json


parser = argparse.ArgumentParser(description="Run MCP services")
parser.add_argument(
    "mode",
    choices=["server", "scheduler", "both"],
    default="server",
    nargs="?",
    help="Select which component to run"
)

# Step 2: Parse known args
args, remaining_args = parser.parse_known_args()

sys.argv = [sys.argv[0]] + remaining_args

# Step 4: Dispatch
if args.mode == "scheduler":
    CONFIG_PATH = os.path.join(os.path.dirname(__file__),"Agent","config", "mcp_servers_config.json")
    config_dict = json.load(open(CONFIG_PATH, 'r'))
    for key, value in config_dict.items():
        globals()[key] = value  #



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