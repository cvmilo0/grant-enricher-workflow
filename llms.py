from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_core.runnables.config import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import tiktoken
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from dotenv import load_dotenv
from langsmith import traceable
load_dotenv()

# Language Models
class LanguageModel:
    _openrouter_language_models = [
        "mistral/ministral-8b",
        "meta-llama/llama-3.3-70b-instruct",
        "qwen/qwen-2.5-72b-instruct",
        "deepseek/deepseek-chat-v3-0324:free",
        "google/gemini-2.0-flash-001"
        "anthropic/claude-3-haiku",
        "mistralai/mistral-medium"
    ]

    _deepseek_language_models = [
        "deepseek-chat"
    ]

    _openai_language_models = [
        "gpt-4o-mini",
        "gpt-4o"
    ]

    _gemini_language_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash-8b",
        "gemini-2.0-flash-lite"
    ]

    _huggingface_language_models = [
        "deepseek-ai/DeepSeek-R1",
        "meta-llama/Llama-3.1-8B-Instruct",
        "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "Qwen/QwQ-32B",
        "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
    ]
    
                    
    def __init__(self, model_name: str):
        self.model_name = model_name  # Store model name
        if model_name in self._openrouter_language_models:
            self.model = ChatOpenAI(
                model_name=model_name,
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
            )
        elif model_name in self._openai_language_models:
            self.model = ChatOpenAI(
                model_name=model_name,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                openai_api_base=os.getenv("OPENAI_API_BASE"),
            )
        elif model_name in self._gemini_language_models:
            self.model = ChatGoogleGenerativeAI(
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                model=model_name,
            )
        elif model_name in self._huggingface_language_models:
            self.model = ChatHuggingFace(
                llm=HuggingFaceEndpoint(
                    repo_id=model_name,
                    task="text-generation"
                ),
                verbose=True
            )
        elif model_name in self._deepseek_language_models:
            self.model = ChatDeepSeek(
                model=model_name,
                api_key=os.getenv("DEEPSEEK_API_KEY")            
                )
        else:
            raise ValueError(f"Model {model_name} not found")

    def _count_tokens(self, text: str) -> int:
        """Counts tokens using tiktoken with a default encoding."""
        # Using cl100k_base as a common default. Specific models might need different encodings.
        try:
            encoding = tiktoken.get_encoding("cl100k_base") 
            return len(encoding.encode(text))
        except Exception as e:
            print(f"Could not count tokens: {e}")
            # Fallback or error handling - returning 0 or raising might be options
            return 0 

    @traceable(name="language_model_invoke_with_tokens")
    def invoke(self, input, config: RunnableConfig | None = None) -> dict:
        """
        Invokes the underlying language model and counts input/output tokens.

        Args:
            input: The input messages for the model (usually a list of BaseMessage).
            config: Optional RunnableConfig for the invocation.

        Returns:
            A dictionary containing the model's response and token usage.
            e.g., {"response": AIMessage(...), "token_usage": {"input_tokens": 100, "output_tokens": 50}}
        """
        input_tokens = 0
        # LangChain inputs can be dicts or lists of messages. Handle list case.
        if isinstance(input, list):
             for message in input:
                 # Assuming messages have a 'content' attribute
                 if hasattr(message, 'content') and isinstance(message.content, str):
                     input_tokens += self._count_tokens(message.content)
                 # Handle cases where content might be structured (e.g., vision models) - basic string conversion for now
                 elif hasattr(message, 'content'):
                      try:
                          input_tokens += self._count_tokens(str(message.content))
                      except Exception:
                          # Add more robust handling if needed
                          pass 
        elif isinstance(input, str): # Handle plain string input
            input_tokens += self._count_tokens(input)
        # Add handling for other potential input types if necessary

        # Invoke the actual model
        response = self.model.invoke(input, config=config)

        # Count output tokens
        output_tokens = 0
        if hasattr(response, 'content') and isinstance(response.content, str):
             output_tokens = self._count_tokens(response.content)

        token_usage = [
            {
                "model_name": self.model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        ]

        return response, token_usage