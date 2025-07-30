import pytest
import uuid
from datetime import datetime, timezone
from chunk_metadata_adapter.semantic_chunk import SemanticChunk
from chunk_metadata_adapter.chunk_query import ChunkQuery
from chunk_metadata_adapter.data_types import ChunkType, LanguageEnum, ChunkRole, ChunkStatus, BlockType
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

def test_chunkquery_factory_valid():
    # Корректный фильтр с равенством
    data = {"type": "DocBlock", "language": "en"}
    f, err = ChunkQuery.from_dict_with_validation(data)
    assert err is None
    assert f.type == "DocBlock"
    assert f.language == "en"

    # Корректный фильтр с диапазоном и in
    data2 = {"start": ">=10", "end": "<100", "year": "in:2022,2023"}
    f2, err2 = ChunkQuery.from_dict_with_validation(data2)
    assert err2 is None
    assert f2.start == ">=10"
    assert f2.end == "<100"
    assert f2.year == "in:2022,2023"

    # Сериализация и восстановление
    flat = f2.to_flat_dict()
    f2_restored = ChunkQuery.from_flat_dict(flat)
    assert f2_restored.start == f2.start
    assert f2_restored.end == f2.end
    assert f2_restored.year == f2.year

    # Пустой фильтр
    f3, err3 = ChunkQuery.from_dict_with_validation({})
    assert err3 is None
    for field in f3.model_fields:
        assert getattr(f3, field) is None

    # Ошибка: неверный тип
    bad = {"start": [1,2,3]}
    f4, err4 = ChunkQuery.from_dict_with_validation(bad)
    assert f4 is None
    assert err4 is not None
    assert "start" in err4["fields"]

    # --- Негативные сценарии: несуществующее поле ---
    bad2 = {"not_a_field": 123}
    f5, err5 = ChunkQuery.from_dict_with_validation(bad2)
    # Pydantic игнорирует неизвестные поля, ошибки не будет
    assert f5 is not None
    assert err5 is None

    # None как значение
    f6, err6 = ChunkQuery.from_dict_with_validation({"type": None})
    assert err6 is None
    assert f6.type is None

    # Проверка фильтрации списка (минимальная логика)
    chunks = [
        {"type": "DocBlock", "start": 15, "year": 2022},
        {"type": "CodeBlock", "start": 5, "year": 2023},
        {"type": "DocBlock", "start": 50, "year": 2023},
    ]
    filter_data = {"type": "DocBlock", "start": ">=10"}
    f, _ = ChunkQuery.from_dict_with_validation(filter_data)
    def match(chunk, f):
        if f.type and chunk["type"] != f.type:
            return False
        if f.start and isinstance(f.start, str) and f.start.startswith(">="):
            try:
                val = int(f.start[2:])
                if chunk["start"] < val:
                    return False
            except Exception:
                return False
        return True
    filtered = [c for c in chunks if match(c, f)]
    assert len(filtered) == 2
    assert filtered[0]["start"] == 15
    assert filtered[1]["start"] == 50

def test_chunkquery_factory_positive_negative_cases():
    # --- Позитивные сценарии ---
    import uuid
    from chunk_metadata_adapter.data_types import ChunkType, ChunkRole, ChunkStatus, BlockType, LanguageEnum
    valid_uuid = str(uuid.uuid4())
    # Валидные UUID и enum
    data = {
        "uuid": valid_uuid,
        "source_id": valid_uuid,
        "task_id": valid_uuid,
        "subtask_id": valid_uuid,
        "unit_id": valid_uuid,
        "block_id": valid_uuid,
        "link_parent": valid_uuid,
        "link_related": valid_uuid,
        "type": ChunkType.DOC_BLOCK.value,
        "role": ChunkRole.DEVELOPER.value,
        "status": ChunkStatus.RAW.value,
        "block_type": BlockType.PARAGRAPH.value,
        "language": LanguageEnum.EN.value,
        "start": 10,
        "end": "<100",
        "year": "in:2022,2023",
        "quality_score": 0.9,
        "coverage": ">0.5",
        "cohesion": None,
        "boundary_prev": None,
        "boundary_next": None,
    }
    f, err = ChunkQuery.from_dict_with_validation(data)
    assert err is None, f"Unexpected error: {err}"
    assert f.type == ChunkType.DOC_BLOCK.value
    assert f.language == LanguageEnum.EN.value
    assert f.uuid == valid_uuid
    assert f.status == ChunkStatus.RAW.value
    assert f.start == 10
    assert f.end == "<100"
    assert f.year == "in:2022,2023"
    # --- Негативные сценарии: невалидные UUID ---
    bad_uuid = "not-a-uuid"
    data_bad_uuid = data.copy()
    data_bad_uuid["uuid"] = bad_uuid
    f2, err2 = ChunkQuery.from_dict_with_validation(data_bad_uuid)
    assert f2 is None
    assert err2 is not None
    assert "uuid" in err2["fields"]
    assert "UUIDv4" in err2["fields"]["uuid"][0]
    # --- Негативные сценарии: невалидный enum ---
    data_bad_enum = data.copy()
    data_bad_enum["type"] = "NotAChunkType"
    f3, err3 = ChunkQuery.from_dict_with_validation(data_bad_enum)
    assert f3 is None
    assert err3 is not None
    assert "type" in err3["fields"]
    assert "one of" in err3["fields"]["type"][0]
    # --- Негативные сценарии: невалидный тип для поля, где допускается только str/int/float/bool ---
    data_bad_type = data.copy()
    data_bad_type["start"] = [1,2,3]  # список не допускается
    f4, err4 = ChunkQuery.from_dict_with_validation(data_bad_type)
    assert f4 is None
    assert err4 is not None
    assert "start" in err4["fields"] or "value is not a valid integer" in str(err4)
    # --- Позитив: допускается str для start/end/year ---
    data_str = data.copy()
    data_str["start"] = ">=10"
    data_str["end"] = "<100"
    data_str["year"] = "in:2022,2023"
    f5, err5 = ChunkQuery.from_dict_with_validation(data_str)
    assert err5 is None
    assert f5.start == ">=10"
    assert f5.end == "<100"
    assert f5.year == "in:2022,2023"

def test_chunkquery_only_source_id():
    # Передаём только source_id
    from chunk_metadata_adapter.chunk_query import ChunkQuery
    import uuid
    sid = str(uuid.uuid4())
    data = {"source_id": sid}
    obj, err = ChunkQuery.from_dict_with_validation(data)
    assert err is None
    assert obj.source_id == sid
    flat_dict = obj.to_flat_dict()
    # Все остальные поля должны быть None
    for field in obj.model_fields:
        if field != "source_id":
            assert getattr(obj, field) is None, f"Field {field} is not None: {getattr(obj, field)}" 
    for field in flat_dict:
        if field != "source_id":
            assert flat_dict[field] is None, f"Field {field} is not None: {flat_dict[field]}"
    
    
    