from bot_discord.core.logger import setup_logger


def test_setup_logger_returns_named_logger():
    logger = setup_logger("test.logger")
    assert logger.name == "test.logger"
