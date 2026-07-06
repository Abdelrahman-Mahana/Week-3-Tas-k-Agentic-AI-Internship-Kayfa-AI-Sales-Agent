"""Unit tests for CRM ticket extraction helpers."""

from unittest.mock import MagicMock
from agent.graph import _build_conversation_text, _extract_crm_fields


def test_build_conversation_text_includes_user_message():
    history = [
        {"role": "user", "content": "أهلاً"},
        {"role": "assistant", "content": "أهلاً بيك في Kif"},
    ]
    text = _build_conversation_text("عايز أسجل في دبلومة SOC", history)
    assert "User: أهلاً" in text
    assert "Kif: أهلاً بيك في Kif" in text
    assert "User: عايز أسجل في دبلومة SOC" in text


def test_extract_crm_fields_parses_json():
    fake_message = MagicMock()
    fake_message.content = '{"name": "أحمد", "products": "SOC", "temperature": "ساخن"}'
    fake_message.reasoning = None

    fake_choice = MagicMock()
    fake_choice.message = fake_message

    fake_usage = MagicMock()
    fake_usage.prompt_tokens = 100
    fake_usage.completion_tokens = 50

    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    fake_response.usage = fake_usage

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response

    result = _extract_crm_fields(fake_client, "model", "openrouter", "some text")
    assert result["fields"]["name"] == "أحمد"
    assert result["fields"]["products"] == "SOC"
    assert result["fields"]["temperature"] == "ساخن"
    assert result["input_tokens"] == 100
    assert result["output_tokens"] == 50
    assert result["cost_usd"] >= 0


def test_extract_crm_fields_falls_back_to_regex():
    fake_message = MagicMock()
    fake_message.content = "Here is the JSON:\n{\"name\": \"سارة\", \"products\": \"Power BI\"}\nHope that helps."
    fake_message.reasoning = None

    fake_choice = MagicMock()
    fake_choice.message = fake_message

    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    fake_response.usage = None

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response

    result = _extract_crm_fields(fake_client, "model", "openrouter", "text")
    assert result["fields"]["name"] == "سارة"
    assert result["fields"]["products"] == "Power BI"
