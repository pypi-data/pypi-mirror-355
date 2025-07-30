import pytest
import uuid
from chunk_metadata_adapter.semantic_chunk import SemanticChunk
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