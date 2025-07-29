import sys
from bson import ObjectId 
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.operations import IndexModel
from stage0_py_utils.config.config import Config

import logging
logger = logging.getLogger(__name__)

# TODO: - Refactor to use connection pooling

class MongoIO:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MongoIO, cls).__new__(cls, *args, **kwargs)
            
            
            # TODO: Add timeout configs to Client and use here in client constructor
            config = Config.get_instance()
            client = MongoClient(
                config.MONGO_CONNECTION_STRING, 
                serverSelectionTimeoutMS=2000, 
                socketTimeoutMS=5000
            )
            client.admin.command('ping')  # Force connection

            cls._instance.config = config
            cls._instance.client = client
            cls._instance.db = client.get_database(config.MONGO_DB_NAME)
            cls._instance.connected = True
            logger.info(f"Connected to MongoDB")
        return cls._instance

    def disconnect(self):
        """Disconnect from MongoDB."""
        if not self.connected: raise Exception("disconnect when mongo not connected")
            
        try:
            if self.client:
                self.client.close()
                logger.info("Disconnected from MongoDB")
        except Exception as e:
            logger.fatal(f"Failed to disconnect from MongoDB: {e} - exiting")
            sys.exit(1) # fail fast 

    def get_collection(self, collection_name):
        """Get a collection, creating it if it doesn't exist.
        
        Args:
            collection_name (str): Name of the collection to get/create
            
        Returns:
            Collection: The MongoDB collection object
        """
        if not self.connected: raise Exception("get_collection when Mongo Not Connected")
        
        try:
            # Check if collection exists
            if collection_name not in self.db.list_collection_names():
                # Create collection if it doesn't exist
                self.db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            
            return self.db.get_collection(collection_name)
        except Exception as e:
            logger.error(f"Failed to get/create collection: {collection_name} {e}")
            raise

    def drop_collection(self, collection_name):
        """Drop a collection from the database.
        
        Args:
            collection_name (str): Name of the collection to drop
            
        Returns:
            bool: True if collection was dropped, False if it didn't exist
        """
        if not self.connected: raise Exception("drop_collection when Mongo Not Connected")

        try:
            if collection_name in self.db.list_collection_names():
                self.db.drop_collection(collection_name)
                logger.info(f"Dropped collection: {collection_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to drop collection: {e}")
            raise
      
    def get_documents(self, collection_name, match=None, project=None, sort_by=None):
        """
        Retrieve a list of documents based on a match, projection, and optional sorting.

        Args:
            collection_name (str): Name of the collection to query.
            match (dict, optional): MongoDB match filter. Defaults to {}.
            project (dict, optional): Fields to include or exclude. Defaults to None.
            sort_by (list of tuple, optional): Sorting criteria (e.g., [('field1', ASCENDING), ('field2', DESCENDING)]). Defaults to None.

        Returns:
            list: List of documents matching the query.
        """
        if not self.connected: raise Exception("get_documents when Mongo Not Connected")

        # Default match and projection
        match = match or {}
        project = project or None
        sort_by = sort_by or None
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.find(match, project)
            if sort_by: cursor = cursor.sort(sort_by)

            documents = list(cursor)
            return documents
        except Exception as e:
            logger.error(f"Failed to get documents from collection '{collection_name}': {e}")
            raise
                
    def update_document(self, collection_name, document_id=None, match=None, set_data=None, push_data=None, add_to_set_data=None, pull_data=None):
        """
        Update a document in the specified collection with optional set, push, add_to_set, and pull operations.

        Args:
            collection_name (str): Name of the collection to update.
            document_id (str): ID of the document to update.
            set_data (dict, optional): Fields to update or set. Defaults to None.
            push_data (dict, optional): Fields to push items into arrays. Defaults to None.
            add_to_set_data (dict, optional): Fields to add unique items to arrays. Defaults to None.
            pull_data (dict, optional): Fields to remove items from arrays. Defaults to None.

        Returns:
            dict: The updated document if successful, otherwise None.
        """
        if not self.connected: raise Exception("update_document when Mongo Not Connected")

        try:
            document_collection = self.get_collection(collection_name)

            if match is None: 
                document_object_id = ObjectId(document_id)
                match = {"_id": document_object_id}

            # Build the update pipeline
            pipeline = {}
            if set_data:
                pipeline["$set"] = set_data
            if push_data:
                pipeline["$push"] = push_data
            if add_to_set_data:
                pipeline["$addToSet"] = add_to_set_data
            if pull_data:
                pipeline["$pull"] = pull_data

            updated = document_collection.find_one_and_update(match, pipeline, return_document=True)

        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            raise

        return updated

    def get_document(self, collection_name, document_id):
        """Retrieve a document by ID."""
        if not self.connected: raise Exception("get_document when Mongo Not Connected")

        try:
            # Get the document
            collection = self.get_collection(collection_name)
            document_object_id = ObjectId(document_id)
            document = collection.find_one({"_id": document_object_id})
            return document
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            raise

    def create_document(self, collection_name, document):
        """Create a curriculum by ID."""
        if not self.connected: raise Exception("create_document when Mongo Not Connected")
        
        try:
            document_collection = self.get_collection(collection_name)
            result = document_collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise   

    def delete_document(self, collection_name, document_id):
        """Delete a single document by ID.
        
        Args:
            collection_name (str): Name of the collection
            document_id (str): ID of the document to delete
            
        Returns:
            int: Number of documents deleted (0 or 1)
        """
        if not self.connected: raise Exception("delete_document when Mongo Not Connected")

        try:
            document_collection = self.get_collection(collection_name)
            document_object_id = ObjectId(document_id)
            result = document_collection.delete_one({"_id": document_object_id})
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise 
        
        return result.deleted_count

    def delete_documents(self, collection_name, match):
        """Delete multiple documents matching the criteria.
        
        Args:
            collection_name (str): Name of the collection
            match (dict): Match criteria to delete matching documents
            
        Returns:
            int: Number of documents deleted
        """
        if not self.connected: raise Exception("delete_documents when Mongo Not Connected")

        try:
            document_collection = self.get_collection(collection_name)
            result = document_collection.delete_many(match)
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise 
        
        return result.deleted_count

    def upsert_document(self, collection_name, match, data):
        """Upsert a document - create if not exists, update if exists.
        
        Args:
            collection_name (str): Name of the collection
            match (dict): Match criteria to find existing document
            data (dict): Data to insert or update
            
        Returns:
            dict: The upserted document
        """
        if not self.connected: raise Exception("upsert_document when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one_and_update(
                match,
                {"$set": data},
                upsert=True,
                return_document=True
            )
            return result
        except Exception as e:
            logger.error(f"Failed to upsert document: {e}")
            raise

    def apply_schema(self, collection_name, schema):
        """Apply schema validation to a collection.
        
        Args:
            collection_name (str): Name of the collection
            schema (dict): MongoDB JSON Schema validation rules
        """
        if not self.connected: raise Exception("apply_schema when Mongo Not Connected")
        
        try:
            # Get collection (creates if doesn't exist)
            self.get_collection(collection_name)
            
            command = {
                "collMod": collection_name,
                "validator": {"$jsonSchema": schema}
            }
            
            result = self.db.command(command)
            logger.info(f"Schema validation applied successfully: {collection_name} {result}")
        except Exception as e:
            logger.error(f"Failed to apply schema validation: {collection_name} {e} {schema}")
            raise

    def get_schema(self, collection_name):
        """Get the current schema validation rules for a collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            dict: The current schema validation rules
        """
        if not self.connected: raise Exception("get_schema when Mongo Not Connected")
        
        try:
            # Get collection (creates if doesn't exist)
            collection = self.get_collection(collection_name)
            options = collection.options()
            validation_rules = options.get("validator", {})
            
            return validation_rules
        except Exception as e:
            logger.error(f"Failed to get schema validation: {collection_name} {e}")
            raise

    def remove_schema(self, collection_name):
        """Remove schema validation from a collection.
        
        Args:
            collection_name (str): Name of the collection
        """
        if not self.connected: raise Exception("remove_schema when Mongo Not Connected")
        
        try:
            # Get collection (creates if doesn't exist)
            self.get_collection(collection_name)
            
            command = {
                "collMod": collection_name,
                "validator": {}
            }
            
            result = self.db.command(command)
            logger.info(f"Schema validation cleared successfully: {result}")
        except Exception as e:
            logger.error(f"Failed to clear schema validation: {e}")
            raise

    def create_index(self, collection_name, indexes):
        """Create indexes on a collection.
        
        Args:
            collection_name (str): Name of the collection
            indexes (list): List of index specifications, each containing 'name' and 'key' fields
        """
        if not self.connected: raise Exception("create_index when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            index_models = [IndexModel(index["key"], name=index["name"]) for index in indexes]
            collection.create_indexes(index_models)
            logger.info(f"Created {len(indexes)} indexes")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise

    def drop_index(self, collection_name, index_name):
        """Drop an index from a collection.
        
        Args:
            collection_name (str): Name of the collection
            index_name (str): Name of the index to drop
        """
        if not self.connected: raise Exception("drop_index when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            collection.drop_index(index_name)
            logger.info(f"Dropped index {index_name} from collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to drop index: {e}")
            raise

    def get_indexes(self, collection_name):
        """Get all indexes for a collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            list: List of index configurations
        """
        if not self.connected: raise Exception("get_indexes when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            return list(collection.list_indexes())
        except Exception as e:
            logger.error(f"Failed to get indexes: {e}")
            raise

    def execute_pipeline(self, collection_name, pipeline):
        """Execute a MongoDB aggregation pipeline.
        
        Args:
            collection_name (str): Name of the collection
            pipeline (list): List of pipeline stages to execute
        """
        if not self.connected: raise Exception("execute_pipeline when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            result = list(collection.aggregate(pipeline))
            logger.info(f"Executed pipeline on collection: {collection_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to execute pipeline: {e}")
            raise
    
    # Singleton Getter
    @staticmethod
    def get_instance():
        """Get the singleton instance of the MongoIO class."""
        if MongoIO._instance is None:
            MongoIO()
        return MongoIO._instance
