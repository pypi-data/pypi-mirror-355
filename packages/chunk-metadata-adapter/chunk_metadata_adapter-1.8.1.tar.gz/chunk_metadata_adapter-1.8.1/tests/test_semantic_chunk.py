import pytest
import uuid
from datetime import datetime, timezone
from chunk_metadata_adapter.semantic_chunk import SemanticChunk
from chunk_metadata_adapter.chunk_query import ChunkQuery
from chunk_metadata_adapter.data_types import ChunkType, LanguageEnum
import pydantic

def test_semanticchunk_factory_valid():
    data = dict(
        chunk_uuid=str(uuid.uuid4()),
        type=ChunkType.DOC_BLOCK.value,
        text="test",
        language=LanguageEnum.EN,
        sha256="a"*64,
        created_at="2024-01-01T00:00:00+00:00",
        body="b",
        summary="s"
    )
    chunk = SemanticChunk.from_dict_with_autofill_and_validation(data)
    assert chunk.text == "test"
    assert chunk.body == "b"
    assert chunk.summary == "s"
    assert chunk.language == LanguageEnum.EN


def test_semanticchunk_factory_missing_required():
    with pytest.raises(pydantic.ValidationError) as e:
        SemanticChunk.from_dict_with_autofill_and_validation({})
    assert "[type=missing" in str(e.value)

def valid_uuid():
    return str(uuid.uuid4())

def valid_sha256():
    return "a" * 64

def valid_created_at():
    return datetime.now(timezone.utc).isoformat()

def test_chunkquery_empty():
    # Пустой фильтр — все поля None
    q = ChunkQuery()
    for field in q.model_fields:
        assert getattr(q, field) is None

def test_chunkquery_equality_fields():
    # Проверка равенства для обычных полей (только нужные поля)
    q = ChunkQuery(type='DocBlock', language='en', uuid=valid_uuid())
    assert q.type == 'DocBlock'
    assert q.language == 'en'
    assert len(q.uuid) == 36

def test_chunkquery_comparison_fields_str():
    # Проверка полей с операторами сравнения (строка)
    q = ChunkQuery(start='>100', end='<200', quality_score='[0.7,1.0]', year='in:2022,2023')
    assert q.start == '>100'
    assert q.end == '<200'
    assert q.quality_score == '[0.7,1.0]'
    assert q.year == 'in:2022,2023'

def test_chunkquery_comparison_fields_native():
    # Проверка полей с исходным типом
    q = ChunkQuery(start=10, end=20, quality_score=0.95, year=2023)
    assert q.start == 10
    assert q.end == 20
    assert q.quality_score == 0.95
    assert q.year == 2023

def test_chunkquery_mixed_fields():
    # Комбинированные условия
    q = ChunkQuery(type='DocBlock', start='>=0', end=100, coverage='>0.5', status='verified')
    assert q.type == 'DocBlock'
    assert q.start == '>=0'
    assert q.end == 100
    assert q.coverage == '>0.5'
    assert q.status == 'verified'

def example_chunkquery_usage():
    """
    Пример: поиск всех чанков типа 'DocBlock' с quality_score > 0.8 и годом 2022 или 2023
    """
    q = ChunkQuery(type='DocBlock', quality_score='>0.8', year='in:2022,2023')
    assert q.type == 'DocBlock'
    assert q.quality_score == '>0.8'
    assert q.year == 'in:2022,2023' 