from unittest.mock import MagicMock, patch

from google.genai import errors

from app.services import llm


def _server_error() -> errors.ServerError:
    response = MagicMock()
    response.json.side_effect = Exception("no body")
    response.text = "temporarily unavailable"
    response.reason = "UNAVAILABLE"
    return errors.ServerError(503, response)


def _rate_limit_error() -> errors.ClientError:
    response = MagicMock()
    response.json.side_effect = Exception("no body")
    response.text = "quota exceeded"
    response.reason = "RESOURCE_EXHAUSTED"
    return errors.ClientError(429, response)


def test_call_llm_returns_response_text():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="cevap")

    with patch("app.services.llm._get_client", return_value=mock_client), patch("app.services.llm.time.sleep"):
        result = llm.call_llm("görev", "bağlam")

    assert result == "cevap"
    _, kwargs = mock_client.models.generate_content.call_args
    assert kwargs["contents"] == "görev\n\nbağlam"
    assert kwargs["config"] is None


def test_call_llm_retries_on_server_error_then_succeeds():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [_server_error(), MagicMock(text="ikinci denemede geldi")]

    with patch("app.services.llm._get_client", return_value=mock_client), patch("app.services.llm.time.sleep"):
        result = llm.call_llm("görev")

    assert result == "ikinci denemede geldi"
    assert mock_client.models.generate_content.call_count == 2


def test_call_llm_raises_immediately_on_non_429_client_error():
    mock_client = MagicMock()
    bad_request = errors.ClientError(400, MagicMock(json=MagicMock(side_effect=Exception()), text="bozuk istek"))
    mock_client.models.generate_content.side_effect = bad_request

    with patch("app.services.llm._get_client", return_value=mock_client), patch("app.services.llm.time.sleep"):
        try:
            llm.call_llm("görev")
            assert False, "beklenen hata fırlatılmadı"
        except errors.ClientError:
            pass

    assert mock_client.models.generate_content.call_count == 1


def test_call_llm_with_tools_passes_tools_through_config():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="cevap")

    def dummy_tool():
        """test aracı"""
        return "sonuç"

    with patch("app.services.llm._get_client", return_value=mock_client):
        result = llm.call_llm_with_tools("görev", "bağlam", tools=[dummy_tool])

    assert result == "cevap"
    _, kwargs = mock_client.models.generate_content.call_args
    assert kwargs["config"].tools == [dummy_tool]
