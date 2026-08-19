from unittest.mock import patch

import pytest

from app.db.database import SessionLocal
from app.models import Company, KnowledgeBaseChunk
from app.services import retrieval

# knowledge_base_chunks.embedding sütununun boyutuyla aynı olmalı
# (bkz. backend/app/models/knowledge_base_chunk.py EMBEDDING_DIM).
DIM = 768


def _unit_vector(active_index: int) -> list[float]:
    """`active_index`teki değeri 1.0, geri kalanı 0.0 olan bir vektör üretir.
    Böylece kosinüs mesafesiyle "hangi vektör hangisine daha yakın" kontrolü
    gerçek embedding üretmeden, tahmin edilebilir şekilde yapılabilir."""
    vector = [0.0] * DIM
    vector[active_index] = 1.0
    return vector


@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_company(db_session):
    company = Company(slug="test-retrieval-co", name="Test Retrieval Co")
    db_session.add(company)
    db_session.commit()
    yield company
    db_session.delete(company)
    db_session.commit()


@pytest.fixture
def sample_chunks(db_session, test_company):
    chunks = [
        KnowledgeBaseChunk(
            company_id=test_company.id,
            category="TEST",
            intent="test_close",
            question="q-close",
            answer="a-close",
            source="test",
            embedding=_unit_vector(0),
        ),
        KnowledgeBaseChunk(
            company_id=test_company.id,
            category="TEST",
            intent="test_far",
            question="q-far",
            answer="a-far",
            source="test",
            embedding=_unit_vector(100),
        ),
    ]
    db_session.add_all(chunks)
    db_session.commit()
    yield chunks
    for chunk in chunks:
        db_session.delete(chunk)
    db_session.commit()


def test_retrieve_relevant_chunks_returns_closest_first(db_session, test_company, sample_chunks):
    query_vector = _unit_vector(0)  # test_close ile birebir aynı yönde
    with patch("app.services.retrieval.embed_text", return_value=query_vector):
        results = retrieval.retrieve_relevant_chunks("herhangi bir soru", test_company.id, db_session, top_k=1)

    assert len(results) == 1
    assert results[0].intent == "test_close"


def test_retrieve_relevant_chunks_respects_top_k(db_session, test_company, sample_chunks):
    query_vector = _unit_vector(0)
    with patch("app.services.retrieval.embed_text", return_value=query_vector):
        results = retrieval.retrieve_relevant_chunks("soru", test_company.id, db_session, top_k=2)

    assert len(results) == 2


def test_retrieve_relevant_chunks_with_distances_orders_closest_first(db_session, test_company, sample_chunks):
    query_vector = _unit_vector(0)  # test_close ile birebir aynı yönde
    with patch("app.services.retrieval.embed_text", return_value=query_vector):
        results = retrieval.retrieve_relevant_chunks_with_distances(
            "herhangi bir soru", test_company.id, db_session, top_k=5
        )

    closest_chunk, closest_distance = results[0]
    assert closest_chunk.intent == "test_close"
    assert closest_distance == pytest.approx(0.0, abs=1e-6)  # birebir aynı yön

    distances = [distance for _chunk, distance in results]
    assert distances == sorted(distances)


def test_retrieve_relevant_chunks_ignores_rows_without_embedding(db_session, test_company, sample_chunks):
    no_embedding_chunk = KnowledgeBaseChunk(
        company_id=test_company.id,
        category="TEST",
        intent="test_no_embedding",
        question="q",
        answer="a",
        source="test",
        embedding=None,
    )
    db_session.add(no_embedding_chunk)
    db_session.commit()

    query_vector = _unit_vector(0)
    try:
        with patch("app.services.retrieval.embed_text", return_value=query_vector):
            results = retrieval.retrieve_relevant_chunks("soru", test_company.id, db_session, top_k=10)
        assert all(r.intent != "test_no_embedding" for r in results)
    finally:
        db_session.delete(no_embedding_chunk)
        db_session.commit()


def test_retrieve_relevant_chunks_never_crosses_company_boundary(db_session, test_company, sample_chunks):
    """En kritik test: başka bir şirketin (mükemmel eşleşen) SSS parçası,
    bu şirketin sorgusunda asla dönmemeli — bkz. plan 'RAG izolasyonu'."""
    other_company = Company(slug="test-retrieval-other-co", name="Other Co")
    db_session.add(other_company)
    db_session.commit()

    other_chunk = KnowledgeBaseChunk(
        company_id=other_company.id,
        category="TEST",
        intent="other_company_chunk",
        question="q-other",
        answer="a-other",
        source="test",
        embedding=_unit_vector(0),  # test_close ile BİREBİR aynı vektör
    )
    db_session.add(other_chunk)
    db_session.commit()

    try:
        query_vector = _unit_vector(0)
        with patch("app.services.retrieval.embed_text", return_value=query_vector):
            results = retrieval.retrieve_relevant_chunks("soru", test_company.id, db_session, top_k=10)

        assert all(r.intent != "other_company_chunk" for r in results)
    finally:
        # Ayrı commit'ler gerekiyor — Company ve KnowledgeBaseChunk arasında
        # SQLAlchemy `relationship()` tanımlı değil (bilinçli, bkz. modeller),
        # bu yüzden unit-of-work sırasını otomatik çözemiyor; chunk önce
        # silinmezse foreign key ihlali oluşur.
        db_session.delete(other_chunk)
        db_session.commit()
        db_session.delete(other_company)
        db_session.commit()
