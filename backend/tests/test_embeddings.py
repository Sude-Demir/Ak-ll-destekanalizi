from unittest.mock import MagicMock, patch

import pytest

from app.services import embeddings


@pytest.fixture(autouse=True)
def reset_client():
    """Testler arası paylaşılan _client global'ini sıfırlar."""
    embeddings._client = None
    yield
    embeddings._client = None


def test_get_client_creates_and_caches_client():
    with patch.object(embeddings.genai, "Client", return_value=MagicMock()) as mock_client_cls:
        client1 = embeddings._get_client()
        client2 = embeddings._get_client()

    mock_client_cls.assert_called_once()
    assert client1 is client2


def test_embed_text_returns_vector_from_gemini_response():
    fake_embedding = [0.1, 0.2, 0.3]
    fake_response = MagicMock()
    fake_response.embeddings = [MagicMock(values=fake_embedding)]
    fake_client = MagicMock()
    fake_client.models.embed_content.return_value = fake_response

    with patch.object(embeddings, "_get_client", return_value=fake_client):
        result = embeddings.embed_text("iade nasıl yapılır?")

    assert result == fake_embedding
    _, kwargs = fake_client.models.embed_content.call_args
    assert kwargs["model"] == embeddings.EMBEDDING_MODEL
    assert kwargs["contents"] == "iade nasıl yapılır?"
    assert kwargs["config"].output_dimensionality == embeddings.EMBEDDING_DIM
