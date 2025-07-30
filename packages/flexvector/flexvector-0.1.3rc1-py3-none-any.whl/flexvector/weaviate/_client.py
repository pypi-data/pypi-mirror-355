import hashlib
import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from typing import List, Dict, Any, Union
from urllib.parse import urlparse

import weaviate
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore
from loguru import logger
from tqdm import tqdm
from weaviate.classes.init import Auth
from weaviate.collections.classes.config import DataType, Property

from flexvector.config import VectorDBSettings
from flexvector.core import VectorDBClient, Document


class WeaviateFlexClient(VectorDBClient):
    __slots__ = (
        "_weaviate_client",
        "_embeddings",
        "logger",
        "config",
    )

    def __init__(self, config: VectorDBSettings):
        self.logger = logger.bind(context="WeaviateFlexClient")
        self.config = config
        if config.WEAVIATE_HTTP_URL is None:
            raise ValueError("You need to provide connection info for a local or remote Weaviate instance")

        if config.WEAVIATE_HTTP_URL.startswith("http://"):
            self.logger.info(f"Connecting to local Weaviate instance at: {config.WEAVIATE_HTTP_URL}")
            parsed_url = urlparse(config.WEAVIATE_HTTP_URL)
            self._weaviate_client = weaviate.connect_to_local(
                host=parsed_url.hostname,
                port=parsed_url.port,
                grpc_port=os.environ.get("WEAVIATE_GRPC_PORT", 50051),
            )
        elif config.WEAVIATE_CLOUD_ENABLED:
            self.logger.info(f"Using Weaviate cloud instance at: {config.WEAVIATE_HTTP_URL}")
            self._weaviate_client = weaviate.connect_to_weaviate_cloud(
                cluster_url=config.WEAVIATE_HTTP_URL,
                auth_credentials=Auth.api_key(config.WEAVIATE_API_KEY),
            )
        else:
            logger.info(f"Connecting custom weavite server running on: {config.WEAVIATE_HTTP_URL}")
            parsed_url = urlparse(config.WEAVIATE_HTTP_URL)
            self._weaviate_client = weaviate.connect_to_custom(
                http_host=parsed_url.hostname,
                http_port=parsed_url.port,
                http_secure=parsed_url.scheme == "https",
                grpc_host=os.getenv("WEAVIATE_GRPC_HOST", parsed_url.hostname),
                grpc_port=os.environ.get("WEAVIATE_GRPC_PORT", 50051),
                grpc_secure=parsed_url.scheme == "https",
                auth_credentials=Auth.api_key(config.WEAVIATE_API_KEY),
            )
        is_ready = self._weaviate_client.is_ready()
        collection_info = self._weaviate_client.collections.list_all(True)
        self.logger.info(
            f"Successfully connected to Weaviate instance. Found {len(collection_info)} collections.\n{collection_info}")

        self.logger.info(
            f"Successfully connected to Weaviate instance. {is_ready=}")

        if config.OPENAI_API_KEY:
            self._embeddings = OpenAIEmbeddings(api_key=config.OPENAI_API_KEY,
                                                dimensions=config.EMBEDDING_DIMENSION,
                                                chunk_size=3096,
                                                show_progress_bar=True,
                                                model=config.EMBEDDING_MODEL)
            self.logger.debug(f"Using embedding model {config.EMBEDDING_MODEL}")
        else:
            self.logger.info("No OpenAI API key provided, Will use FastEmbed embeddings")
            self._embeddings = FastEmbedEmbeddings(
                model_name=config.FAST_EMBEDDING_MODEL,
                max_length=512
            )
            self.config.EMBEDDING_DIMENSION = 512

    def load(self, collection_name: str, **kwargs) -> list[Document]:
        """Load data into a Weaviate collection.

        Args:
            collection_name (str): The name of the collection to load data into.
            **kwargs: Additional arguments to specify the source of the data. Can be:
                - path (str or list): Path(s) to the data file(s).
                - data (list): List of documents to load.
                - uri (str or list): URI(s) to fetch data from.
        """

        self.logger.debug(f"Loading to collection {collection_name} given kwargs: {kwargs.keys()}")

        path = kwargs.get("path")
        data = kwargs.get("data")
        uri = kwargs.get("uri")

        self._get_or_create_collection(collection_name)
        vectorstore = WeaviateVectorStore(
            index_name=collection_name,
            embedding=self._embeddings,
            client=self._weaviate_client,
            text_key="text"
        )

        if path:
            return self._load_from_path(vectorstore, path)
        elif data:
            return self._load_from_data(vectorstore, data)
        elif uri:
            return self._load_from_uri(vectorstore, uri)
        else:
            raise ValueError("You MUST provide either path, data, or uri to load data")

    def _get_or_create_collection(self, collection_name: str) -> None:
        self.logger.debug(f"GetOrCreate weaviate collection {collection_name}..")
        return  # TODO: Let langchain handle the collection creation for now
        # noinspection PyUnreachableCode
        collection = self._weaviate_client.collections.get(collection_name)
        if not collection.exists():
            self.logger.info(f"Collection {collection_name} does not exist, creating it...")
            self._weaviate_client.collections.create(
                collection_name,
                description=collection_name,
                properties=[
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="hash", data_type=DataType.TEXT),
                    # Property(name="metadata", data_type=DataType.OBJECT),
                ]
            )
            return
        self.logger.debug(f"Collection {collection_name} already exists")

    def from_langchain(self, collection_name: str, documents: list[Document], **kwargs) -> list[Document]:
        """Load langchain compatible documents into the vector database.

        Args:
            collection_name (str): The name of the collection to load data into.
            documents (List[Document]): List of langchain compatible documents to load.
            **kwargs: Additional arguments for loading data.
        """
        self.logger.debug(f"Loading {len(documents)} langchain documents into collection {collection_name}...")
        self._get_or_create_collection(collection_name)
        vectorstore = WeaviateVectorStore(
            index_name=collection_name,
            embedding=self._embeddings,
            client=self._weaviate_client,
            text_key="text"
        )

        ids = vectorstore.add_documents(documents)
        self.logger.info(f"Loaded {len(ids)} documents into collection {collection_name}.")
        return documents

    def search(self, collection_name: str, query: str, top_k: int = 3, **kwargs) -> list[Document]:
        """Search a Weaviate collection for similar documents.

        Args:
            collection_name (str): The name of the collection to search.
            query (str): The query string or vector to search for.
            top_k (int): The number of top results to return.
            **kwargs: Additional arguments for the search.
        Returns:
            List[Document]: A list of documents matching the query.
        """
        self.logger.debug(f"Searching collection {collection_name} with query: {query[:25]}...")
        self.logger.debug(f"Given kwargs: {kwargs}")

        search_type = kwargs.get("search_type", "similarity")
        filters = kwargs.get("filters", {})
        initial_candidates = kwargs.get("initial_candidates", 10)  # Before re-ranking
        self.logger.debug(
            f"Search params: search_type={search_type}, filters={filters}, initial_candidates={initial_candidates}")

        if not self._weaviate_client.collections.get(collection_name).exists():
            raise FileNotFoundError(f"Collection {collection_name} does not exist")

        vectorstore = WeaviateVectorStore(
            index_name=collection_name,
            embedding=self._embeddings,
            client=self._weaviate_client,
            text_key="text"
        )

        retriever = vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs={"k": top_k, "fetch_k": initial_candidates},
        )
        docs = retriever.invoke(query, filter=filters if len(filters) > 0 else None)
        self.logger.debug(f"Found {len(docs)} documents for query {query[:25]}...")
        return docs

    def remove_collection(self, collection_name: str) -> None:
        """Remove a collection from Weaviate.

        Args:
            collection_name (str): The name of the collection to remove.
        """
        self.logger.debug(f"Removing collection {collection_name}...")
        self._weaviate_client.collections.delete(collection_name)
        self.logger.info(f"Collection {collection_name} removed.")

    def delete(self, collection_name: str, ids: list[str]) -> None:
        """Delete a list of documents from a Weaviate collection.

        Args:
            collection_name (str): The name of the collection to delete from.
            ids (List[str]): List of document IDs to delete.
        """
        self.logger.debug(f"Deleting {len(ids)} documents from collection {collection_name}...")
        collection = self._weaviate_client.collections.get(collection_name)
        for doc_id in ids:
            collection.data.delete_by_id(doc_id)
        self.logger.info(f"Deleted {len(ids)} documents from collection {collection_name}.")

    def exists(self, collection_name: str) -> bool:
        """Check if a collection exists in Weaviate.

        Args:
            collection_name (str): The name of the collection to check.
        Returns:
            bool: True if the collection exists, False otherwise.
        """
        self.logger.debug(f"Checking if collection {collection_name} exists...")
        try:
            exists = self._weaviate_client.collections.exists(collection_name)
        except ValueError:
            exists = False
        self.logger.info(f"Collection {collection_name} exists: {exists}")
        return exists

    def get_info(self):
        collections = self._weaviate_client.collections.list_all()
        collection_names = [c for c in collections] if collections else []

        return dict(
            connection=self.config.WEAVIATE_HTTP_URL or "local",
            collections={
                "count": len(collection_names),
                "names": collection_names
            },
            telemetry=self._weaviate_client.get_meta(),
            embedding_fn=str(self._embeddings.__class__.__name__)
        )

    @property
    def client(self) -> Union[weaviate.WeaviateClient]:
        return self._weaviate_client

    @property
    def langchain(self) -> WeaviateVectorStore:
        return WeaviateVectorStore(
            client=self._weaviate_client,
            text_key="text",
            index_name="default",
            embedding=self._embeddings,
        )

    @property
    def llama_index(self):
        raise NotImplementedError()

    # region Helper methods
    @staticmethod
    def _get_hash(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def _load_from_path(self, vectorstore: WeaviateVectorStore, paths: Union[str, list[str]]) -> list[Document]:
        """Load data from a file or list of files into Weaviate collection. The path could also be a directory.

        Args:
            vectorstore (WeaviateVectorStore): The langchain Weaviate vector store instance.
            paths (Union[str, List[str]]): Path(s) to the data file(s) or directory(s) to load data from.

        Returns:
            list[Document]: A list of documents loaded from the specified path(s).
        """
        self.logger.debug(f"Begin loading data from paths...")
        try:
            from langchain_community.document_loaders import DirectoryLoader
        except ImportError:
            self.logger.error("langchain-community package is not installed. Please install it to use this feature.")
            raise

        try:
            from langchain_docling import DoclingLoader
        except ImportError:
            self.logger.error("langchain-docling package is not installed. Please install it to use this feature.")
            raise

        from langchain_community.document_loaders import DirectoryLoader
        from langchain_docling import DoclingLoader

        if isinstance(paths, str):
            paths = [paths]

        self.logger.debug("Moving files to a single tmp directory...")
        with tempfile.TemporaryDirectory(suffix="_qdrant_loader_tmp", delete=True) as tmp_dir:
            for path in tqdm(paths, desc="Moving to tmp directory", unit="path"):
                if os.path.isdir(path):
                    self.logger.debug(f"Copying directory {path} to {tmp_dir}")
                    shutil.copytree(path, os.path.join(tmp_dir, os.path.basename(path)))
                else:
                    self.logger.debug(f"Copying file {path} to {tmp_dir}")
                    shutil.copy2(path, tmp_dir)

            # If any files, have .txt or .text extension, rename them to .md
            for file in os.listdir(tmp_dir):
                if file.endswith(".txt") or file.endswith(".text"):
                    new_file = os.path.splitext(file)[0] + ".md"
                    os.rename(os.path.join(tmp_dir, file), os.path.join(tmp_dir, new_file))
                    self.logger.debug(f"Renamed {file} to {new_file}")

            self.logger.debug(f"Loading data from {tmp_dir}...")
            # noinspection PyTypeChecker
            loader = DirectoryLoader(tmp_dir, loader_cls=DoclingLoader)
            documents = []
            for d in loader.load():
                meta = d.metadata
                meta["model"] = self._embeddings.model
                meta["dimensions"] = self.config.EMBEDDING_DIMENSION
                meta["lastUpdate"] = datetime.now(UTC).isoformat()
                for key, value in meta.items():
                    if isinstance(value, (dict, list)):
                        self.logger.debug(f"Converting metadata={key}:{value} to str")
                        meta[key] = json.dumps(value, indent=2)
                d.metadata = meta
                documents.append(d)
            vectorstore.add_documents(documents)
            self.logger.info(f"Loaded {len(documents)} documents from {tmp_dir}")
            return documents

    def _load_from_data(self, vectorstore: WeaviateVectorStore, data: list[dict[str, Any]]) -> list[Document]:
        """Loads data from a list of dictionaries into a Weaviate collection.

        Args:
            vectorstore (WeaviateVectorStore): The langchain Weaviate vector store instance.
            data (List[Dict[str, Any]]): List of dictionaries containing the data to load.

        Returns:
            list[Document]: A list of documents loaded from the specified data.
        """
        self.logger.debug(f"Loading {len(data)} objects into Weaviate collection...")
        documents = []
        try:
            for item in tqdm(data, desc="Transforming to documents", unit="dict"):
                # noinspection PyArgumentList
                doc = Document(
                    page_content=item["content"],
                    id=self._get_hash(item["content"]),
                    metadata=dict(
                        model=self._embeddings.model,
                        dimensions=self.config.EMBEDDING_DIMENSION,
                        lastUpdate=datetime.now(UTC).isoformat(),
                        **item.get("metadata", {})
                    )
                )
                documents.append(doc)
        except KeyError as e:
            self.logger.error(
                f"Key error while loading data: {e}. Please make sure content key is present in the data.")
            raise

        ids = vectorstore.add_documents(documents)
        self.logger.debug(f"Loaded {len(ids)} documents")
        return documents

    def _load_from_uri(self, vectorstore: WeaviateVectorStore, uris: Union[str, list[str]]) -> list[Document]:
        """Load data from a list of URIs into a Weaviate collection.
        Each URI must be a publicly accessible document supported by `docling` loaders.

        Args:
            vectorstore (WeaviateVectorStore): The langchain Weaviate vector store instance.
            uris (Union[str, List[str]]): URI(s) to fetch data from.

        Returns:
            list[Document]: A list of documents loaded from the specified URIs.
        """
        try:
            from langchain_docling import DoclingLoader
        except ImportError:
            self.logger.error("langchain-docling package is not installed. Please install it to use this feature.")
            raise

        if isinstance(uris, str):
            uris = [uris]

        self.logger.debug(f"Loading {len(uris)} URIs into Weaviate collection...")
        documents = []
        loader = DoclingLoader(file_path=uris)
        for doc in tqdm(loader.load(), desc="Enrich Metatata", unit="doc"):
            meta = doc.metadata
            meta["model"] = self._embeddings.model
            meta["dimensions"] = self.config.EMBEDDING_DIMENSION
            meta["lastUpdate"] = datetime.now(UTC).isoformat()
            documents.append(doc)

        ids = vectorstore.add_documents(documents)
        self.logger.debug(f"Loaded {len(ids)} documents")
        return documents

    # endregion

    # region: Async methods

    async def remove_collection_async(self, collection_name: str) -> None:
        raise NotImplementedError("Async operations are not supported in this client.")

    async def delete_async(self, collection_name: str, ids: list[str]) -> None:
        raise NotImplementedError("Async operations are not supported in this client.")

    async def search_async(self, collection_name: str, query: str, top_k: int = 3, **kwargs) -> list[Document]:
        raise NotImplementedError("Async operations are not supported in this client.")

    async def load_async(self, collection_name: str, **kwargs) -> list[Document]:
        raise NotImplementedError("Async operations are not supported in this client.")

    async def exists_async(self, collection_name: str) -> bool:
        raise NotImplementedError("Async operations are not supported in this client.")
    # endregion
