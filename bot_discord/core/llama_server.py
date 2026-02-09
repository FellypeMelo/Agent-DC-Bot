import subprocess
import logging
import asyncio
import aiohttp
import time
import os
import shlex
import sys

logger = logging.getLogger(__name__)

class LlamaServerManager:
    def __init__(self, config):
        self.config = config
        self.process = None
        self.server_path = config.get_config_value("llama_server_path", "llama-server.exe")
        self.model_path = config.get_config_value("model_path", "model.gguf")
        self.host = config.get_config_value("llama_server_host", "127.0.0.1")
        self.port = config.get_config_value("llama_server_port", 8080)
        self.flags = config.get_config_value("llama_server_flags", "-c 4096")
        self.api_url = f"http://{self.host}:{self.port}"
        self._log_file = None

    def start(self):
        """Inicia o servidor Llama.cpp em um subprocesso."""
        if self.is_running():
            logger.warning("Llama Server já está rodando.")
            return

        cmd = [
            self.server_path,
            "-m", self.model_path,
            "--host", self.host,
            "--port", str(self.port)
        ]

        # Parse flags string into list safely
        if self.flags:
            # On Windows, shlex might behave differently with paths,
            # but flags are usually simple.
            try:
                args = shlex.split(self.flags, posix=(os.name != 'nt'))
                cmd.extend(args)
            except Exception as e:
                logger.error(f"Erro ao processar flags: {e}")

        logger.info(f"Iniciando Llama Server: {' '.join(cmd)}")

        try:
            self._log_file = open("llama_server.log", "w")

            # On Windows, we might want to hide the window or show it.
            # Defaulting to no new console (hidden) but logging to file.
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                # startupinfo.wShowWindow = subprocess.SW_HIDE # Uncomment to hide completely if needed

            self.process = subprocess.Popen(
                cmd,
                stdout=self._log_file,
                stderr=subprocess.STDOUT,
                # startupinfo=startupinfo # Let's stick to default for now to avoid complexity unless requested
            )
            logger.info(f"Llama Server iniciado com PID: {self.process.pid}")
        except FileNotFoundError:
            logger.error(f"Executável não encontrado: {self.server_path}")
            print(f"ERRO: Não foi possível encontrar {self.server_path}. Verifique o caminho no .env")
        except Exception as e:
            logger.error(f"Erro ao iniciar Llama Server: {e}")

    def stop(self):
        """Para o servidor."""
        if self.process:
            logger.info("Parando Llama Server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            logger.info("Llama Server parado.")

        if self._log_file:
            self._log_file.close()
            self._log_file = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    async def wait_for_ready(self, timeout=60):
        """Aguarda o servidor estar pronto para aceitar requisições."""
        start_time = time.time()
        logger.info(f"Aguardando Llama Server em {self.api_url}...")

        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < timeout:
                try:
                    # Check /health (some versions) or /v1/models (standard)
                    async with session.get(f"{self.api_url}/health", timeout=1) as resp:
                        if resp.status == 200:
                            logger.info("Llama Server está pronto (health check)!")
                            return True
                except:
                    pass

                try:
                    # Fallback to checking models if health endpoint doesn't exist
                    async with session.get(f"{self.api_url}/v1/models", timeout=1) as resp:
                        if resp.status == 200:
                            logger.info("Llama Server está pronto (models check)!")
                            return True
                except:
                    pass

                # Check process status
                if self.process and self.process.poll() is not None:
                    logger.error(f"Llama Server morreu com código de saída {self.process.returncode}.")
                    return False

                await asyncio.sleep(1)

        logger.error("Timeout aguardando Llama Server.")
        return False
