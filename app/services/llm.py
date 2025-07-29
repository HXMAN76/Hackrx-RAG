import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

import httpx
import groq  # Import Groq client

from app.config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Groq LLM API."""
    
    def __init__(self, api_key: str = GROQ_API_KEY, model: str = GROQ_MODEL):
        self.api_key = api_key
        self.model = model
        self.temperature = GROQ_TEMPERATURE
        self.max_tokens = GROQ_MAX_TOKENS
        self.timeout = httpx.Timeout(30.0)  # Default timeout
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Generate text using the Groq API.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            # Use provided values or defaults from config
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            logger.info(f"Sending request to Groq API with prompt length: {len(prompt)}")
            
            # Check if API key is set
            if not self.api_key:
                error_msg = "GROQ_API_KEY is not set. Please set it in your environment or .env file."
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Create Groq client
            client = groq.Groq(api_key=self.api_key)
            
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Call Groq API
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens
            )
            
            # Extract response text
            if completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.content
            return ""
                
        except httpx.TimeoutException:
            logger.error("Request to Groq API timed out")
            raise Exception("Request to LLM API timed out")
        except groq.error.APIError as e:
            logger.error(f"Groq API error: {str(e)}")
            raise Exception(f"Groq API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise
    
    async def generate_rag_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> str:
        """
        Generate a response using RAG methodology.
        
        Args:
            query: User query
            context_chunks: List of context chunks retrieved from vector store
            temperature: Controls randomness (0.0 to 1.0)
            
        Returns:
            Generated answer
        """
        try:
            # Format context for the prompt
            formatted_context = ""
            for i, chunk in enumerate(context_chunks):
                formatted_context += f"\nPASSAGE {i+1}:\n{chunk['text']}\n"
            
            system_prompt = """
            You are a helpful AI assistant that provides accurate answers based on the given context.
            If the answer cannot be found in the context, say that you don't have enough information.
            Always provide your answer based ONLY on the given context passages.
            Do not make up information or use your general knowledge to answer.
            """
            
            prompt = f"""
            CONTEXT:
            {formatted_context}
            
            USER QUERY: {query}
            
            Please provide a detailed and helpful answer to the user's query based ONLY on the provided context.
            """
            
            # Generate response
            response = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=1000
            )
            
            logger.info(f"Generated RAG response of length: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            raise


# Global instance for reuse
_llm_service = None


def get_llm_service() -> LLMService:
    """
    Get or create an LLMService instance.
    
    Returns:
        LLMService instance
    """
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService()
    
    return _llm_service
