"""Redis Database implementation."""

from typing import Any, Dict, Mapping, Type

import pymongo

# import redis.commands.search.aggregation as aggregations
# import redis.commands.search.reducers as reducers
import pymongo.database

# from redis.commands.search.query import Query
from flxtrtwn_objectdb.database import Database, DatabaseItem, T, UnknownEntityError


class MongoDBDatabase(Database):
    """MongoDB database implementation."""

    def __init__(self, mongodb_client: pymongo.MongoClient, name: str) -> None:
        self.connection: pymongo.MongoClient[Mapping[str, dict[str, Any]]] = mongodb_client
        self.database: pymongo.database.Database[Mapping[str, dict[str, Any]]] = self.connection[name]

    def update(self, item: DatabaseItem) -> None:
        """Update data."""
        item_type = type(item)
        item.model_validate(item)
        self.database[item_type.__name__].update_one(
            filter={"identifier": item.identifier}, update={"$set": item.model_dump()}, upsert=True
        )

    def get(self, schema: Type[T], identifier: str) -> T:
        collection = self.database[schema.__name__]
        if res := collection.find_one(filter={"identifier": identifier}):
            return schema(**res)
        raise UnknownEntityError(f"Unknown identifier: {identifier}")

    def get_all(self, schema: Type[T]) -> Dict[str, T]:
        raise NotImplementedError
