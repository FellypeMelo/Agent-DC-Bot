import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add bot_discord directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.llama_server import LlamaServerManager
from core.config import Config

class TestLlamaServerManager(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock(spec=Config)
        self.config.get_config_value.side_effect = lambda key, default=None: default or {
            "llama_server_path": "llama-server.exe",
            "model_path": "model.gguf",
            "llama_server_host": "127.0.0.1",
            "llama_server_port": 8080,
            "llama_server_flags": "-c 4096"
        }.get(key)

        self.manager = LlamaServerManager(self.config)

    @patch('subprocess.Popen')
    def test_start_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Prevent open() from creating a real file
        with patch('builtins.open', new_callable=MagicMock):
            self.manager.start()

        self.assertTrue(self.manager.is_running())
        mock_popen.assert_called_once()

        args, kwargs = mock_popen.call_args
        cmd = args[0]
        self.assertIn("llama-server.exe", cmd)
        self.assertIn("-m", cmd)

    @patch('subprocess.Popen')
    def test_stop(self, mock_popen):
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        self.manager.process = mock_process

        mock_file = MagicMock()
        self.manager._log_file = mock_file

        self.manager.stop()

        mock_process.terminate.assert_called_once()
        mock_file.close.assert_called_once() # Check the mock directly
        self.assertIsNone(self.manager.process)
        self.assertIsNone(self.manager._log_file)

if __name__ == '__main__':
    unittest.main()
