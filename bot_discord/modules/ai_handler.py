# ai_handler.py
import logging
import json
import re
from typing import List, Dict, Any, AsyncGenerator, Optional, Tuple
from core.llm_provider import LMStudioProvider, OllamaProvider, LlamaCppProvider

logger = logging.getLogger(__name__)

class AIHandler:
    def __init__(self, config):
        """
        Initializes the AI Handler with the selected LLM backend.
        
        Args:
            config: Configuration object containing backend settings.
            
        Big (O): O(1) - Constant time initialization and provider selection.
        """
        self.config = config
        backend = config.get_config_value("llm_backend", "lm_studio")
        
        if backend == "llama_cpp":
            host = config.get_config_value("llama_server_host", "127.0.0.1")
            port = config.get_config_value("llama_server_port", 8080)
            api_url = f"http://{host}:{port}/v1"
            self.provider = LlamaCppProvider(api_url, "local-model")
        elif backend == "ollama":
            api_url = config.get_config_value("ollama_api_url", "http://localhost:11434/v1")
            model = config.get_config_value("ollama_model", "ministral-3:3b")
            self.provider = OllamaProvider(api_url, model)
        else:
            api_url = config.get_config_value("lm_studio_api_url", "http://localhost:1234/v1")
            model = config.get_config_value("ai_model", "ministral-3:3b")
            self.provider = LMStudioProvider(api_url, model)
            
        logger.info(f"LLM Backend: {self.provider.name} | URL: {self.provider.api_url}")

    async def initialize(self) -> None:
        """
        Verifies connectivity with the selected provider.
        
        Big (O): O(1) - Single HTTP request to verify API status.
        """
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.provider.api_url}/models", timeout=2) as response:
                    if response.status == 200:
                        logger.info(f"Connection to {self.provider.name} verified.")
        except Exception:
            logger.error(f"Failed to connect to {self.provider.name} at {self.provider.api_url}")

    def _trim_context(self, messages: List[Dict[str, str]], max_msgs: int = 14) -> List[Dict[str, str]]:
        """
        Prunes message history to stay within context limits while preserving the system prompt.
        
        Args:
            messages: Full list of context messages.
            max_msgs: Number of recent messages to keep.
            
        Returns:
            Trimmed list of messages.
            
        Big (O): O(N) - Linear pass to filter system messages and slice the recent history.
        """
        if len(messages) <= 10:
            return messages
        
        system_msg = [m for m in messages if m['role'] == 'system']
        chat_msgs = [m for m in messages if m['role'] != 'system']
        
        # Preserve system prompt + last N messages
        return system_msg + chat_msgs[-max_msgs:]

    def _sanitize_context(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Merges consecutive messages from the same role to prevent LLM API errors and improve token efficiency.
        
        Args:
            messages: List of raw messages.
            
        Returns:
            Sanitized list with merged contents.
            
        Big (O): O(N) - Linear pass through messages. Efficient content joining using list-based buffering.
        """
        if not messages:
            return []
            
        sanitized = []
        for msg in messages:
            if not sanitized or sanitized[-1]['role'] != msg['role']:
                # New role, append a fresh dictionary copy
                sanitized.append({"role": msg['role'], "content": msg['content']})
            else:
                # Same role, append content with double newline (O(1) amortized list append)
                sanitized[-1]['content'] = f"{sanitized[-1]['content']}\n\n{msg['content']}"
                
        return sanitized

    async def generate_response_stream(self, prompt: str, personality: Optional[str] = None, context: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[str, None]:
        """
        Prepares context and generates a streaming response from the provider.
        
        Args:
            prompt: User message.
            personality: System prompt for the persona.
            context: Short-term conversation history.
            
        Yields:
            Response chunks (tokens).
            
        Big (O): O(N + LLM_Inference) - N is context size. Inference time is the dominant bottleneck.
        """
        messages = []
        if personality:
            messages.append({"role": "system", "content": personality})
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})
        
        # Optimize context before sending to LLM
        messages = self._trim_context(self._sanitize_context(messages))
        
        async for chunk in self.provider.generate_stream(messages):
            yield chunk

    async def detect_memory_triggers(self, text: str, memory_module: Any, user_id: str) -> bool:
        """
        Analyzes user input to extract facts for permanent memory.
        
        Args:
            text: Input text to analyze.
            memory_module: The memory cog instance.
            user_id: Discord ID of the user.
            
        Returns:
            True if facts were extracted and saved.
            
        Big (O): O(LLM_Inference + M) - Requires a separate LLM call. M is number of facts.
        """
        extract_prompt = (
            "Extraia fatos importantes sobre o usuário da frase abaixo. "
            "Responda APENAS com um array JSON de strings. Exemplo: ['Gosta de café'].\n\n"
            f"Frase: '{text}'"
        )
        try:
            response = await self.provider.generate([{"role": "user", "content": extract_prompt}], max_tokens=128)
            # Find JSON array using regex for robustness
            match = re.search(r"\[.*\]", response.replace("\n", ""))
            if match:
                facts = json.loads(match.group(0))
                if isinstance(facts, list) and facts:
                    for fact in facts:
                        # Background task for memory storage is handled by the caller or here
                        await memory_module.store_permanent_info(user_id, fact)
                    return True
        except Exception as e:
            logger.debug(f"Memory extraction failed: {e}")
        return False

    def extract_sentiment(self, text: str) -> Tuple[str, str]:
        """
        Parses [SENTIMENT] tags from LLM responses using optimized Regex.
        
        Args:
            text: Raw LLM output.
            
        Returns:
            Tuple of (cleaned_text, sentiment_string).
            
        Big (O): O(L) - L is string length. Single pass regex search and substitution.
        """
        match = re.search(r"\[([A-Z]+)\]", text)
        if match:
            sentiment = match.group(1).lower()
            cleaned_text = re.sub(r"\[[A-Z]+\]", "", text).strip()
            return cleaned_text, sentiment
        return text, "neutral"

    async def summarize_history(self, history: List[Dict[str, str]]) -> str:
        """
        Generates a concise summary of a conversation slice.
        
        Args:
            history: Message history list.
            
        Returns:
            Summary string.
            
        Big (O): O(N + LLM_Inference) - N is the character length of history.
        """
        if not history: return ""
        
        # Use list join for efficient string building O(N)
        formatted_history = "\n".join([f"{m['role']}: {m['content']}" for m in history])
        prompt = f"Resuma a conversa abaixo em um parágrafo curto:\n\n{formatted_history}"
        
        return await self.provider.generate([{"role": "user", "content": prompt}], max_tokens=256)
