import os
import logging
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import OpenSearchException
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from requests_aws4auth import AWS4Auth
from ephor_cli.constant import AWS_OPENSEARCH_ENDPOINT
from ephor_cli.constant import AWS_OPENSEARCH_INDEX_NAME

logger = logging.getLogger(__name__)

class OpenSearchClient:
    """Client for AWS OpenSearch Service with vector search capabilities."""
    
    def __init__(self):
        self.endpoint = AWS_OPENSEARCH_ENDPOINT
        self.index_name = AWS_OPENSEARCH_INDEX_NAME
        self.region = "us-east-1"  
        
        # Remove https:// if present
        if self.endpoint.startswith('https://'):
            self.endpoint = self.endpoint[8:]
        
        self.client = self._create_client()
        
    def _create_client(self) -> OpenSearch:
        """Create OpenSearch client with AWS authentication."""
        try:
            # Get AWS credentials
            session = boto3.Session()
            credentials = session.get_credentials()
            
            # Create AWS4Auth for authentication
            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                self.region,
                'es',
                session_token=credentials.token
            )
            
            client = OpenSearch(
                hosts=[{'host': self.endpoint, 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=60
            )
            
            # Test connection
            client.info()
            logger.info(f"Successfully connected to OpenSearch at {self.endpoint}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create OpenSearch client: {e}")
            raise
    
    def create_vector_index(self) -> bool:
        """Create vector index with proper mapping for embeddings."""
        mapping = {
            "mappings": {
                "properties": {
                    "conversation_id": {"type": "keyword"},
                    "attachment_id": {"type": "keyword"},
                    "filename": {"type": "text"},
                    "chunk_index": {"type": "integer"},
                    "chunk_text": {"type": "text"},
                    "file_type": {"type": "keyword"},
                    "content_type": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "embedding_vector": {
                        "type": "knn_vector",
                        "dimension": 1536,  # OpenAI text-embedding-3-small dimension
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "lucene"
                        }
                    }
                }
            },
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            }
        }
        
        try:
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"Index {self.index_name} already exists")
                return True
                
            response = self.client.indices.create(
                index=self.index_name,
                body=mapping
            )
            logger.info(f"Created vector index {self.index_name}: {response}")
            return True
            
        except OpenSearchException as e:
            logger.error(f"Failed to create vector index: {e}")
            return False
    
    def store_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Store document chunks with embeddings in bulk."""
        try:
            bulk_body = []
            
            for chunk in chunks:
                # Index action
                bulk_body.append({
                    "index": {
                        "_index": self.index_name,
                        "_id": f"{chunk['conversation_id']}_{chunk['attachment_id']}_{chunk['chunk_index']}"
                    }
                })
                # Document data
                bulk_body.append(chunk)
            
            response = self.client.bulk(body=bulk_body)
            
            if response.get('errors'):
                logger.error(f"Bulk indexing errors: {response}")
                return False
                
            logger.info(f"Successfully stored {len(chunks)} chunks")
            return True
            
        except OpenSearchException as e:
            logger.error(f"Failed to store chunks: {e}")
            return False
    
    def similarity_search(self, query_vector: List[float], conversation_id: str, 
                         top_k: int = 5, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform cosine similarity search for relevant chunks."""
        try:
            # Use KNN query directly for proper similarity scoring
            query_body = {
                "size": top_k * 2,  # Get more results to filter by conversation_id
                "query": {
                    "knn": {
                        "embedding_vector": {
                            "vector": query_vector,
                            "k": top_k * 2
                        }
                    }
                },
                "_source": [
                    "conversation_id", "attachment_id", "filename", 
                    "chunk_index", "chunk_text", "file_type", "content_type", "created_at"
                ]
            }
            
            response = self.client.search(
                index=self.index_name,
                body=query_body
            )
            
            results = []
            for hit in response['hits']['hits']:
                # Filter by conversation_id after KNN search
                if hit['_source']['conversation_id'] != conversation_id:
                    continue
                    
                # OpenSearch KNN returns scores that need to be converted to similarity
                # For cosine similarity with HNSW, score = 1 / (1 + distance)
                # where distance = 1 - cosine_similarity
                # So: cosine_similarity = 1 - (1/score - 1) = 2 - 1/score
                raw_score = hit['_score']
                
                # Handle edge cases
                if raw_score <= 0:
                    similarity = 0.0
                elif raw_score >= 1.0:
                    # Direct cosine similarity (close to 1.0)
                    similarity = min(raw_score, 1.0)
                else:
                    # Convert HNSW score to cosine similarity
                    # For cosinesimil space_type: similarity = 2 - (1/score)
                    similarity = max(0.0, min(1.0, 2.0 - (1.0 / raw_score)))
                
                if similarity >= similarity_threshold:
                    result = hit['_source']
                    result['similarity_score'] = similarity
                    results.append(result)
                    
                    # Stop when we have enough results
                    if len(results) >= top_k:
                        break
            
            logger.info(f"Found {len(results)} relevant chunks above threshold {similarity_threshold}")
            return results
            
        except OpenSearchException as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def delete_conversation_chunks(self, conversation_id: str) -> bool:
        """Delete all chunks for a conversation."""
        try:
            query_body = {
                "query": {
                    "term": {
                        "conversation_id": conversation_id
                    }
                }
            }
            
            response = self.client.delete_by_query(
                index=self.index_name,
                body=query_body
            )
            
            deleted = response.get('deleted', 0)
            logger.info(f"Deleted {deleted} chunks for conversation {conversation_id}")
            return True
            
        except OpenSearchException as e:
            logger.error(f"Failed to delete conversation chunks: {e}")
            return False
    
    def delete_attachment_chunks(self, attachment_id: str) -> bool:
        """Delete all chunks for a specific attachment."""
        try:
            query_body = {
                "query": {
                    "term": {
                        "attachment_id": attachment_id
                    }
                }
            }
            
            response = self.client.delete_by_query(
                index=self.index_name,
                body=query_body
            )
            
            deleted = response.get('deleted', 0)
            logger.info(f"Deleted {deleted} chunks for attachment {attachment_id}")
            return deleted > 0
            
        except OpenSearchException as e:
            logger.error(f"Failed to delete attachment chunks: {e}")
            return False
    
    def delete_specific_chunks(self, conversation_id: str, attachment_id: str) -> bool:
        """Delete chunks for a specific attachment within a conversation."""
        try:
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"conversation_id": conversation_id}},
                            {"term": {"attachment_id": attachment_id}}
                        ]
                    }
                }
            }
            
            response = self.client.delete_by_query(
                index=self.index_name,
                body=query_body
            )
            
            deleted = response.get('deleted', 0)
            logger.info(f"Deleted {deleted} chunks for attachment {attachment_id} in conversation {conversation_id}")
            return deleted > 0
            
        except OpenSearchException as e:
            logger.error(f"Failed to delete specific chunks: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check OpenSearch cluster health."""
        try:
            health = self.client.cluster.health()
            info = self.client.info()
            
            return {
                "status": health.get('status', 'unknown'),
                "cluster_name": health.get('cluster_name', 'unknown'),
                "version": info.get('version', {}).get('number', 'unknown'),
                "connected": True
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "red",
                "connected": False,
                "error": str(e)
            } 