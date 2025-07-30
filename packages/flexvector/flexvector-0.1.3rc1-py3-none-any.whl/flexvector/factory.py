from flexvector.config import VectorDBSettings
from flexvector.core.models import VectorDBClient


class VectorDBFactory:

    @staticmethod
    def chroma(config: VectorDBSettings) -> VectorDBClient:
        from flexvector.chroma import ChromaFlexClient

        return ChromaFlexClient(config)

    @staticmethod
    def qdrant(config: VectorDBSettings) -> VectorDBClient:
        try:
            from flexvector.qdrant import QdrantFlexClient
        except ImportError:
            raise ImportError(
                "Qdrant dependencies not installed. Install with: pip install flexvector[qdrant]"
            )
        return QdrantFlexClient(config)

    @staticmethod
    def weaviate(config: VectorDBSettings) -> VectorDBClient:
        try:
            from flexvector.weaviate import WeaviateFlexClient
        except ImportError:
            raise ImportError(
                "Weaviate dependencies not installed. Install with: pip install flexvector[weaviate]"
            )
        return WeaviateFlexClient(config)

    @staticmethod
    def pgvector(config: VectorDBSettings) -> VectorDBClient:
        try:
            from flexvector.pgvector import PostgresFlexClient
        except ImportError:
            raise ImportError(
                "PGVector dependencies not installed. Install with: pip install flexvector[pgvector]"
            )
        return PostgresFlexClient(config)

    @staticmethod
    def milvus(config: VectorDBSettings) -> VectorDBClient:
        try:
            from flexvector.milvus import MilvusFlexClient
        except ImportError:
            raise ImportError(
                "Milvus dependencies not installed. Install with: pip install flexvector[milvus]"
            ) 
        return MilvusFlexClient(config)

    @staticmethod
    def get(db_type: str, config: VectorDBSettings) -> VectorDBClient:
        factory = VectorDBFactory()
        if db_type == "chroma":
            return factory.chroma(config)
        elif db_type == "qdrant":
            return factory.qdrant(config)
        elif db_type == "weaviate":
            return factory.weaviate(config)
        elif db_type == "pg":
            return factory.pgvector(config)
        elif db_type == "milvus":
            return factory.milvus(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @staticmethod
    def list_available() -> list[str]:
        """List all available vector database types."""
        return [
            "chroma",     # Default - always available
            "qdrant",     # Requires: pip install flexvector[qdrant]
            "weaviate",   # Requires: pip install flexvector[weaviate]  
            "pg",         # Requires: pip install flexvector[pgvector]
            "milvus",     # Requires: pip install flexvector[milvus]
        ]
    
    @staticmethod
    def list_installed() -> list[str]:
        """List currently installed and available vector database types."""
        available = ["chroma"]
        try:
            import qdrant_client
            available.append("qdrant")
        except ImportError:
            pass
            
        try:
            import weaviate
            available.append("weaviate")
        except ImportError:
            pass
            
        try:
            import pgvector
            available.append("pg")
        except ImportError:
            pass
            
        try:
            import pymilvus
            available.append("milvus")
        except ImportError:
            pass
            
        return available
