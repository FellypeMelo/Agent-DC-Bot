# ai_handler.py
# Conexão com LM Studio

import requests
import json
import logging
import os
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do logger
logger = logging.getLogger(__name__)

class AIHandler:
    def __init__(self, config):
        self.config = config
        self.api_url = os.getenv('LM_STUDIO_API_URL', 'http://localhost:1234/v1')
        self.model = config.get_config_value('ai_model')
        self.max_tokens = 2048  # Valor padrão
        self.temperature = 0.7  # Valor padrão
        self.timeout = 30  # Timeout para requisições em segundos
        
        # Cache simples para respostas frequentes
        self.response_cache = {}
        self.cache_size = 50  # Tamanho máximo do cache
        self.cache_enabled = True
        
    def set_model_params(self, max_tokens=None, temperature=None):
        """Define parâmetros do modelo de IA"""
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature
        
    async def generate_response(self, prompt, personality=None, context=None):
        """Gera uma resposta usando o LM Studio com cache e timeout"""
        try:
            # Prepara o contexto para o modelo
            messages = []

            # Adiciona a personalidade como uma instrução de sistema (se existir)
            if personality:
                system_prompt = (
                    f"{personality}\n\n"
                    "**Diretriz de Roleplay:** Use formatação Markdown (*itálico* para pensamentos e sussuros, "
                    "**negrito** para ações e ênfase) para tornar suas respostas mais imersivas e expressivas."
                )
                messages.append({"role": "system", "content": system_prompt})
            
            # Adiciona contexto se fornecido
            if context:
                # Registra informações sobre o contexto para depuração
                logger.debug(f"Contexto recebido: {len(context)} mensagens")
                logger.debug(f"Memória de longo prazo: {sum(1 for msg in context if msg.get('is_memory', False))} itens")
                
                for msg in context:
                    # Determina o papel da mensagem no contexto
                    if msg.get("user_id") == "system" and msg.get("is_memory", False):
                        # Mensagens de memória de longo prazo são tratadas como informações do sistema
                        role = "system"
                        logger.debug(f"Memória de longo prazo incluída: {msg.get('content', '')[:50]}...")
                    else:
                        # Outras mensagens são do assistente ou do usuário
                        role = "assistant" if msg.get("is_bot", False) else "user"
                    
                    messages.append({
                        "role": role,
                        "content": msg.get("content", "")
                    })
            
            # Adiciona a mensagem atual
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Gera uma chave de cache baseada no prompt e contexto
            cache_key = self._generate_cache_key(prompt, context)
            
            # Verifica se a resposta está no cache
            if self.cache_enabled and cache_key in self.response_cache:
                logger.info(f"Resposta obtida do cache para: {prompt[:30]}...")
                return self.response_cache[cache_key]
            
            # Prepara os dados para a API
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            # Faz a requisição para a API com timeout usando aiohttp (assíncrono)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        # Armazena no cache se estiver habilitado
                        if self.cache_enabled:
                            self._update_cache(cache_key, content)
                            
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"Erro na API do LM Studio: {response.status} - {error_text}")
                        return "Desculpe, ocorreu um erro ao processar sua mensagem."
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout ao conectar com a API do LM Studio após {self.timeout} segundos")
            return "Desculpe, a resposta está demorando muito. Por favor, tente novamente."
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return "Desculpe, ocorreu um erro ao processar sua mensagem."
    
    def _generate_cache_key(self, prompt, context=None):
        """Gera uma chave única para o cache baseada no prompt e contexto"""
        # Cria uma string simples para representar o contexto
        context_str = ""
        if context:
            # Usa apenas as últimas 3 mensagens do contexto para a chave
            for msg in context[-3:]:
                role = "assistant" if msg.get("is_bot", False) else "user"
                content = msg.get("content", "")[:50]  # Limita o tamanho
                context_str += f"{role}:{content[:50]}|"  # Trunca para manter a chave pequena
        
        # Combina prompt e contexto para a chave
        key_base = f"{prompt[:100]}|{context_str}"
        
        # Usa um hash para garantir tamanho fixo da chave
        import hashlib
        return hashlib.md5(key_base.encode('utf-8')).hexdigest()
    
    def _update_cache(self, key, content):
        """Atualiza o cache com uma nova resposta"""
        # Adiciona ao cache
        self.response_cache[key] = content
        
        # Se o cache excedeu o tamanho máximo, remove os itens mais antigos
        if len(self.response_cache) > self.cache_size:
            # Remove o primeiro item (o mais antigo em um dict ordenado por inserção)
            self.response_cache.pop(next(iter(self.response_cache)))
            
        logger.debug(f"Cache atualizado. Tamanho atual: {len(self.response_cache)}")
    
    def process_response(self, response):
        """Processa a resposta do modelo para melhorar a inteligibilidade"""
        # Aqui podem ser adicionadas regras para melhorar a resposta
        # Por exemplo, remover repetições, corrigir formatação, etc.
        return response
        
    def detect_memory_triggers(self, message, memory):
        """Detecta gatilhos para armazenar informações na memória de longo prazo"""
        # Lista de gatilhos que indicam que o usuário quer que o bot lembre de algo
        memory_triggers = [
            "lembre-se", "lembre se", "memorize", "guarde", "não esqueça", 
            "anote", "grave", "registre", "salve", "armazene"
        ]
        
        # Verifica se a mensagem contém algum dos gatilhos
        message_lower = message.lower()
        triggered = False
        trigger_used = None
        
        for trigger in memory_triggers:
            if trigger in message_lower:
                triggered = True
                trigger_used = trigger
                break
                
        if not triggered:
            return False
            
        # Extrai a informação que deve ser armazenada
        # Procura pelo gatilho e pega o texto após ele
        trigger_index = message_lower.find(trigger_used)
        if trigger_index >= 0:
            # Pega o texto após o gatilho
            info_to_store = message[trigger_index + len(trigger_used):].strip()
            
            # Remove palavras como "que", "de", "do", "da" no início da informação
            info_to_store = info_to_store.lstrip("que de do da dos das ").strip()
            
            # Se a informação não estiver vazia, armazena na memória de longo prazo
            if info_to_store:
                # Gera uma chave baseada no conteúdo da informação
                import hashlib
                key = f"user_info_{hashlib.md5(info_to_store.encode('utf-8')).hexdigest()[:8]}"
                
                # Armazena a informação na memória de longo prazo
                memory.store_permanent_info(key, info_to_store)
                logger.info(f"Informação armazenada na memória de longo prazo: {info_to_store}")
                return True
                
        return False

    # O método _generate_response foi removido por ser redundante
    # Agora todas as chamadas usam diretamente o método generate_response

    async def analyze_search_results(self, results, query):
        """Analisa os resultados da busca usando a IA"""
        try:
            # Formata os resultados para o prompt incluindo o conteúdo das páginas
            formatted_results = []
            for i, res in enumerate(results[:3]):
                try:
                    # Tenta fazer o web scraping da página com headers personalizados
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(res['link'], headers=headers, timeout=10) as response:
                            if response.status == 200:
                                html = await response.text()
                                # Extrai o texto principal usando BeautifulSoup
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Remove elementos irrelevantes
                                for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'form', 'button']):
                                    tag.decompose()
                                    
                                # Encontra o conteúdo principal
                                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=['content', 'main', 'article'])
                                if main_content:
                                    text = main_content.get_text(separator='\n', strip=True)
                                else:
                                    text = soup.get_text(separator='\n', strip=True)
                                
                                # Limpa o texto
                                text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                                
                                # Limita o tamanho do texto mantendo parágrafos completos
                                if len(text) > 500:
                                    paragraphs = text.split('\n')
                                    text = '\n'.join(paragraphs[:5])  # Mantém os 5 primeiros parágrafos
                                    text = text[:500] + '...'
                            else:
                                text = res.get('snippet', '')
                except Exception as e:
                    logger.warning(f"Erro ao fazer scraping de {res['link']}: {e}")
                    text = res.get('snippet', '')
                
                # Formata o resultado de forma mais concisa
                formatted_results.append(
                    f"[{i+1}] {res['title']}\n"
                    f"URL: {res['link']}\n"
                    f"Resumo:\n{text}\n"
                )

            # Limita o tamanho total do texto formatado
            formatted_text = '\n---\n'.join(formatted_results)
            
            # Cria um prompt focado em responder diretamente à pergunta
            prompt = (
                f"Com base nas informações a seguir, responda diretamente à pergunta: '{query}'\n\n"
                f"{formatted_text}\n\n"
                "Diretriz: Forneça uma resposta direta e objetiva à pergunta usando apenas as informações encontradas.\n"
                "Não mencione fontes, URLs ou metadados.\n"
                "Se não encontrar uma resposta clara nos textos fornecidos, responda 'Desculpe, não encontrei uma resposta precisa para sua pergunta.'\n"
                "Mantenha a resposta concisa e focada especificamente na pergunta feita."
            )

            response = await self.generate_response(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Erro na análise de resultados: {e}")
            return "Não foi possível analisar os resultados no momento."