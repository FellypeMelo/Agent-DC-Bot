# ai_handler.py
# Conexão com LM Studio e Lógica de IA

import logging
import os
import aiohttp
import asyncio
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class AIHandler:
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.api_url = os.getenv('LM_STUDIO_API_URL', 'http://localhost:1234/v1')
        self.model = config.get_config_value('ai_model')
        self.max_tokens = 2048
        self.temperature = 0.7
        self.timeout = 60

    async def generate_response(self, prompt, context=None, user_id=None):
        """Gera uma resposta usando o LM Studio com personalidade e contexto."""
        try:
            active_personality_name = self.config.get_config_value("active_personality_name", "default")
            personality = self.db.get_personality(active_personality_name)
            
            if not personality:
                if active_personality_name == "default":
                    # A personalidade padrão não existe, então vamos criá-la
                    default_desc = self.config.get_config_value("bot_personality")
                    self.db.create_personality("default", default_desc, "Sou um assistente prestativo e padrão.", "system")
                    personality = self.db.get_personality("default")
                else:
                    # A personalidade ativa não foi encontrada, reverte para a padrão
                    personality = self.db.get_personality("default")
                    if not personality:
                         # Se nem a padrão existir, cria
                        default_desc = self.config.get_config_value("bot_personality")
                        self.db.create_personality("default", default_desc, "Sou um assistente prestativo e padrão.", "system")
                        personality = self.db.get_personality("default")
                    self.config.set_config_value("active_personality_name", "default")

            system_prompt = f"Personalidade: {personality['description']}\nMemória Principal: {personality['core_memory']}"
            
            relationship_status = self.db.get_relationship(user_id)
            system_prompt += f"\nRelacionamento com o usuário: {relationship_status}"

            messages = [{"role": "system", "content": system_prompt}]
            
            if context:
                for msg in context:
                    role = "assistant" if msg.get("is_bot") else "user"
                    messages.append({"role": role, "content": msg.get("content", "")})
            
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return (await response.json())["choices"][0]["message"]["content"]
                    else:
                        logger.error(f"Erro na API: {response.status} - {await response.text()}")
                        return "Desculpe, ocorreu um erro ao contatar a IA."
        except asyncio.TimeoutError:
            logger.error("Timeout ao conectar com a API do LM Studio.")
            return "A IA está demorando muito para responder."
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return "Desculpe, ocorreu um erro inesperado."

    def detect_memory_triggers(self, message, memory):
        """Detecta gatilhos para armazenar informações na memória de longo prazo."""
        triggers = ["lembre-se", "memorize", "guarde", "anote", "salve"]
        message_lower = message.lower()
        for trigger in triggers:
            if trigger in message_lower:
                info_to_store = message.split(trigger, 1)[1].strip().lstrip("que de do da ")
                if info_to_store:
                    # Usando hashlib que já deve estar importado
                    import hashlib
                    key = f"user_info_{hashlib.md5(info_to_store.encode()).hexdigest()[:6]}"
                    memory.store_permanent_info(key, info_to_store)
                    logger.info(f"Informação '{info_to_store}' armazenada por gatilho.")
                    return True
        return False

    async def extract_and_memorize_facts(self, conversation_history, memory):
        """Usa a IA para extrair fatos estruturados da conversa e salvá-los."""
        if len(conversation_history) < 4:
            return

        prompt = (
            "Analise a conversa a seguir e extraia fatos importantes sobre o usuário. "
            "Formate cada fato como 'chave: valor', um por linha. "
            "Use chaves claras e concisas em inglês (ex: user_name, user_city, user_preference_music). "
            "Extraia apenas informações concretas e declaradas pelo usuário. "
            "Se nenhum fato novo for encontrado, responda com 'Nenhum fato novo'.\n\n"
            "Exemplo:\n"
            "Conversa:\n- Usuário: Olá, meu nome é Carlos e eu gosto de rock.\n"
            "Extração:\nuser_name: Carlos\nuser_preference_music: Rock\n\n"
            "--- FIM DO EXEMPLO ---\n\n"
            "Conversa para análise:\n"
        )
        user_messages = [msg['content'] for msg in conversation_history if not msg.get('is_bot')]
        if not user_messages:
            return
            
        prompt += "\n".join([f"- Usuário: {msg}" for msg in user_messages])

        extracted_text = await self.generate_response(prompt)

        if extracted_text and "nenhum fato novo" not in extracted_text.lower():
            facts = extracted_text.strip().split('\n')
            for fact in facts:
                if ':' in fact:
                    try:
                        key, value = [item.strip() for item in fact.split(':', 1)]
                        memory_key = f"fact_{key.replace(' ', '_')}"
                        memory.store_permanent_info(memory_key, value)
                        logger.info(f"Fato estruturado salvo: {memory_key}: {value}")
                    except ValueError:
                        logger.warning(f"Não foi possível processar o fato extraído: '{fact}'")

    async def analyze_and_update_relationship(self, user_id, conversation_history):
        """Analisa a conversa e atualiza o status de relacionamento com o usuário."""
        if len(conversation_history) < 5:
            return

        current_status = self.db.get_relationship(user_id)

        user_messages = [msg['content'] for msg in conversation_history if not msg.get('is_bot')]
        if not user_messages:
            return

        prompt = (
            f"Analise o tom e o conteúdo das mensagens do usuário e classifique o relacionamento dele com o bot. "
            f"O status atual do relacionamento é '{current_status}'.\n"
            "Escolha UM dos seguintes status: [Desconhecido, Amigável, Curioso, Formal, Hostil].\n"
            "Responda apenas com a palavra do status escolhido.\n\n"
            "Mensagens do usuário:\n"
        )
        prompt += "\n".join([f"- {msg}" for msg in user_messages])

        new_status = await self.generate_response(prompt)

        # Validação simples da resposta da IA
        valid_statuses = ["Desconhecido", "Amigável", "Curioso", "Formal", "Hostil"]
        final_status = new_status.strip().capitalize()

        if final_status in valid_statuses and final_status != current_status:
            self.db.update_relationship(user_id, final_status)
            logger.info(f"Relacionamento com usuário {user_id} atualizado para '{final_status}'.")
