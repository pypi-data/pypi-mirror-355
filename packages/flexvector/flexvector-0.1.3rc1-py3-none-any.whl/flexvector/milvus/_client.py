import hashlib
import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from typing import List, Dict, Any, Union

from flexvector.config import VectorDBSettings
from flexvector.core import VectorDBClient, Document
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_milvus import Milvus
from langchain_openai import OpenAIEmbeddings
from loguru import logger
from pymilvus import connections, utility, CollectionSchema, FieldSchema, DataType
from tqdm import tqdm


class MilvusFlexClient(VectorDBClient):
    __slots__ = (
        "_milvus_client",
        "_embeddings",
        "logger",
        "config",
    )

    def __init__(self, config: VectorDBSettings):
        self.logger = logger.bind(context="MilvusFlexClient")
        self.config = config

        if not config.MILVUS_URI:
            raise ValueError("MILVUS_URI must be provided in the configuration.")

        connections.connect(uri=config.MILVUS_URI)
        self.logger.info(f"Successfully connected to Milvus instance at {config.MILVUS_URI}")

        if config.OPENAI_API_KEY:
            self._embeddings = OpenAIEmbeddings(
                api_key=config.OPENAI_API_KEY,
                dimensions=config.EMBEDDING_DIMENSION,
                chunk_size=3096, # TODO: Check if this is optimal for Milvus
                show_progress_bar=True,
                model=config.EMBEDDING_MODEL
            )
            self.logger.debug(f"Using embedding model {config.EMBEDDING_MODEL}")
        else:
            self.logger.info("No OpenAI API key provided, Will use FastEmbed embeddings")
            self._embeddings = FastEmbedEmbeddings(
                model_name=config.FAST_EMBEDDING_MODEL,
                max_length=512
            )
            self.config.EMBEDDING_DIMENSION = 512

    def _get_or_create_collection(self, collection_name: str, **kwargs):
        if not utility.has_collection(collection_name):
            self.logger.info(f"Collection {collection_name} does not exist. Creating...")
            # TODO: Make schema more configurable, especially primary key and vector field names
            pk_field = FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True)
            text_field = FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535) # Max length for VARCHAR
            vector_field = FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.config.EMBEDDING_DIMENSION)
            metadata_field = FieldSchema(name="metadata", dtype=DataType.JSON)

            schema = CollectionSchema(
                fields=[pk_field, text_field, vector_field, metadata_field],
                description=f"Collection for {collection_name}",
                enable_dynamic_field=kwargs.get("enable_dynamic_field", True)
            )
            utility.create_collection(collection_name, schema=schema)
            self.logger.info(f"Collection {collection_name} created successfully.")

            # TODO: Make index params configurable
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT", # Basic index type
                "params": {"nlist": 128},
            }
            utility.create_index(collection_name, field_name="vector", index_params=index_params)
            self.logger.info(f"Index created for field 'vector' in collection {collection_name}.")
        else:
            self.logger.debug(f"Collection {collection_name} already exists.")

        utility.load_collection(collection_name)


    def load(self, collection_name: str, **kwargs) -> list[Document]:
        self.logger.debug(f"Loading to collection {collection_name} given kwargs: {kwargs.keys()}")
        self._get_or_create_collection(collection_name)

        path = kwargs.get("path")
        data = kwargs.get("data")
        uri = kwargs.get("uri")

        vectorstore = Milvus(
            embedding_function=self._embeddings,
            collection_name=collection_name,
            connection_args={"uri": self.config.MILVUS_URI},
            auto_id=True, # Let Milvus handle ID generation
            primary_field_name="pk", # As defined in schema
            text_field_name="text", # As defined in schema
            vector_field_name="vector", # As defined in schema
        )

        if path:
            return self._load_from_path(vectorstore, path)
        elif data:
            return self._load_from_data(vectorstore, data)
        elif uri:
            return self._load_from_uri(vectorstore, uri)
        else:
            raise ValueError("You MUST provide either path, data, or uri to load data")

    def from_langchain(self, collection_name: str, documents: List[Document], **kwargs) -> list[Document]:
        self.logger.debug(f"Loading {len(documents)} langchain documents into collection {collection_name}...")
        self._get_or_create_collection(collection_name, **kwargs)

        vectorstore = Milvus(
            embedding_function=self._embeddings,
            collection_name=collection_name,
            connection_args={"uri": self.config.MILVUS_URI},
            auto_id=True,
            primary_field_name="pk",
            text_field_name="text",
            vector_field_name="vector",
        )
        processed_documents = []
        for doc in documents:
            new_metadata = {}
            if doc.metadata:
                for k, v in doc.metadata.items():
                    # Milvus metadata should be a dict; complex values (dicts/lists) should be JSON serialized
                    # for the JSON field
                    if isinstance(v, (dict, list)):
                        new_metadata[k] = json.dumps(v)
                    else:
                        new_metadata[k] = v
            processed_documents.append(Document(page_content=doc.page_content, metadata=new_metadata))

        ids = vectorstore.add_documents(processed_documents)
        self.logger.info(f"Loaded {len(ids)} documents into collection {collection_name}.")
        return documents


    def search(self, collection_name: str, query: str, top_k: int = 3, **kwargs) -> List[Document]:
        self.logger.debug(f"Searching collection {collection_name} with query: {query[:25]}...")
        self.logger.debug(f"Given kwargs: {kwargs}")

        if not utility.has_collection(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist. Returning empty list.")
            return []

        utility.load_collection(collection_name) # Ensure collection is loaded

        search_type = kwargs.get("search_type", "similarity")
        filters = kwargs.get("filters", None) # Milvus expects an `expr` string for filtering

        # Other search parameters like `consistency_level`, `metric_type`, `offset`,
        # and `search_params` (e.g., {"nprobe": 10} for IVF_FLAT) can be passed via kwargs
        # if supported by the Langchain Milvus retriever's `search_kwargs`.

        vectorstore = Milvus(
            embedding_function=self._embeddings,
            collection_name=collection_name,
            connection_args={"uri": self.config.MILVUS_URI},
            auto_id=True,
            primary_field_name="pk",
            text_field_name="text",
            vector_field_name="vector",
        )

        retriever_kwargs = {"k": top_k}
        if filters:
             # Langchain's Milvus retriever uses `filter` in `search_kwargs` to pass the `expr` string.
            retriever_kwargs["search_kwargs"] = {'expr': filters}

        retriever = vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=retriever_kwargs
        )
        docs = retriever.invoke(query)
        self.logger.debug(f"Found {len(docs)} documents for query {query[:25]}...")
        return docs

    def remove_collection(self, collection_name: str) -> None:
        self.logger.debug(f"Removing collection {collection_name}...")
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            self.logger.info(f"Collection {collection_name} removed.")
        else:
            self.logger.info(f"Collection {collection_name} does not exist.")

    def delete(self, collection_name: str, ids: List[str]) -> None:
        if not ids:
            self.logger.info("No IDs provided for deletion.")
            return

        self.logger.debug(f"Deleting {len(ids)} documents from collection {collection_name}...")
        if not utility.has_collection(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist. Cannot delete documents.")
            return

        # Langchain's Milvus `delete` method expects a list of primary key values.
        # Our schema uses auto_id=True with 'pk' as the INT64 primary field.
        # The caller must provide these specific Milvus-generated integer PKs for deletion.
        vectorstore = Milvus(
            embedding_function=self._embeddings, # Not strictly needed for delete, but part of constructor
            collection_name=collection_name,
            connection_args={"uri": self.config.MILVUS_URI},
            auto_id=True,
            primary_field_name="pk", # Matches schema
            text_field_name="text",   # Matches schema
            vector_field_name="vector", # Matches schema
        )
        try:
            vectorstore.delete(ids)
            self.logger.info(f"Attempted to delete {len(ids)} documents from collection {collection_name}.")
        except Exception as e:
            self.logger.error(f"Error deleting documents from {collection_name}: {e}")
            raise

    def exists(self, collection_name: str) -> bool:
        self.logger.debug(f"Checking if collection {collection_name} exists...")
        exists = utility.has_collection(collection_name)
        self.logger.info(f"Collection {collection_name} exists: {exists}")
        return exists

    def get_info(self):
        db_info = {"uri": self.config.MILVUS_URI, "collections": []}
        try:
            collection_names = utility.list_collections()
            db_info["collections_count"] = len(collection_names)
            for name in collection_names:
                collection_info = utility.describe_collection(name)
                num_entities = utility.get_query_segment_info(name)[0].num_rows # More reliable way to get count
                db_info["collections"].append({
                    "name": name,
                    "schema": collection_info.to_dict(),
                    "count": num_entities,
                })
        except Exception as e:
            self.logger.error(f"Could not retrieve Milvus info: {e}")
        return db_info

    @property
    def client(self) -> Milvus: # Should return the Langchain Milvus client instance
        # This property might need to be collection-specific if the Langchain client is always tied to one
        # For now, returning a generic one, but it's not ideal as collection_name is needed.
        # Consider if this property is truly generic or should be removed/rethought.
        self.logger.warning("The 'client' property for MilvusFlexClient returns a generic Langchain Milvus instance "
                            "without a pre-defined collection. Instantiate with a collection name for specific operations.")
        return Milvus(
            embedding_function=self._embeddings,
            collection_name="default_collection", # Placeholder
            connection_args={"uri": self.config.MILVUS_URI},
            auto_id=True,
            primary_field_name="pk",
            text_field_name="text",
            vector_field_name="vector",
        )

    @property
    def langchain(self) -> Milvus:
         return self.client # Or raise NotImplementedError if it should be more specific

    @property
    def llama_index(self):
        # Placeholder for LlamaIndex integration if needed in the future
        # try:
        #     from llama_index.vector_stores.milvus import MilvusVectorStore
        #     # Requires MilvusVectorStore to be configured
        #     # Example: MilvusVectorStore(uri=self.config.MILVUS_URI, collection_name="your_collection")
        # except ImportError:
        #     self.logger.error("llama-index-vector-stores-milvus is not installed.")
        #     raise
        raise NotImplementedError("LlamaIndex integration for Milvus is not yet implemented.")

    # region Helper methods
    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def _load_from_path(self, vectorstore: Milvus, paths: Union[str, List[str]]) -> list[Document]:
        self.logger.debug(f"Begin loading data from {paths}...")
        try:
            from langchain_community.document_loaders import DirectoryLoader
            from langchain_docling import DoclingLoader
        except ImportError:
            self.logger.error("langchain-community or langchain-docling package is not installed.")
            raise

        if isinstance(paths, str):
            paths = [paths]

        all_documents = []
        with tempfile.TemporaryDirectory(suffix="_milvus_loader_tmp", delete=True) as tmp_dir:
            for path in tqdm(paths, desc="Moving to tmp directory", unit="path"):
                if os.path.isdir(path):
                    shutil.copytree(path, os.path.join(tmp_dir, os.path.basename(path)))
                else:
                    shutil.copy2(path, tmp_dir)

            for file in os.listdir(tmp_dir):
                if file.endswith(".txt") or file.endswith(".text"):
                    new_file = os.path.splitext(file)[0] + ".md"
                    os.rename(os.path.join(tmp_dir, file), os.path.join(tmp_dir, new_file))

            loader = DirectoryLoader(tmp_dir, loader_cls=DoclingLoader, silent_errors=True, show_progress=True)
            loaded_docs = loader.load()

            for d in tqdm(loaded_docs, desc="Processing documents for Milvus", unit="doc"):
                meta = d.metadata or {}
                processed_meta = {}
                for key, value in meta.items():
                    if isinstance(value, (dict, list)): # Ensure complex metadata types are JSON serialized
                        processed_meta[key] = json.dumps(value)
                    else:
                        processed_meta[key] = value

                processed_meta["model"] = self._embeddings.model
                processed_meta["dimensions"] = self.config.EMBEDDING_DIMENSION
                processed_meta["lastUpdate"] = datetime.now(UTC).isoformat()

                all_documents.append(Document(page_content=d.page_content, metadata=processed_meta))

        if all_documents:
            vectorstore.add_documents(all_documents)
            self.logger.info(f"Loaded {len(all_documents)} documents from path(s).")
        else:
            self.logger.info("No documents found in the provided path(s).")
        return all_documents

    def _load_from_data(self, vectorstore: Milvus, data: List[Dict[str, Any]]) -> list[Document]:
        self.logger.debug(f"Loading {len(data)} objects into Milvus collection...")
        documents = []
        try:
            for item in tqdm(data, desc="Transforming to documents", unit="dict"):
                page_content = item.get("content")
                if not page_content:
                    self.logger.warning(f"Skipping item due to missing 'content': {item}")
                    continue

                item_metadata = item.get("metadata", {})
                processed_meta = {}
                for key, value in item_metadata.items():
                    if isinstance(value, (dict, list)): # Ensure complex metadata types are JSON serialized
                        processed_meta[key] = json.dumps(value)
                    else:
                        processed_meta[key] = value

                processed_meta["model"] = self._embeddings.model
                processed_meta["dimensions"] = self.config.EMBEDDING_DIMENSION
                processed_meta["lastUpdate"] = datetime.now(UTC).isoformat()

                documents.append(Document(page_content=page_content, metadata=processed_meta))
        except KeyError as e:
            self.logger.error(f"Key error while loading data: {e}. Ensure 'content' key is present.")
            raise

        if documents:
            vectorstore.add_documents(documents)
            self.logger.info(f"Loaded {len(documents)} documents from data.")
        else:
            self.logger.info("No documents to load from data.")
        return documents

    def _load_from_uri(self, vectorstore: Milvus, uris: Union[str, List[str]]) -> list[Document]:
        try:
            from langchain_docling import DoclingLoader
        except ImportError:
            self.logger.error("langchain-docling package is not installed.")
            raise

        if isinstance(uris, str):
            uris = [uris]

        self.logger.debug(f"Loading {len(uris)} URIs into Milvus collection...")
        all_documents = []
        loader = DoclingLoader(file_path=uris)
        loaded_docs = loader.load()

        for doc in tqdm(loaded_docs, desc="Processing documents from URIs for Milvus", unit="doc"):
            meta = doc.metadata or {}
            processed_meta = {}
            for key, value in meta.items():
                if isinstance(value, (dict, list)):
                    processed_meta[key] = json.dumps(value)
                else:
                    processed_meta[key] = value

            processed_meta["model"] = self._embeddings.model
            processed_meta["dimensions"] = self.config.EMBEDDING_DIMENSION
            processed_meta["lastUpdate"] = datetime.now(UTC).isoformat()
            all_documents.append(Document(page_content=doc.page_content, metadata=processed_meta))

        if all_documents:
            vectorstore.add_documents(all_documents)
            self.logger.info(f"Loaded {len(all_documents)} documents from URIs.")
        else:
            self.logger.info("No documents loaded from the provided URIs.")
        return all_documents

    # endregion

    # region: Default async methods (must be implemented from VectorDBClient)
    # TODO: Implement true async operations if an async Milvus client becomes available or if current client supports it.
    async def load_async(self, collection_name: str, **kwargs) -> list[Document]:
        self.logger.warning("Async load not fully implemented for Milvus, using sync version.")
        return self.load(collection_name, **kwargs)

    async def remove_collection_async(self, collection_name: str) -> None:
        self.logger.warning("Async remove_collection not fully implemented for Milvus, using sync version.")
        return self.remove_collection(collection_name)

    async def delete_async(self, collection_name: str, ids: List[str]) -> None:
        self.logger.warning("Async delete not fully implemented for Milvus, using sync version.")
        return self.delete(collection_name, ids)

    async def search_async(self, collection_name: str, query: str, top_k: int = 3, **kwargs) -> List[Document]:
        self.logger.warning("Async search not fully implemented for Milvus, using sync version.")
        return self.search(collection_name, query, top_k, **kwargs)

    async def exists_async(self, collection_name: str) -> bool:
        self.logger.warning("Async exists not fully implemented for Milvus, using sync version.")
        return self.exists(collection_name)

    async def from_langchain_async(self, collection_name: str, documents: List[Document], **kwargs) -> list[Document]:
        self.logger.warning("Async from_langchain not fully implemented for Milvus, using sync version.")
        return self.from_langchain(collection_name, documents, **kwargs)
    # endregion
