import json
from erioon.collection import Collection

class Database:
    def __init__(self, user_id, metadata, database=None, cluster=None):
        self.user_id = user_id
        self.metadata = metadata
        self.db_id = metadata.get("database_info", {}).get("_id")
        self.database = database
        self.cluster = cluster

    def __getitem__(self, collection_id):
        try:
            collections = self.metadata.get("database_info", {}).get("collections", {})
            coll_meta = collections.get(collection_id)

            if not coll_meta:
                return "No collection found"

            return Collection(
                user_id=self.user_id,
                db_id=self.db_id,
                coll_id=collection_id,
                metadata=coll_meta,
                database = self.database, 
                cluster = self.cluster
            )
        except Exception:
            return "Connection error"

    def __str__(self):
        return json.dumps(self.metadata, indent=4)

    def __repr__(self):
        return f"<Database db_id={self.db_id}, cluster={self.cluster}, database={self.database}>"

