import asyncio
import os
import json
from openai import OpenAI

class LLMClient:
    """
    A simple chat completion client for OpenAI models.
    Configures using the same pattern as other MCP services.
    """
    
    def __init__(self, openai_api_key=None):
        """
        Initialize the LLM client with the provided API key or from environment.
        
        Args:
            openai_api_key (str, optional): OpenAI API key. If not provided, 
                                          will be obtained from configuration or environment.
        """
        self.api_key = openai_api_key
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the OpenAI client with the API key."""
        if self.client is None:
            self.client = OpenAI(api_key=self.api_key)
    
    async def chat_completion(self, messages, model_name="gpt-4o", json_mode=False, temperature=0.7, max_tokens=1000):
        """
        Async version of fetching a response from the OpenAI API for the given messages.
        
        Args:
            messages (list): List of message objects with role and content.
            model_name (str): OpenAI model name to use.
            json_mode (bool): If True, attempts to parse the assistant's response as JSON.
            temperature (float): Controls randomness. Lower values make responses more deterministic.
            max_tokens (int): Maximum number of tokens to generate.
            
        Returns:
            Union[str, dict]: The model's response, parsed as JSON if json_mode=True.
        """
        if json_mode:
            response_format = {"type": "json_object"}
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model_name,
                messages=messages,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            return json.loads(response.choices[0].message.content)
        else:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            return response.choices[0].message.content

    async def ask(self, query, system_prompt=None, model_name="gpt-4o", json_mode=False, temperature=0.7):
        """
        Simple completion method that takes a query and optional system prompt.
        
        Args:
            query (str): The user's query or message.
            system_prompt (str, optional): System message to guide the model's behavior.
            model_name (str): OpenAI model name to use.
            json_mode (bool): If True, attempts to parse the assistant's response as JSON.
            temperature (float): Controls randomness. Lower values make responses more deterministic.
            
        Returns:
            Union[str, dict]: The model's response, parsed as JSON if json_mode=True.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})
        
        return await self.chat_completion(messages, model_name, json_mode, temperature)


def create_llm_client(config=None):
    """
    Create an LLM client using configuration from MCP config.
    
    Args:
        config (dict, optional): Configuration dictionary containing OpenAI API key.
                                If not provided, will use the default from constants.
                                
    Returns:
        LLMClient: An initialized LLM client.
    """
    if config is not None and 'openai' in config and 'api_key' in config['openai']:
        openai_api_key = config['openai']['api_key']
    else:
        openai_api_key = os.getenv('OPENAI_API_KEY')
    
    return LLMClient(openai_api_key=openai_api_key)