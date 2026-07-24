
import logging
import uuid
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import grpc
from grpc import aio
import numpy as np
# Import the generated gRPC modules
# Make sure to add the parent directory to sys.path if needed
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import proto.python.inference_pb2 as inference_pb2
    import proto.python.inference_pb2_grpc as inference_pb2_grpc
except ImportError as e:
    print(f"ImportError: {e}")
    print("Error: Could not import gRPC modules. Make sure to run generate_proto.py first.")
    print("Run: python embeddings/generate_proto.py")
    sys.exit(1)

logger = logging.getLogger(__name__)

class InferenceClient:
    """Client for the InferenceService gRPC service."""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        """Initialize the client.
        
        Args:
            host: The host of the gRPC server.
            port: The port of the gRPC server.
        """
        self.host = host
        self.port = port
        self.channel = None
        self.stub = None
    
    async def connect(self):
        """Connect to the gRPC server."""
        if self.channel is None:
            address = f"{self.host}:{self.port}"
            logger.info(f"Connecting to gRPC server at {address}")
            
            # Create a channel with increased message size limits
            self.channel = aio.insecure_channel(
                address,
                options=[
                    ('grpc.max_send_message_length', 100 * 1024 * 1024),
                    ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                ]
            )
            self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)
    
    async def close(self):
        """Close the connection to the gRPC server."""
        if self.channel is not None:
            await self.channel.close()
            self.channel = None
            self.stub = None
    
    
    async def embed(
        self,
        prompts: List[str],
        model_name: str,
        request_id: Optional[str] = None,
    ) -> List[np.ndarray]:
        """Embed a given prompt.
        
        Args:
            prompts: The prompts to embed.
            model_name: The name of the model to use.
            request_id: Optional request ID.
            
        Returns:
            A list of embedding arrays.
        """
        if self.stub is None:
            await self.connect()
        
        # Create the request
        request_id = request_id or str(uuid.uuid4())
        
        # Create the request
        request = inference_pb2.EncodeRequest(
            request_id=request_id,
            n_prompts=len(prompts),
            prompts=prompts,
            model_name=model_name,
        )
    
        embedding_response = await self.stub.Encode(request)

        if embedding_response.error:
            raise Exception(embedding_response.error)
        
        n_prompts = len(prompts)
        embedding_dim = embedding_response.embedding_dim

        if embedding_response.n_prompts != n_prompts:
            raise Exception(f"Expected {n_prompts} embeddings, got {embedding_response.n_prompts}")

        if len(embedding_response.embedding_bytes_fp32) != n_prompts:
            raise Exception(f"Expected {n_prompts * embedding_dim * 4} bytes, got {len(embedding_response.embedding_bytes_fp32)}")
        
        embeddings = []
        for i in range(n_prompts):
            embedding = np.frombuffer(embedding_response.embedding_bytes_fp32[i], dtype=np.float32).reshape(embedding_dim)
            embeddings.append(embedding)

        return embeddings

    async def embed_single(
        self,
        prompt: str,
        model_name: str,
        request_id: Optional[str] = None,
    ) -> List[np.ndarray]:
        """Convenience method to embed a single prompt."""
        return await self.embed(prompts=[prompt], model_name=model_name, request_id=request_id)

    async def embed_query(
        self,
        query: str,
        model_name: str,
        request_id: Optional[str] = None,
    ) -> List[np.ndarray]:
        """Convenience method to embed a query with 'query:' prefix."""
        return await self.embed(prompts=[f"query: {query}"], model_name=model_name, request_id=request_id)

    
    async def abort(self, request_id: str) -> Dict[str, Any]:
        """Abort an ongoing generation.
        
        Args:
            request_id: The ID of the request to abort.
            
        Returns:
            A dictionary with the result of the abort operation.
        """
        if self.stub is None:
            await self.connect()
        
        request = inference_pb2.AbortRequest(request_id=request_id)
        
        try:
            response = await self.stub.Abort(request)
            return {
                "success": response.success,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error(f"RPC error: {e}")
            raise
    
    async def get_replica_info(self):
        """Get replica information.
        
        Returns:
            A dictionary with model information.
        """
        if self.stub is None:
            await self.connect()
        
        request = inference_pb2.ReplicaInfoRequest()
        
        try:
            response = await self.stub.GetReplicaInfo(request)

            return response
        
        except grpc.RpcError as e:
            logger.error(f"RPC error: {e}")
            raise
    
    async def health_check(self) -> inference_pb2.HealthCheckResponse:
        """Perform a health check.
        
        Returns:
            A dictionary with the health status.
        """
        if self.stub is None:
            await self.connect()
        
        request = inference_pb2.HealthCheckRequest()
        
        try:
            response = await self.stub.HealthCheck(request)
            return response
        except grpc.RpcError as e:
            logger.error(f"RPC error: {e}")
            raise
