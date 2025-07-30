from typing import Optional, Union
from pydantic import Field, BaseModel

class ChunkQuery(BaseModel):
    """
    Query/command model for search and delete operations over chunks.
    Позволяет формировать фильтры с операторами сравнения для числовых и вещественных полей.

    Особенности:
    - Все поля, где допустимы только операции равенства (перечисления, идентификаторы, строки, булевы и т.п.), наследуются как Optional.
    - Для полей, где допустимы сравнения (start, end, year, quality_score, coverage, cohesion, boundary_prev, boundary_next), допускается либо исходный тип, либо строка с оператором (например, '>5', '<=10', '[1,5]', 'in:1,2,3').
    - Используется для построения поисковых и delete-команд с гибкой фильтрацией.
    - Все поля опциональны, фильтр может быть полностью пустым.

    Примеры использования:
    >>> ChunkQuery(start='>100', end='<200', type='DocBlock')
    >>> ChunkQuery(quality_score='[0.7,1.0]', language='en')
    >>> ChunkQuery(year=2023, status='verified')
    """
    uuid: Optional[str] = Field(default=None, description="Unique identifier (UUIDv4)")
    source_id: Optional[str] = Field(default=None, description="Source identifier (UUIDv4)")
    project: Optional[str] = Field(default=None, description="Project name")
    task_id: Optional[str] = Field(default=None, description="Task identifier (UUIDv4)")
    subtask_id: Optional[str] = Field(default=None, description="Subtask identifier (UUIDv4)")
    unit_id: Optional[str] = Field(default=None, description="Processing unit identifier (UUIDv4)")
    type: Optional[str] = Field(default=None, description="Chunk type (e.g., 'Draft', 'DocBlock')")
    role: Optional[str] = Field(default=None, description="Role in the system")
    language: Optional[str] = Field(default=None, description="Language code (enum)")
    body: Optional[str] = Field(default=None, description="Original chunk text")
    text: Optional[str] = Field(default=None, description="Normalized text for search")
    summary: Optional[str] = Field(default=None, description="Short summary of the chunk")
    ordinal: Optional[int] = Field(default=None, description="Order of the chunk within the source")
    sha256: Optional[str] = Field(default=None, description="SHA256 hash of the text")
    created_at: Optional[str] = Field(default=None, description="ISO8601 creation date with timezone")
    status: Optional[str] = Field(default=None, description="Processing status")
    source_path: Optional[str] = Field(default=None, description="Path to the source file")
    quality_score: Optional[Union[float, str]] = Field(default=None, description="Quality score [0,1] (float or comparison string)")
    coverage: Optional[Union[float, str]] = Field(default=None, description="Coverage [0,1] (float or comparison string)")
    cohesion: Optional[Union[float, str]] = Field(default=None, description="Cohesion [0,1] (float or comparison string)")
    boundary_prev: Optional[Union[float, str]] = Field(default=None, description="Boundary similarity with previous chunk (float or comparison string)")
    boundary_next: Optional[Union[float, str]] = Field(default=None, description="Boundary similarity with next chunk (float or comparison string)")
    used_in_generation: Optional[bool] = Field(default=None, description="Whether used in generation")
    feedback_accepted: Optional[int] = Field(default=None, description="How many times the chunk was accepted")
    feedback_rejected: Optional[int] = Field(default=None, description="How many times the chunk was rejected")
    start: Optional[Union[int, str]] = Field(default=None, description="Start offset (int or comparison string)")
    end: Optional[Union[int, str]] = Field(default=None, description="End offset (int or comparison string)")
    category: Optional[str] = Field(default=None, description="Business category (e.g., 'science', 'programming', 'news')")
    title: Optional[str] = Field(default=None, description="Title or short name")
    year: Optional[Union[int, str]] = Field(default=None, description="Year (int or comparison string)")
    is_public: Optional[bool] = Field(default=None, description="Public visibility (True/False)")
    source: Optional[str] = Field(default=None, description="Data source (e.g., 'user', 'external', 'import')")
    block_type: Optional[str] = Field(default=None, description="Type of the source block (BlockType: 'paragraph', 'message', 'section', 'other')")
    chunking_version: Optional[str] = Field(default=None, description="Version of the chunking algorithm or pipeline")
    metrics: Optional[dict] = Field(default=None, description="Full metrics object for compatibility")
    block_id: Optional[str] = Field(default=None, description="UUIDv4 of the source block")
    embedding: Optional[list] = Field(default=None, description="Embedding vector")
    block_index: Optional[int] = Field(default=None, description="Index of the block in the source document")
    source_lines_start: Optional[int] = Field(default=None, description="Start line in the source file")
    source_lines_end: Optional[int] = Field(default=None, description="End line in the source file")
    tags: Optional[list] = Field(default=None, description="Categorical tags for the chunk.")
    links: Optional[list] = Field(default=None, description="References to other chunks in the format 'relation:uuid'.")
    block_meta: Optional[dict] = Field(default=None, description="Additional metadata about the block.")
    tags_flat: Optional[str] = Field(default=None, description="Comma-separated tags for flat storage.")
    link_related: Optional[str] = Field(default=None, description="Related chunk UUID")
    link_parent: Optional[str] = Field(default=None, description="Parent chunk UUID") 