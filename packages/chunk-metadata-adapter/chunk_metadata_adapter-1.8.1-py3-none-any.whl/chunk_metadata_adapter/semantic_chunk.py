"""
Models for chunk metadata representation using Pydantic.

Бизнес-поля (Business fields) — расширяют основную модель чанка для поддержки бизнес-логики и интеграции с внешними системами.

Поля:
- category: Optional[str] — бизнес-категория записи (например, 'наука', 'программирование', 'новости'). Максимум 64 символа.
- title: Optional[str] — заголовок или краткое название записи. Максимум 256 символов.
- year: Optional[int] — год, связанный с записью (например, публикации). Диапазон: 0–2100.
- is_public: Optional[bool] — публичность записи (True/False).
- source: Optional[str] — источник данных (например, 'user', 'external', 'import'). Максимум 64 символов.
- language: str — язык содержимого (например, 'en', 'ru').
- tags: List[str] — список тегов для классификации.
- uuid: str — уникальный идентификатор (UUIDv4).
- type: str — тип чанка (например, 'Draft', 'DocBlock').
- text: str — нормализованный текст для поиска.
- body: str — исходный текст чанка.
- sha256: str — SHA256 хеш текста.
- created_at: str — ISO8601 дата создания.
- status: str — статус обработки.
- start: int — смещение начала чанка.
- end: int — смещение конца чанка.
"""
from enum import Enum
from typing import List, Dict, Optional, Union, Any, Pattern
import re
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator, field_validator, model_validator
import abc
import pydantic
from chunk_metadata_adapter.utils import get_empty_value_for_type, is_empty_value, get_base_type, get_valid_default_for_type, ChunkId, EnumBase, to_flat_dict, from_flat_dict
from chunk_metadata_adapter.data_types import BaseChunkMetadata, ISO8601_PATTERN, ChunkType, ChunkRole, ChunkStatus, BlockType, LanguageEnum
from dateutil.parser import isoparse
import hashlib
import json

UUID4_PATTERN: Pattern = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)

ISO8601_PATTERN: Pattern = re.compile(
    r'^([0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T([2][0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$'
)

class FeedbackMetrics(BaseModel):
    accepted: int = Field(default=0, description="How many times the chunk was accepted")
    rejected: int = Field(default=0, description="How many times the chunk was rejected")
    modifications: int = Field(default=0, description="Number of modifications made after generation")

class ChunkMetrics(BaseModel):
    quality_score: Optional[float] = Field(default=None, ge=0, le=1, description="Quality score between 0 and 1")
    coverage: Optional[float] = Field(default=None, ge=0, le=1, description="Coverage score between 0 and 1")
    cohesion: Optional[float] = Field(default=None, ge=0, le=1, description="Cohesion score between 0 and 1")
    boundary_prev: Optional[float] = Field(default=None, ge=0, le=1, description="Boundary similarity with previous chunk")
    boundary_next: Optional[float] = Field(default=None, ge=0, le=1, description="Boundary similarity with next chunk")
    matches: Optional[int] = Field(default=None, ge=0, description="How many times matched in retrieval")
    used_in_generation: bool = Field(default=False, description="Whether used in generation")
    used_as_input: bool = Field(default=False, description="Whether used as input")
    used_as_context: bool = Field(default=False, description="Whether used as context")
    feedback: FeedbackMetrics = Field(default_factory=FeedbackMetrics, description="Feedback metrics")

class SemanticChunk(BaseModel):
    """
    Main model representing a universal semantic chunk with metadata.
    
    RECOMMENDED USAGE:
    - Always create SemanticChunk objects via ChunkMetadataBuilder factory methods (not direct constructor).
    - For any transformation (flat <-> semantic <-> dict), use only public builder methods.
    - Full recommended chain: dict (structured) -> build_semantic_chunk -> semantic_to_flat -> flat_to_semantic -> model_dump() (dict).
    
    All field descriptions are now included here.
    """
    uuid: ChunkId = Field(default=ChunkId.default_value(), description="Unique identifier (UUIDv4)")
    source_id: ChunkId = Field(default=ChunkId.default_value(), description="Source identifier (UUIDv4)")
    project: Optional[str] = Field(default=None, min_length=0, max_length=128, description="Project name")
    task_id: ChunkId = Field(default=ChunkId.default_value(), description="Task identifier (UUIDv4)")
    subtask_id: ChunkId = Field(default=ChunkId.default_value(), description="Subtask identifier (UUIDv4)")
    unit_id: ChunkId = Field(default=ChunkId.default_value(), description="Processing unit identifier (UUIDv4)")
    type: str = Field(..., min_length=3, max_length=32, description="Chunk type (e.g., 'Draft', 'DocBlock')")
    role: Optional[str] = Field(default="system", min_length=0, max_length=32, description="Role in the system")
    language: Optional[LanguageEnum] = Field(default=LanguageEnum.UNKNOWN, min_length=0, description="Language code (enum)")
    body: str = Field(..., min_length=1, max_length=10000, description="Original chunk text")
    text: Optional[str] = Field(default=None, min_length=0, max_length=10000, description="Normalized text for search")
    summary: Optional[str] = Field(default=None, min_length=0, max_length=512, description="Short summary of the chunk")
    ordinal: Optional[int] = Field(default=0, ge=0, description="Order of the chunk within the source")
    sha256: Optional[str] = Field(default=None, min_length=0, max_length=64, description="SHA256 hash of the text")
    created_at: Optional[str] = Field(default=None, min_length=0, description="ISO8601 creation date with timezone")
    status: Optional[str] = Field(default="new", min_length=0, max_length=32, description="Processing status")
    source_path: Optional[str] = Field(default=None, min_length=0, max_length=512, description="Path to the source file")
    quality_score: Optional[float] = Field(default=None, ge=0, le=1, description="Quality score [0, 1]")
    coverage: Optional[float] = Field(default=None, ge=0, le=1, description="Coverage score [0, 1]")
    cohesion: Optional[float] = Field(default=None, ge=0, le=1, description="Cohesion score [0, 1]")
    boundary_prev: Optional[float] = Field(default=None, ge=0, le=1, description="Boundary similarity with previous chunk")
    boundary_next: Optional[float] = Field(default=None, ge=0, le=1, description="Boundary similarity with next chunk")
    used_in_generation: Optional[bool] = Field(default=None, description="Whether used in generation")
    feedback_accepted: Optional[int] = Field(default=None, ge=0, description="How many times the chunk was accepted")
    feedback_rejected: Optional[int] = Field(default=None, ge=0, description="How many times the chunk was rejected")
    start: Optional[int] = Field(default=None, ge=0, description="Start offset of the chunk")
    end: Optional[int] = Field(default=None, ge=0, description="End offset of the chunk")
    category: Optional[str] = Field(default=None, min_length=0, max_length=64, description="Business category (e.g., 'science', 'programming', 'news')")
    title: Optional[str] = Field(default=None, min_length=0, max_length=256, description="Title or short name")
    year: Optional[int] = Field(default=0, ge=0, le=2100, description="Year associated with the record")
    is_public: Optional[bool] = Field(default=None, description="Public visibility (True/False)")
    source: Optional[str] = Field(default=None, min_length=0, max_length=64, description="Data source (e.g., 'user', 'external', 'import')")
    block_type: Optional[str] = Field(default=None, min_length=0, description="Type of the source block (BlockType: 'paragraph', 'message', 'section', 'other')")
    chunking_version: Optional[str] = Field(default="1.0", min_length=0, max_length=32, description="Version of the chunking algorithm or pipeline")
    metrics: Optional[ChunkMetrics] = Field(default=None, description="Full metrics object for compatibility")
    block_id: ChunkId = Field(default=ChunkId.default_value(), description="UUIDv4 of the source block")
    embedding: Optional[Any] = Field(default=None, description="Embedding vector")
    block_index: Optional[int] = Field(default=None, ge=0, description="Index of the block in the source document")
    source_lines_start: Optional[int] = Field(default=None, ge=0, description="Start line in the source file")
    source_lines_end: Optional[int] = Field(default=None, ge=0, description="End line in the source file")
    # Коллекционные и бизнес-поля
    tags: Optional[List[str]] = Field(default=None, min_length=0, max_length=32, description="Categorical tags for the chunk.")
    links: Optional[List[str]] = Field(default=None, min_length=0, max_length=32, description="References to other chunks in the format 'relation:uuid'.")
    block_meta: Optional[dict] = Field(default=None, description="Additional metadata about the block.")
    # Flat-only поля (были только в FlatSemanticChunk)
    tags_flat: Optional[str] = Field(default=None, min_length=0, max_length=1024, description="Comma-separated tags for flat storage.")
    link_related: Optional[str] = Field(default=None, min_length=0, description="Related chunk UUID")
    link_parent: Optional[str] = Field(default=None, min_length=0, description="Parent chunk UUID")

    def __init__(self, **data):
        # Обработка source_lines до вызова BaseModel
        source_lines = data.pop('source_lines', None)
        super().__init__(**data)
        if source_lines is not None and isinstance(source_lines, list) and len(source_lines) == 2:
            self.source_lines_start = source_lines[0]
            self.source_lines_end = source_lines[1]

    @classmethod
    def from_dict_with_autofill_and_validation(cls, data: dict) -> "SemanticChunk":
        # Преобразуем language к Enum, если это строка
        if "language" in data and not isinstance(data["language"], LanguageEnum):
            data["language"] = LanguageEnum(data["language"])
        return cls(**data)

    @classmethod
    def get_default_prop_val(cls, prop_name):
        if prop_name == "tags":
            return []
        if prop_name == "links":
            return []
        raise ValueError(f"No such property: {prop_name}")

    @property
    def source_lines(self) -> Optional[list[int]]:
        if self.source_lines_start is not None and self.source_lines_end is not None:
            return [self.source_lines_start, self.source_lines_end]
        return None

    @source_lines.setter
    def source_lines(self, value: Optional[list[int]]):
        if value and len(value) == 2:
            self.source_lines_start, self.source_lines_end = value
        else:
            self.source_lines_start = self.source_lines_end = None

    def to_flat_dict(self, for_redis: bool = True) -> dict:
        """
        Преобразует SemanticChunk в плоский словарь для записи в БД или Redis.
        Если for_redis=True (по умолчанию) — все значения сериализуются в строки, dict/list — в JSON, bool — 'true'/'false', None — '', Enum — str, datetime — ISO, created_at автозаполняется.
        """
        return to_flat_dict(self.model_dump(), for_redis=for_redis)

    @classmethod
    def from_flat_dict(cls, data: dict) -> "SemanticChunk":
        """
        Создаёт SemanticChunk из плоского словаря (например, из БД).
        Корректно десериализует списки/массивы/embedding/tags/links из строк.
        Удаляет created_at из block_meta, если он там есть.
        Восстанавливает Enum-поля.
        """
        import json
        from chunk_metadata_adapter.data_types import LanguageEnum  # пример, добавить другие Enum при необходимости
        # Сопоставление: flat_key -> EnumClass
        enums = {
            "language": LanguageEnum,
            # добавить другие Enum-поля, если есть
        }
        restored = from_flat_dict(data, enums=enums)
        # Гарантируем правильные типы для списков/массивов
        for field in ["tags", "links", "embedding"]:
            val = restored.get(field)
            if isinstance(val, str):
                if val.strip() == "" or val.strip() == "null":
                    restored[field] = []
                else:
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, list):
                            restored[field] = parsed
                        else:
                            raise ValueError(f"Field '{field}' must be a list, got: {val}")
                    except Exception:
                        raise ValueError(f"Field '{field}' must be a list, got: {val}")
            elif val is None:
                restored[field] = []
        return cls(**restored)

    def validate_metadata(self) -> None:
        if not isinstance(self.tags, list):
            raise ValueError("tags must be a list for structured metadata")
        if not isinstance(self.links, list):
            raise ValueError("links must be a list for structured metadata")
        self.__class__.model_validate(self)

    @model_validator(mode="before")
    @classmethod
    def fill_text_from_body(cls, values):
        # Если text не задан, заполняем его из body
        if values.get("text") in (None, "") and values.get("body") not in (None, ""):
            values["text"] = values["body"]
        return values

    @classmethod
    def validate_and_fill(cls, data: dict):
        """
        Универсальная фабрика: валидация, автозаполнение, создание экземпляра.
        Возвращает (экземпляр, ошибки) — если ошибки есть, экземпляр None.
        """
        from pydantic import ValidationError
        from chunk_metadata_adapter.utils import (
            get_base_type, EnumBase, autofill_enum_field, is_empty_value, get_empty_value_for_type, ChunkId, get_valid_default_for_field
        )
        import hashlib
        from datetime import datetime, timezone
        import json
        # --- Автодесериализация списков/массивов из строк ---
        for field in ["tags", "links", "embedding"]:
            val = data.get(field)
            if isinstance(val, str):
                if val.strip() == "" or val.strip() == "null":
                    data[field] = []
                else:
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, list):
                            data[field] = parsed
                        else:
                            raise ValueError(f"Field '{field}' must be a list, got: {val}")
                    except Exception:
                        return None, {"error": f"Field '{field}' must be a list, got: {val}", "fields": {field: [f"Must be a list, got: {val}"]}}
            elif val is None:
                data[field] = []
        # block_meta — dict
        if "block_meta" in data and isinstance(data["block_meta"], str):
            if data["block_meta"].strip() == "" or data["block_meta"].strip() == "null":
                data["block_meta"] = {}
            else:
                try:
                    parsed = json.loads(data["block_meta"])
                    if isinstance(parsed, dict):
                        data["block_meta"] = parsed
                    else:
                        raise ValueError(f"Field 'block_meta' must be a dict, got: {data['block_meta']}")
                except Exception:
                    return None, {"error": f"Field 'block_meta' must be a dict, got: {data['block_meta']}", "fields": {"block_meta": [f"Must be a dict, got: {data['block_meta']}"]}}
        # Удаляем created_at из block_meta, если он там есть
        if "block_meta" in data and isinstance(data["block_meta"], dict):
            data["block_meta"].pop("created_at", None)
        # --- Автозаполнение sha256 ---
        if not data.get("sha256"):
            text = data.get("body") or data.get("text") or ""
            data["sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        # --- Автозаполнение created_at ---
        if not data.get("created_at"):
            data["created_at"] = datetime.now(timezone.utc).isoformat()
        errors = {}
        error_lines = []
        # 1. Автозаполнение Enum-полей
        enum_fields = {
            'type': ChunkType,
            'role': ChunkRole,
            'status': ChunkStatus,
            'block_type': BlockType,
            'language': LanguageEnum,
        }

        if "body" in data:
            if "text" not in data:
                data["text"] = data["body"]
            elif data["body"] != "" and data["text"] == "":
                data["text"] = data["body"]

        print(f"data[body]: {data.get('body')}")
        print(f"data[text]: {data.get('text')}")

        for name, enum_cls in enum_fields.items():
            if name in data:
                data[name] = autofill_enum_field(data.get(name), enum_cls, allow_none=True)
        # 2. Автозаполнение строковых полей с min_length >= 0 (кроме Enum)
        for name, field in cls.model_fields.items():
            base_type = get_base_type(field.annotation)
            val = data.get(name, None)
            # Enum
            if isinstance(base_type, type) and issubclass(base_type, EnumBase):
                data[name] = autofill_enum_field(val, base_type, allow_none=True)
            # str
            elif base_type is str:
                min_len = getattr(field, 'min_length', 0)
                if min_len > 0:
                    if val is None or not isinstance(val, str) or len(val) < min_len:
                        if name == "chunking_version":
                            data[name] = "1.0"
                        else:
                            fill = val if isinstance(val, str) else ''
                            data[name] = (fill + 'x' * min_len)[:min_len]
                elif val is None:
                    data[name] = ""
            # int/float
            elif base_type in (int, float):
                if val is None or val == "":
                    min_v = getattr(field, 'ge', None)
                    max_v = getattr(field, 'le', None)
                    if min_v is not None:
                        data[name] = min_v
                    elif max_v is not None:
                        data[name] = max_v
                    else:
                        data[name] = 0 if base_type is int else 0.0
            # bool
            elif base_type is bool:
                if val is None:
                    data[name] = False
            # UUID/ChunkId
            elif base_type is ChunkId:
                if is_empty_value(val):
                    data[name] = ChunkId.default_value()
            # pydantic.BaseModel
            elif isinstance(base_type, type) and hasattr(base_type, 'model_fields'):
                if is_empty_value(val):
                    data[name] = base_type()
            # list
            elif base_type is list:
                min_len = getattr(field, 'min_length', 0)
                if val is None and min_len > 0:
                    data[name] = [None] * min_len
                elif val is None:
                    data[name] = []
            # dict, tuple
            elif base_type in (dict, tuple):
                if val is None:
                    data[name] = base_type()
            # Остальные
            elif is_empty_value(val):
                data[name] = get_empty_value_for_type(base_type)
        # --- Автозаполнение бизнес-полей дефолтами ---
        for field, default in [
            ("category", ""),
            ("title", ""),
            ("source", ""),
        ]:
            if data.get(field) is None:
                data[field] = default
        if data.get("year") is None:
            data["year"] = 0
        if data.get("is_public") is None:
            data["is_public"] = False
        if data.get("tags") is None:
            data["tags"] = []
        if data.get("links") is None:
            data["links"] = []
        if data.get("role") is None:
            data["role"] = "system"
        # Попытка создать экземпляр
        try:
            obj = cls(**data)
            return obj, None
        except ValidationError as e:
            field_errors = {}
            error_lines = []
            for err in e.errors():
                loc = err.get('loc')
                msg = err.get('msg')
                if loc:
                    field = loc[0]
                    field_errors.setdefault(field, []).append(msg)
                    error_lines.append(f"{field}: {msg}")
            return None, {'error': '; '.join(error_lines), 'fields': field_errors}
        except Exception as e:
            return None, {'error': str(e), 'fields': {}}

    def model_post_init(self, __context):
        # Синхронизация metrics
        if self.metrics is not None and isinstance(self.metrics, dict):
            self.metrics = ChunkMetrics(**self.metrics)
        # Удаляем created_at из block_meta, если он там есть
        if hasattr(self, 'block_meta') and isinstance(self.block_meta, dict):
            self.block_meta.pop('created_at', None)
        # Синхронизация source_lines
        if hasattr(self, 'source_lines') and self.source_lines is not None:
            if isinstance(self.source_lines, list) and len(self.source_lines) == 2:
                self.source_lines_start = self.source_lines[0]
                self.source_lines_end = self.source_lines[1]

    @field_validator('sha256')
    @classmethod
    def validate_sha256(cls, v):
        if v is not None:
            if not isinstance(v, str) or len(v) != 64 or not all(c in '0123456789abcdefABCDEF' for c in v):
                raise ValueError('sha256 must be a 64-character hex string')
        return v

    @field_validator('created_at')
    @classmethod
    def validate_created_at(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError('created_at must be a valid ISO8601 string')
            try:
                isoparse(v)
            except Exception:
                raise ValueError('created_at must be a valid ISO8601 string')
        return v

    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v):
        if v is not None and not isinstance(v, list):
            raise ValueError('embedding must be a list or None')
        return v

    @field_validator('uuid', 'source_id', 'task_id', 'subtask_id', 'unit_id', 'block_id')
    @classmethod
    def validate_chunkid_fields(cls, v):
        from chunk_metadata_adapter.utils import ChunkId
        if v is None:
            return ChunkId.default_value()
        # Use built-in ChunkId validation
        try:
            return ChunkId.validate(v, None)
        except Exception as e:
            raise ValueError(f"Invalid UUIDv4 for ChunkId field: {v} ({e})")


def _autofill_min_length_str_fields(data, model_fields):
    for name, field in model_fields.items():
        base_type = get_base_type(field.annotation)
        if base_type is str and name != 'tags':
            min_len = getattr(field, 'min_length', 0)
            val = data.get(name, None)
            if min_len > 0:
                if val is None or val == '' or (isinstance(val, str) and len(val) < min_len):
                    if name == 'chunking_version':
                        data[name] = '1.0'
                    else:
                        fill = val if isinstance(val, str) else ''
                        data[name] = (fill + 'x' * min_len)[:min_len]
    return data


