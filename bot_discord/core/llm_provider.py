# llm_provider.py
from abc import ABC, abstractmethod
import aiohttp
import logging
import os
import json

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages, temperature=0.7, max_tokens=2048):
        pass

    @abstractmethod
    async def generate_stream(self, messages, temperature=0.7, max_tokens=2048):
        pass

class LMStudioProvider(LLMProvider):
    def __init__(self, api_url, model):
        self.api_url = api_url
        self.model = model
        self._session = None
        self.metrics = {"latency": [], "total_requests": 0, "errors": 0}

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def generate(self, messages, temperature=0.7, max_tokens=2048, top_p=0.95, frequency_penalty=0.0):
        import time
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty
        }
        session = await self._get_session()
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        try:
            async with session.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                timeout=120
            ) as response:
                latency = time.time() - start_time
                self.metrics["latency"].append(latency)
                
                if response.status == 200:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    logger.info(f"LLM Success | Latency: {latency:.2f}s")
                    return content
                else:
                    self.metrics["errors"] += 1
                    error_text = await response.text()
                    logger.error(f"LM Studio Error {response.status}: {error_text}")
                    return f"Erro no servidor LM Studio (Status: {response.status})"
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"LLM Connection Error: {e}")
            return "Erro de conexão com o servidor local de IA."

    async def generate_stream(self, messages, temperature=0.7, max_tokens=2048, top_p=0.95):
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": True
        }
        session = await self._get_session()
        try:
            async with session.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                timeout=120
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            if line == 'data: [DONE]':
                                break
                            try:
                                chunk = json.loads(line[6:])
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except:
                                continue
                else:
                    logger.error(f"Stream Error: {response.status}")
                    yield f"Erro no streaming: {response.status}"
        except Exception as e:
            logger.error(f"Stream Connection Error: {e}")
            yield "Erro de conexão no stream."