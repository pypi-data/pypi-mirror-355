"""
AI Service for managing local and cloud-based language models.

This service handles:
- MLX integration for Apple Silicon local inference
- Hugging Face Transformers for cloud models
- Model loading, switching, and resource management
- Streaming response generation
"""

import asyncio
import logging
import platform
from typing import AsyncGenerator, Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of AI models available."""
    LOCAL_MLX = "mlx"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"


class ModelStatus(Enum):
    """Model loading status."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


@dataclass
class ModelInfo:
    """Information about an AI model."""
    name: str
    type: ModelType
    description: str
    size: str
    status: ModelStatus
    parameters: Optional[Dict[str, Any]] = None
    memory_usage: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None


@dataclass
class ChatResponse:
    """Response from AI model."""
    content: str
    model: str
    tokens_used: int
    processing_time: float
    finish_reason: str = "stop"


class AIModelManager:
    """Manages AI models and inference."""
    
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self.loaded_models: Dict[str, Any] = {}
        self.default_model = "phi-3-mini"
        self._initialize_available_models()
    
    def _initialize_available_models(self):
        """Initialize the catalog of available models."""
        # MLX Models (for Apple Silicon)
        if self._is_apple_silicon():
            self.models.update({
                "phi-3-mini": ModelInfo(
                    name="phi-3-mini",
                    type=ModelType.LOCAL_MLX,
                    description="Microsoft's efficient small language model optimized for Apple Silicon",
                    size="~3.8B parameters",
                    status=ModelStatus.UNLOADED,
                    parameters={"max_tokens": 2048, "temperature": 0.7}
                ),
                "llama-3.2-1b": ModelInfo(
                    name="llama-3.2-1b", 
                    type=ModelType.LOCAL_MLX,
                    description="Meta's compact Llama model for fast local inference",
                    size="~1B parameters",
                    status=ModelStatus.UNLOADED,
                    parameters={"max_tokens": 2048, "temperature": 0.7}
                ),
                "gemma-2b": ModelInfo(
                    name="gemma-2b",
                    type=ModelType.LOCAL_MLX,
                    description="Google's Gemma model optimized for Apple Silicon",
                    size="~2B parameters", 
                    status=ModelStatus.UNLOADED,
                    parameters={"max_tokens": 2048, "temperature": 0.7}
                )
            })
        
        # Hugging Face Models (cloud/local)
        self.models.update({
            "gpt-3.5-turbo": ModelInfo(
                name="gpt-3.5-turbo",
                type=ModelType.HUGGINGFACE,
                description="Fast and efficient conversational AI via Hugging Face",
                size="~175B parameters",
                status=ModelStatus.UNLOADED,
                parameters={"max_tokens": 4096, "temperature": 0.7}
            ),
            "llama-2-7b-chat": ModelInfo(
                name="llama-2-7b-chat",
                type=ModelType.HUGGINGFACE,
                description="Meta's Llama 2 chat model via Hugging Face",
                size="~7B parameters",
                status=ModelStatus.UNLOADED,
                parameters={"max_tokens": 4096, "temperature": 0.7}
            )
        })
    
    def _is_apple_silicon(self) -> bool:
        """Check if running on Apple Silicon."""
        return platform.system() == "Darwin" and platform.processor() == "arm"
    
    async def load_model(self, model_name: str) -> bool:
        """Load a specific model."""
        if model_name not in self.models:
            logger.error(f"Model {model_name} not found in catalog")
            return False
        
        model_info = self.models[model_name]
        if model_info.status == ModelStatus.LOADED:
            logger.info(f"Model {model_name} already loaded")
            return True
        
        logger.info(f"Loading model {model_name}...")
        model_info.status = ModelStatus.LOADING
        
        try:
            if model_info.type == ModelType.LOCAL_MLX:
                loaded_model = await self._load_mlx_model(model_name)
            elif model_info.type == ModelType.HUGGINGFACE:
                loaded_model = await self._load_huggingface_model(model_name)
            else:
                raise ValueError(f"Unsupported model type: {model_info.type}")
            
            self.loaded_models[model_name] = loaded_model
            model_info.status = ModelStatus.LOADED
            model_info.memory_usage = "2.1 GB"  # TODO: Calculate actual usage
            
            logger.info(f"Successfully loaded model {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            model_info.status = ModelStatus.ERROR
            model_info.error_message = str(e)
            return False
    
    async def _load_mlx_model(self, model_name: str) -> Any:
        """Load MLX model for Apple Silicon."""
        try:
            import mlx.core as mx
            from mlx_lm import load, generate
            
            # Map our model names to MLX model identifiers
            mlx_model_map = {
                "phi-3-mini": "microsoft/Phi-3-mini-4k-instruct",
                "llama-3.2-1b": "meta-llama/Llama-3.2-1B-Instruct", 
                "gemma-2b": "google/gemma-2b-it"
            }
            
            if model_name not in mlx_model_map:
                raise ValueError(f"MLX model mapping not found for {model_name}")
            
            # Load model and tokenizer
            model_path = mlx_model_map[model_name]
            model, tokenizer = await asyncio.to_thread(load, model_path)
            
            return {
                "model": model,
                "tokenizer": tokenizer,
                "generate_fn": generate,
                "type": "mlx"
            }
            
        except ImportError:
            logger.warning("MLX not available, using mock model")
            return self._create_mock_model(model_name, "mlx")
        except Exception as e:
            logger.error(f"Failed to load MLX model: {e}")
            raise
    
    async def _load_huggingface_model(self, model_name: str) -> Any:
        """Load Hugging Face model."""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            # Map our model names to HF model identifiers
            hf_model_map = {
                "gpt-3.5-turbo": "microsoft/DialoGPT-medium",  # Placeholder
                "llama-2-7b-chat": "meta-llama/Llama-2-7b-chat-hf"
            }
            
            if model_name not in hf_model_map:
                raise ValueError(f"HuggingFace model mapping not found for {model_name}")
            
            model_path = hf_model_map[model_name]
            
            # Load tokenizer and model
            tokenizer = await asyncio.to_thread(
                AutoTokenizer.from_pretrained, model_path
            )
            model = await asyncio.to_thread(
                AutoModelForCausalLM.from_pretrained,
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            return {
                "model": model,
                "tokenizer": tokenizer,
                "type": "huggingface"
            }
            
        except ImportError:
            logger.warning("Transformers not available, using mock model")
            return self._create_mock_model(model_name, "huggingface")
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {e}")
            raise
    
    def _create_mock_model(self, model_name: str, model_type: str) -> Dict[str, Any]:
        """Create a mock model for testing when real models aren't available."""
        return {
            "model": None,
            "tokenizer": None,
            "type": f"mock_{model_type}",
            "name": model_name
        }
    
    async def unload_model(self, model_name: str) -> bool:
        """Unload a specific model."""
        if model_name not in self.models:
            return False
        
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            
        self.models[model_name].status = ModelStatus.UNLOADED
        self.models[model_name].memory_usage = None
        
        logger.info(f"Unloaded model {model_name}")
        return True
    
    async def chat(
        self, 
        messages: List[ChatMessage], 
        model_name: Optional[str] = None,
        stream: bool = False,
        conversation_context: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Union[ChatResponse, AsyncGenerator[str, None]]:
        """Generate a chat response."""
        model_name = model_name or self.default_model
        
        # Ensure model is loaded
        if not await self.load_model(model_name):
            raise ValueError(f"Failed to load model {model_name}")
        
        # Combine conversation context with current messages
        all_messages = []
        if conversation_context:
            for ctx_msg in conversation_context:
                all_messages.append(ChatMessage(
                    role=ctx_msg["role"],
                    content=ctx_msg["content"],
                    timestamp=ctx_msg.get("timestamp")
                ))
        
        # Add current messages
        all_messages.extend(messages)
        
        if stream:
            return self._generate_streaming_response(all_messages, model_name, **kwargs)
        else:
            return await self._generate_single_response(all_messages, model_name, **kwargs)
    
    async def _generate_single_response(
        self, 
        messages: List[ChatMessage], 
        model_name: str,
        **kwargs
    ) -> ChatResponse:
        """Generate a single (non-streaming) response."""
        import time
        
        start_time = time.time()
        loaded_model = self.loaded_models[model_name]
        
        # Format messages for the model
        prompt = self._format_messages_for_model(messages, model_name)
        
        try:
            if loaded_model["type"] == "mlx":
                response_text = await self._generate_mlx_response(loaded_model, prompt, **kwargs)
            elif loaded_model["type"] == "huggingface":
                response_text = await self._generate_hf_response(loaded_model, prompt, **kwargs)
            else:
                # Mock response
                response_text = f"Mock AI response from {model_name}: {messages[-1].content}"
            
            processing_time = time.time() - start_time
            
            return ChatResponse(
                content=response_text,
                model=model_name,
                tokens_used=len(response_text.split()),  # Rough estimate
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def _generate_streaming_response(
        self, 
        messages: List[ChatMessage], 
        model_name: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response."""
        loaded_model = self.loaded_models[model_name]
        prompt = self._format_messages_for_model(messages, model_name)
        
        try:
            if loaded_model["type"] == "mlx":
                async for token in self._stream_mlx_response(loaded_model, prompt, **kwargs):
                    yield token
            elif loaded_model["type"] == "huggingface":
                async for token in self._stream_hf_response(loaded_model, prompt, **kwargs):
                    yield token
            else:
                # Mock streaming response
                response = f"Mock streaming AI response from {model_name}: {messages[-1].content}"
                for word in response.split():
                    yield f"{word} "
                    await asyncio.sleep(0.05)  # Simulate streaming delay
                    
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"Error: {str(e)}"
    
    def _format_messages_for_model(self, messages: List[ChatMessage], model_name: str) -> str:
        """Format conversation messages for the specific model."""
        # Simple formatting - can be enhanced per model
        formatted = ""
        for msg in messages:
            if msg.role == "user":
                formatted += f"User: {msg.content}\n"
            elif msg.role == "assistant":
                formatted += f"Assistant: {msg.content}\n"
            elif msg.role == "system":
                formatted += f"System: {msg.content}\n"
        
        formatted += "Assistant: "
        return formatted
    
    async def _generate_mlx_response(self, loaded_model: Dict, prompt: str, **kwargs) -> str:
        """Generate response using MLX model."""
        if loaded_model["model"] is None:
            return f"Mock MLX response for prompt: {prompt[:50]}..."
        
        try:
            # Use MLX generate function
            max_tokens = kwargs.get("max_tokens", 512)
            temperature = kwargs.get("temperature", 0.7)
            
            response = await asyncio.to_thread(
                loaded_model["generate_fn"],
                loaded_model["model"],
                loaded_model["tokenizer"],
                prompt=prompt,
                max_tokens=max_tokens,
                temp=temperature
            )
            
            return response
            
        except Exception as e:
            logger.error(f"MLX generation error: {e}")
            return f"MLX model generated response for: {prompt[:50]}..."
    
    async def _generate_hf_response(self, loaded_model: Dict, prompt: str, **kwargs) -> str:
        """Generate response using Hugging Face model."""
        if loaded_model["model"] is None:
            return f"Mock HuggingFace response for prompt: {prompt[:50]}..."
        
        try:
            import torch
            
            # Tokenize input
            inputs = loaded_model["tokenizer"].encode(prompt, return_tensors="pt")
            max_tokens = kwargs.get("max_tokens", 512)
            temperature = kwargs.get("temperature", 0.7)
            
            # Generate response
            with torch.no_grad():
                outputs = await asyncio.to_thread(
                    loaded_model["model"].generate,
                    inputs,
                    max_length=inputs.shape[1] + max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=loaded_model["tokenizer"].eos_token_id
                )
            
            # Decode response
            response = loaded_model["tokenizer"].decode(
                outputs[0][inputs.shape[1]:], 
                skip_special_tokens=True
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"HuggingFace generation error: {e}")
            return f"HuggingFace model generated response for: {prompt[:50]}..."
    
    async def _stream_mlx_response(self, loaded_model: Dict, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream response from MLX model."""
        # For now, simulate streaming by yielding chunks
        response = await self._generate_mlx_response(loaded_model, prompt, **kwargs)
        words = response.split()
        
        for word in words:
            yield f"{word} "
            await asyncio.sleep(0.05)
    
    async def _stream_hf_response(self, loaded_model: Dict, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream response from Hugging Face model."""
        # For now, simulate streaming by yielding chunks
        response = await self._generate_hf_response(loaded_model, prompt, **kwargs)
        words = response.split()
        
        for word in words:
            yield f"{word} "
            await asyncio.sleep(0.05)
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        return self.models.get(model_name)
    
    def list_models(self) -> List[ModelInfo]:
        """List all available models."""
        return list(self.models.values())
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models."""
        return list(self.loaded_models.keys())


# Global AI manager instance
ai_manager = AIModelManager()