# ai_handler.py
import logging
import os
import json
from core.llm_provider import LMStudioProvider

logger = logging.getLogger(__name__)

class AIHandler:
    def __init__(self, config):
        self.config = config
        
        # EXCLUSIVE LM-STUDIO CONFIGURATION
        api_url = os.getenv('LM_STUDIO_API_URL', 'http://localhost:1234/v1')
        model = os.getenv('AI_MODEL', 'ministral-3:3b')
        
        self.provider = LMStudioProvider(api_url, model)
        logger.info(f"LLM Backend: LM-STUDIO | URL: {api_url} | Model: {model}")

    async def initialize(self):
        """Verifica apenas se o LM-Studio está acessível."""
        api_url = self.provider.api_url
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                # Usa /v1/models como health check (padrão OpenAI)
                async with session.get(f"{api_url}/models", timeout=2) as response:
                    if response.status == 200:
                        logger.info("Conexão com LM-Studio estabelecida com sucesso.")
                    else:
                        logger.warning(f"LM-Studio respondeu com status: {response.status}")
        except Exception as e:
            logger.error(f"Não foi possível conectar ao LM-Studio em {api_url}. Verifique se o servidor está ligado!")

    def _trim_context(self, messages, max_tokens=12000):
        """Mantém o contexto dentro do limite para evitar estouro de memória."""
        if len(messages) <= 10:
            return messages
        system_msg = [m for m in messages if m['role'] == 'system']
        chat_msgs = [m for m in messages if m['role'] != 'system']
        return system_msg + chat_msgs[-14:] 

    async def generate_response(self, prompt, personality=None, context=None, temperature=0.7, top_p=0.95):
        messages = []
        if personality:
            messages.append({"role": "system", "content": personality})
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})
        messages = self._trim_context(messages)
        return await self.provider.generate(messages, temperature=temperature, top_p=top_p)

    async def generate_response_stream(self, prompt, personality=None, context=None):
        messages = []
        if personality:
            messages.append({"role": "system", "content": personality})
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})
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

    async def generate_voice_dna_instruction(self, persona_description):
        """
        Gera uma instrução acústica detalhada para o Qwen-TTS baseado na persona.
        """
        prompt = (
            "Com base na descrição de personalidade abaixo, crie uma instrução de voz concisa (máximo 20 palavras) "
            "em português para um sintetizador de voz. Foque no tom, velocidade e características vocais.\n\n"
            f"Persona: {persona_description}\n"
            "Instrução de Voz:"
        )
        try:
            response = await self.provider.generate([{"role": "user", "content": prompt}], max_tokens=64)
            return response.strip().replace('"', '')
        except Exception as e:
            logger.error(f"Erro ao gerar DNA de voz: {e}")
            return "Voz natural, amigável e clara."