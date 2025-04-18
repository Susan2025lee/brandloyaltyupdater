import os
import sys
import json
from typing import Dict, List, Optional, Any, Union
from openai import OpenAI, RateLimitError, APIError, APIConnectionError
from dotenv import load_dotenv  # Import load_dotenv
import time

# Add the project root to the Python path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import ModelManager from project root
from model_manager import ModelManager

# Load environment variables from .env file
load_dotenv()

class LLMInterface:
    """
    Interface for interacting with LLMs, specifically configured for OpenAI models
    with optional proxy settings.
    
    This class handles ONLY the communication with LLM APIs, providing a consistent
    interface regardless of the underlying model being used.
    
    Key features:
    - Conditionally applies proxy settings based on USE_LLM_PROXY environment variable.
    - Automatically detects and adapts to model-specific limitations
    - Converts system messages to user messages for models that don't support system roles
    - Handles temperature restrictions for models with fixed temperature requirements
    - Provides a consistent API across different OpenAI models
    """
    
    # OpenAI proxy configuration (used if USE_LLM_PROXY is True)
    OPENAI_PROXY = {
        "http": "http://testai:testai@192.168.1.7:6666",
        "https": "http://testai:testai@192.168.1.7:6666"
    }
    
    # Models with specific limitations
    MODELS_WITHOUT_SYSTEM_ROLE = ["o1-mini", "gpt-o1-mini"]
    MODELS_WITH_FIXED_TEMPERATURE = ["o1-mini", "gpt-o1-mini", "o3-mini", "gpt-o3-mini", "o4-mini", "gpt-o4-mini"]
    
    def __init__(self,
                 config_path: Optional[str] = None,
                 model_key: Optional[str] = None,
                 embedding_model_key: Optional[str] = None):
        """
        Initialize the LLM interface with specified configuration and conditional proxy.

        Chat model key is determined in the following order:
        1. Explicitly passed `model_key` argument.
        2. `DEFAULT_LLM_MODEL_KEY` environment variable.

        Embedding model key is determined in the following order:
        1. Explicitly passed `embedding_model_key` argument.
        2. `DEFAULT_EMBEDDING_MODEL_KEY` environment variable.

        Args:
            config_path: Path to the config.json file, if None will use default location.
            model_key: Optional chat model key. If None, reads from DEFAULT_LLM_MODEL_KEY env var.
            embedding_model_key: Optional embedding model key. If None, reads from
                                 DEFAULT_EMBEDDING_MODEL_KEY environment variable.
        """
        # --- Determine Chat Model Key ---
        if model_key is None:
            model_key = os.getenv("DEFAULT_LLM_MODEL_KEY")
            if model_key is None:
                # Allow initialization without a chat model if only embedding is needed
                print("Warning: Chat model key not provided and DEFAULT_LLM_MODEL_KEY environment variable not set.")
                self.current_model = None
                self.current_model_config = None
                self.model_name = None
                self.supports_system_role = False
                self.has_fixed_temperature = False
            else:
                print(f"Using default chat model key from environment: {model_key}")
                self.current_model = model_key
        else:
            print(f"Using provided chat model key: {model_key}")
            self.current_model = model_key

        # --- Determine Embedding Model Key ---
        if embedding_model_key is None:
            embedding_model_key = os.getenv("DEFAULT_EMBEDDING_MODEL_KEY")
            if embedding_model_key is None:
                # Allow initialization without an embedding model if only chat is needed
                print("Warning: Embedding model key not provided and DEFAULT_EMBEDDING_MODEL_KEY environment variable not set.")
                self.current_embedding_model = None
                self.embedding_model_config = None
                self.embedding_model_name = None
            else:
                print(f"Using default embedding model key from environment: {embedding_model_key}")
                self.current_embedding_model = embedding_model_key
        else:
            print(f"Using provided embedding model key: {embedding_model_key}")
            self.current_embedding_model = embedding_model_key

        if not self.current_model and not self.current_embedding_model:
             raise ValueError("Must provide configuration for at least a chat model or an embedding model.")

        # Initialize ModelManager to access configuration
        self.model_manager = ModelManager(config_path)

        # --- Load Chat Model Config (if provided) ---
        if self.current_model:
            self.current_model_config = self.model_manager.get_model_config(self.current_model)
            if not self.current_model_config:
                available_models = list(self.model_manager.available_models.keys())
                raise ValueError(f"Chat Model '{self.current_model}' not found in configuration. Available models: {available_models}")
            if self.current_model_config.get("provider") != "openai":
                raise ValueError(f"Chat Model '{self.current_model}' is not an OpenAI model. Provider: {self.current_model_config.get('provider')}")
            self.model_name = self.current_model_config["config"]["name"]
            self.supports_system_role = self.model_name not in self.MODELS_WITHOUT_SYSTEM_ROLE
            self.has_fixed_temperature = self.model_name in self.MODELS_WITH_FIXED_TEMPERATURE
            print(f"LLMInterface chat model configured: {self.model_name}")

        # --- Load Embedding Model Config (if provided) ---
        if self.current_embedding_model:
            self.embedding_model_config = self.model_manager.get_model_config(self.current_embedding_model)
            if not self.embedding_model_config:
                available_models = list(self.model_manager.available_models.keys())
                raise ValueError(f"Embedding Model '{self.current_embedding_model}' not found in configuration. Available models: {available_models}")
            if self.embedding_model_config.get("provider") != "openai":
                raise ValueError(f"Embedding Model '{self.current_embedding_model}' is not an OpenAI model. Provider: {self.embedding_model_config.get('provider')}")
            self.embedding_model_name = self.embedding_model_config["config"]["name"]
            print(f"LLMInterface embedding model configured: {self.embedding_model_name}")

        # --- Conditional Proxy Setup ---
        use_proxy_str = os.getenv('USE_LLM_PROXY', 'True').lower()
        print(f"[DEBUG] Raw USE_LLM_PROXY from os.getenv: '{os.getenv('USE_LLM_PROXY')}' -> Processed string: '{use_proxy_str}'")
        use_proxy = use_proxy_str == 'true'
        print(f"[DEBUG] Calculated use_proxy boolean: {use_proxy}")
        
        if use_proxy:
            print("Configuring OpenAI client to use proxy...")
            os.environ["HTTP_PROXY"] = self.OPENAI_PROXY["http"]
            os.environ["HTTPS_PROXY"] = self.OPENAI_PROXY["https"]
            # Note: The OpenAI client library often picks up these environment variables automatically.
            # If direct instantiation with proxy is needed, it would look like:
            # http_client = httpx.Client(proxies=self.OPENAI_PROXY)
            # self.client = OpenAI(api_key=self.current_model_config["api_key"], http_client=http_client)
        else:
            print("Configuring OpenAI client WITHOUT proxy...")
            # Ensure proxy variables are unset for this process if they existed before
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)
            # self.client = OpenAI(api_key=self.current_model_config["api_key"]) # Initialize without proxy client
        # --- End Conditional Proxy Setup ---

        # Initialize OpenAI client (will pick up env vars if set, otherwise direct connection)
        # Ensure API key exists in at least one of the selected models' config
        api_key = None
        if self.current_model_config:
            api_key = self.current_model_config.get("api_key")
        if not api_key and self.embedding_model_config:
            api_key = self.embedding_model_config.get("api_key")

        if not api_key:
            raise ValueError("No OpenAI API key found in the configuration for the selected model(s).")

        self.client = OpenAI(api_key=api_key)

    def generate_embedding(self, text: str, retry_attempts: int = 3, initial_delay: float = 1.0) -> Optional[List[float]]:
        """Generates an embedding for the given text using the configured embedding model.

        Args:
            text (str): The text to embed.
            retry_attempts (int): Number of times to retry on rate limit or server errors.
            initial_delay (float): Initial delay in seconds for exponential backoff.

        Returns:
            Optional[List[float]]: The embedding vector, or None if embedding fails after retries
                                   or if no embedding model is configured.
        """
        if not self.embedding_model_name:
            print("Error: No embedding model configured for LLMInterface.")
            return None

        # Replace newlines for OpenAI embedding model requirement
        text = text.replace("\n", " ")

        attempt = 0
        delay = initial_delay
        while attempt < retry_attempts:
            try:
                response = self.client.embeddings.create(
                    input=[text], # API expects a list of strings
                    model=self.embedding_model_name
                )
                # API returns a list of embeddings, get the first one
                embedding = response.data[0].embedding
                return embedding
            except RateLimitError as e:
                attempt += 1
                print(f"Rate limit error encountered. Retrying attempt {attempt}/{retry_attempts} after {delay:.2f}s... Error: {e}")
                time.sleep(delay)
                delay *= 2 # Exponential backoff
            except (APIError, APIConnectionError) as e:
                attempt += 1
                print(f"API error encountered. Retrying attempt {attempt}/{retry_attempts} after {delay:.2f}s... Error: {e}")
                time.sleep(delay)
                delay *= 2 # Exponential backoff
            except Exception as e:
                print(f"Unexpected error generating embedding: {e}")
                # Depending on policy, could retry here too or just raise/return None
                return None # Fail on unexpected errors for now

        print(f"Error: Failed to generate embedding for text after {retry_attempts} attempts.")
        return None

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Generate a response from the LLM using a simple prompt.
        
        For models that don't support system roles (like gpt-o1-mini), the system_prompt
        will be automatically converted and prepended to the user prompt.
        
        Args:
            prompt: The user's prompt to send to the model
            system_prompt: Optional system message to guide the model's behavior
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
                         Note: Some models only support the default temperature of 1.0
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Optional[str]: The model's response as a string, or None if generation fails.
        """
        if not self.model_name:
            print("Error: No chat model configured for LLMInterface.")
            return None
        messages = []
        
        if system_prompt:
            if self.supports_system_role:
                messages.append({"role": "system", "content": system_prompt})
            else:
                # For models that don't support system roles, prepend to user message
                prompt = f"[System instruction: {system_prompt}]\n\n{prompt}"
        
        messages.append({"role": "user", "content": prompt})
        
        return self.generate_chat_response(messages, temperature, max_tokens)
    
    def generate_chat_response(self, messages: List[Dict[str, str]],
                              temperature: float = 0.7,
                              max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Generate a response from the LLM using a conversation history.
        
        This method automatically adapts messages and parameters based on model limitations:
        - For models without system role support, system messages are converted to user messages
        - For models with fixed temperature, the temperature parameter is omitted
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
                         Note: Some models only support the default temperature of 1.0
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Optional[str]: The model's response as a string, or None if generation fails.
        """
        if not self.model_name:
            print("Error: No chat model configured for LLMInterface.")
            return None
        try:
            # For models without system role support, convert system messages to user messages
            if not self.supports_system_role:
                converted_messages = []
                system_instructions = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_instructions.append(msg["content"])
                    else:
                        converted_messages.append(msg)
                
                # If there were system messages, prepend them to the first user message
                if system_instructions and converted_messages:
                    for i, msg in enumerate(converted_messages):
                        if msg["role"] == "user":
                            system_text = "\n\n".join(system_instructions)
                            converted_messages[i]["content"] = f"[System instructions: {system_text}]\n\n{msg['content']}"
                            break
                
                messages = converted_messages
            
            # Prepare the request parameters
            params: Dict[str, Any] = {
                "model": self.model_name,
                "messages": messages
            }
            
            # Add temperature only for models that support it
            if not self.has_fixed_temperature:
                params["temperature"] = temperature
            
            # Add max_tokens if specified
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            
            print(f"Sending request to {self.model_name}...")
            response = self.client.chat.completions.create(**params)
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating chat response: {e}")
            return None

    def close(self):
        """
        Clean up resources when done with the interface.
        """
        # Current OpenAI client doesn't require explicit cleanup,
        # but including this method for future-proofing and consistency
        # with the resource management pattern
        pass


# Example usage
if __name__ == "__main__":
    try:
        # Initialize the interface - requires env vars or explicit keys
        # Assumes DEFAULT_LLM_MODEL_KEY and DEFAULT_EMBEDDING_MODEL_KEY are set in .env
        llm = LLMInterface()

        # Test chat completion (if chat model configured)
        if llm.model_name:
            print(f"\n--- Testing Chat Completion ({llm.model_name}) ---")
            chat_response = llm.generate_response(
                prompt="Hello, can you tell me a short fun fact?",
                temperature=0.7 # Will be ignored if model has fixed temperature
            )
            if chat_response:
                print("\nResponse to test prompt:")
                print(chat_response)
            else:
                print("\nChat completion failed.")
        else:
            print("\n--- Skipping Chat Completion Test (No chat model configured) ---")

        # Test embedding generation (if embedding model configured)
        if llm.embedding_model_name:
            print(f"\n--- Testing Embedding Generation ({llm.embedding_model_name}) ---")
            text_to_embed = "This is a sample text for embedding."
            print(f"Generating embedding for: \"{text_to_embed}\"")
            embedding = llm.generate_embedding(text_to_embed)

            if embedding:
                print(f"\nSuccessfully generated embedding vector of dimension: {len(embedding)}")
                print(f"First 5 dimensions: {embedding[:5]}")
            else:
                print("\nEmbedding generation failed.")
        else:
             print("\n--- Skipping Embedding Generation Test (No embedding model configured) ---")

    except Exception as e:
        print(f"Error in example usage: {e}")
        import traceback
        traceback.print_exc() 