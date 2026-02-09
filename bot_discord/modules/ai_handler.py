# ai_handler.py
import logging
import os
import json
from core.llm_provider import LMStudioProvider, OllamaProvider, LlamaCppProvider

logger = logging.getLogger(__name__)

class AIHandler:
    def __init__(self, config):
        self.config = config
        
        backend = config.get_config_value("llm_backend", "lm_studio")
        
        if backend == "llama_cpp":
            host = config.get_config_value("llama_server_host", "127.0.0.1")
            port = config.get_config_value("llama_server_port", 8080)
            api_url = f"http://{host}:{port}/v1"
            model = "local-model" # llama-server usually doesn't care about model name in path
            self.provider = LlamaCppProvider(api_url, model)
        elif backend == "ollama":
            api_url = config.get_config_value("ollama_api_url", "http://localhost:11434/v1")
            model = config.get_config_value("ollama_model", "ministral-3:3b")
            self.provider = OllamaProvider(api_url, model)
        else: # Default or LM Studio
            api_url = config.get_config_value("lm_studio_api_url", "http://localhost:1234/v1")
            model = config.get_config_value("ai_model", "ministral-3:3b")
            self.provider = LMStudioProvider(api_url, model)
            
        logger.info(f"LLM Backend: {self.provider.name} | URL: {self.provider.api_url} | Model: {self.provider.model}")

    async def initialize(self):
        """Verifica se o provedor selecionado está acessível."""
        api_url = self.provider.api_url
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api_url}/models", timeout=2) as response:
                    if response.status == 200:
                        logger.info(f"Conexão com {self.provider.name} estabelecida com sucesso.")
                    else:
                        logger.warning(f"{self.provider.name} respondeu com status: {response.status}")
        except Exception:
            logger.error(f"Não foi possível conectar ao {self.provider.name} em {api_url}. Verifique se o servidor está ligado!")

    def _trim_context(self, messages, max_tokens=12000):
        """Mantém o contexto dentro do limite para evitar estouro de memória."""
        if len(messages) <= 10:
            return messages
        system_msg = [m for m in messages if m['role'] == 'system']
        chat_msgs = [m for m in messages if m['role'] != 'system']
        return system_msg + chat_msgs[-14:]

    def _sanitize_context(self, messages):
        """
        Garante que não existam mensagens consecutivas do mesmo role.
        Mescla mensagens consecutivas do mesmo autor.
        """
        if not messages:
            return []
            
        sanitized = []
        for msg in messages:
            if not sanitized:
                sanitized.append(msg)
                continue
                
            last_msg = sanitized[-1]
            if last_msg['role'] == msg['role']:
                last_msg['content'] += f"\n\n{msg['content']}"
            else:
                sanitized.append(msg)
                
        return sanitized

    async def generate_response(self, prompt, personality=None, context=None, temperature=0.7, top_p=0.95):
        messages = []
        if personality:
            messages.append({"role": "system", "content": personality})
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})
        messages = self._sanitize_context(messages)
        messages = self._trim_context(messages)
        return await self.provider.generate(messages, temperature=temperature, top_p=top_p)

    async def generate_response_stream(self, prompt, personality=None, context=None):
        messages = []
        if personality:
            messages.append({"role": "system", "content": personality})
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})
        messages = self._sanitize_context(messages)
        messages = self._trim_context(messages)
        async for chunk in self.provider.generate_stream(messages):
            yield chunk

    async def detect_memory_triggers(self, text, memory_module, user_id):
        extract_prompt = (
            "Analise a frase do usuário e extraia fatos importantes sobre ele. "
            "Responda APENAS com um array JSON de strings. Exemplo: ['O usuário gosta de pizza'].\n\n"
            f"Frase: '{text}'"
        )
        try:
            response = await self.provider.generate([{"role": "user", "content": extract_prompt}], max_tokens=128)
            clean_response = response.strip()
            if "[" in clean_response and "]" in clean_response:
                clean_response = clean_response[clean_response.find("["):clean_response.rfind("]")+1]
            facts = json.loads(clean_response)
            if isinstance(facts, list) and facts:
                for fact in facts:
                    await memory_module.add_memory(user_id, fact)
                return True
        except:
            pass
        return False

    def extract_sentiment(self, text: str):
        import re
        match = re.search(r"\[([A-Z]+)\]", text)
        if match:
            sentiment = match.group(1).lower()
            cleaned_text = re.sub(r"\[[A-Z]+\]", "", text).strip()
            return cleaned_text, sentiment
        return text, "neutral"

    async def summarize_history(self, history):
        if not history: return ""
        text = "Resuma a conversa abaixo em um parágrafo curto:\n\n"
        for m in history:
            text += f"{m['role']}: {m['content']}\n"
        return await self.provider.generate([{"role": "user", "content": text}], max_tokens=256)