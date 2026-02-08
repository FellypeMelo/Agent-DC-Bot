from datetime import datetime

from bot_discord.modules.time_handler import TimeHandler


class ConfigStub:
    def get_config_value(self, key, default=None):
        return default


def test_time_context_values(monkeypatch):
    handler = TimeHandler(ConfigStub())
    fixed = datetime(2024, 5, 6, 10, 30)
    monkeypatch.setattr(handler, "get_current_time", lambda: fixed)

    context = handler.get_time_context()
    assert context["weekday"] == "segunda-feira"
    assert context["time_of_day"] == "manhã"
    assert context["is_weekend"] == "False"


def test_add_and_remove_special_date(tmp_path):
    handler = TimeHandler(ConfigStub())
    handler.special_dates_file = tmp_path / "special_dates.json"

    assert handler.add_special_date("Teste", "10/12/2024") is True
    assert handler.remove_special_date("Teste") is True
