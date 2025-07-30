"""
Builder for chunk metadata.

This module provides tools for creating and manipulating chunk metadata
for semantic chunking systems.
"""
import uuid
import hashlib
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timezone
from .utils import str_to_list, list_to_str, to_flat_dict, from_flat_dict

from .semantic_chunk import (
    SemanticChunk, 
    ChunkType, 
    ChunkRole, 
    ChunkStatus,
    ChunkMetrics,
    FeedbackMetrics
)
# Если потребуется фильтр — импортировать так:
# from .chunk_query import ChunkQuery

from chunk_metadata_adapter.utils import ChunkId


class ChunkMetadataBuilder:
    """
    Builder for universal chunk metadata.
    
    Used after chunk text is formed to augment it with metadata fields:
    - uuid, sha256, created_at
    - project, status, role, tags, etc.
    
    Supports lifecycle states of data:
    - RAW: initial ingestion of unprocessed data
    - CLEANED: data that has been cleaned and preprocessed
    - VERIFIED: data verified against rules and standards
    - VALIDATED: data validated with cross-references and context
    - RELIABLE: data marked as reliable and ready for use
    
    Supports both flat and structured formats.
    """
    def __init__(
        self, 
        project: Optional[str] = None, 
        unit_id: Optional[str] = None,
        chunking_version: str = "1.0"
    ):
        """
        Initialize a new metadata builder.
        
        Args:
            project: Optional project identifier
            unit_id: Optional identifier for the chunking unit/service
            chunking_version: Version of chunking algorithm used
        """
        self.project = project
        self.unit_id = unit_id if unit_id is not None else ChunkId.default_value()
        self.chunking_version = chunking_version

    def generate_uuid(self) -> str:
        """Generate a new UUIDv4 string"""
        return str(uuid.uuid4())

    def compute_sha256(self, text: str) -> str:
        """Compute SHA256 hash of the given text"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO8601 format with UTC timezone"""
        return datetime.now(timezone.utc).isoformat()

    def build_flat_metadata(
        self, *,
        text: Optional[str] = None,
        body: str,
        source_id: str,
        ordinal: int,
        type: Union[str, ChunkType],
        language: str,
        source_path: Optional[str] = None,
        source_lines_start: Optional[int] = None,
        source_lines_end: Optional[int] = None,
        summary: Optional[str] = None,
        tags: Optional[str] = None,
        role: Optional[Union[str, ChunkRole]] = None,
        task_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        link_parent: Optional[str] = None,
        link_related: Optional[str] = None,
        status: Union[str, ChunkStatus] = ChunkStatus.RAW,
        coverage: Optional[float] = None,
        cohesion: Optional[float] = None,
        boundary_prev: Optional[float] = None,
        boundary_next: Optional[float] = None,
        # бизнес-поля
        category: Optional[str] = None,
        title: Optional[str] = None,
        year: Optional[int] = None,
        is_public: Optional[bool] = None,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build chunk metadata in a flat dictionary format.
        
        Args:
            body: Raw/original content of the chunk (before cleaning)
            text: Cleaned/normalized content of the chunk
            source_id: Identifier of the source (file, document, dialogue)
            ordinal: Order of the chunk within the source
            type: Type of the chunk (see ChunkType)
            language: Programming or natural language of the content
            source_path: Optional path to the source file
            source_lines_start: Start line in source file
            source_lines_end: End line in source file
            summary: Brief summary of the chunk content
            tags: Comma-separated tags
            role: Role of the content creator
            task_id: Task identifier
            subtask_id: Subtask identifier
            link_parent: UUID of the parent chunk
            link_related: UUID of a related chunk
            status: Processing status of the chunk (default: RAW for initial data ingestion)
                   See ChunkStatus for lifecycle states (RAW, CLEANED, VERIFIED, VALIDATED, RELIABLE)
            Бизнес-поля:
            - category: Optional[str]
            - title: Optional[str]
            - year: Optional[int]
            - is_public: Optional[bool]
            - source: Optional[str]
            Если поле не указано или пустое — будет None.
            
        Returns:
            Dictionary with flat metadata
        """
        # Verify UUIDs
        if not isinstance(source_id, str) or not uuid.UUID(source_id, version=4):
            raise ValueError(f"source_id must be a valid UUIDv4 string: {source_id}")
            
        if link_parent is not None and (not isinstance(link_parent, str) or not uuid.UUID(link_parent, version=4)):
            raise ValueError(f"link_parent must be a valid UUIDv4 string: {link_parent}")
            
        if link_related is not None and (not isinstance(link_related, str) or not uuid.UUID(link_related, version=4)):
            raise ValueError(f"link_related must be a valid UUIDv4 string: {link_related}")
        
        # Validate coverage
        if coverage is not None:
            try:
                cov = float(coverage)
            except Exception:
                raise ValueError(f"coverage must be a float in [0, 1], got: {coverage}")
            if not (0 <= cov <= 1):
                raise ValueError(f"coverage must be in [0, 1], got: {coverage}")
            coverage = cov
        
        # Convert enum types to string values if needed
        if isinstance(type, ChunkType):
            type = type.value
        if isinstance(role, ChunkRole):
            role = role.value
        if isinstance(status, ChunkStatus):
            status = status.value
            
        # Приведение text/body к единому правилу
        if text in (None, "") and body not in (None, ""):
            text = body
        elif body in (None, "") and text not in (None, ""):
            body = text

        if tags is not None and not isinstance(tags, list):
            raise ValueError(f"tags must be a list of strings or None, got: {type(tags)}")
        if tags:
            tags = list_to_str(tags, separator=',', allow_none=True)

        return {
            "uuid": self.generate_uuid(),
            "source_id": source_id,
            "ordinal": ordinal,
            "sha256": self.compute_sha256(text),
            "body": body if body else None,
            "text": text,
            "summary": summary if summary else None,
            "language": language,
            "type": type,
            "source_path": source_path if source_path else None,
            "source_lines_start": source_lines_start,
            "source_lines_end": source_lines_end,
            "project": self.project if self.project else None,
            "task_id": task_id if task_id else None,
            "subtask_id": subtask_id if subtask_id else None,
            "status": status,
            "unit_id": self.unit_id if self.unit_id else None,
            "created_at": self._get_iso_timestamp(),
            "tags": tags,
            "role": role if role else None,
            "link_parent": link_parent,
            "link_related": link_related,
            "quality_score": None,
            "coverage": coverage,
            "cohesion": cohesion,
            "boundary_prev": boundary_prev,
            "boundary_next": boundary_next,
            "used_in_generation": False,
            "feedback_accepted": 0,
            "feedback_rejected": 0,
            "category": category if category else None,
            "title": title if title else None,
            "year": year if year is not None else None,
            "is_public": is_public if is_public is not None else None,
            "source": source if source else None,
        }
        
    # Alias for backward compatibility
    build_metadata = build_flat_metadata

    def build_semantic_chunk(
        self, *,
        chunk_uuid: Optional[str] = None,
        text: Optional[str] = None,
        body: str,
        language: str,
        chunk_type: Union[str, ChunkType],
        source_id: Optional[str] = None,
        summary: Optional[str] = None,
        role: Optional[Union[str, ChunkRole]] = None,
        source_path: Optional[str] = None,
        source_lines: Optional[List[int]] = None,
        ordinal: Optional[int] = None,
        task_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        links: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: Union[str, ChunkStatus] = ChunkStatus.RAW,
        metrics: Optional[ChunkMetrics] = None,
        quality_score: Optional[float] = None,
        coverage: Optional[float] = None,
        cohesion: Optional[float] = None,
        boundary_prev: Optional[float] = None,
        boundary_next: Optional[float] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        # бизнес-поля
        category: Optional[str] = None,
        title: Optional[str] = None,
        year: Optional[int] = None,
        is_public: Optional[bool] = None,
        source: Optional[str] = None,
        sha256: Optional[str] = None,
    ) -> SemanticChunk:
        """
        Build a fully-structured SemanticChunk object.
        
        Args:
            body: Raw/original content of the chunk (before cleaning)
            text: Cleaned/normalized content of the chunk
            language: Programming or natural language of the content
            chunk_type: Type of the chunk
            source_id: Optional identifier of the source
            summary: Brief summary of the chunk content
            role: Role of the content creator
            source_path: Optional path to the source file
            source_lines: List of line numbers [start, end]
            ordinal: Order of the chunk within the source
            task_id: Task identifier
            subtask_id: Subtask identifier
            links: List of links to other chunks (format: "relation:uuid")
            tags: List of tags
            status: Processing status of the chunk (default: RAW for initial data ingestion)
                   The data lifecycle includes these states:
                   - RAW: Initial raw data as ingested into the system
                   - CLEANED: Data after cleaning and preprocessing
                   - VERIFIED: Data verified against rules and standards
                   - VALIDATED: Data validated with cross-references
                   - RELIABLE: Data ready for use in critical systems
            start: Start offset of the chunk in the source text (in bytes or characters)
            end: End offset of the chunk in the source text (in bytes or characters)
            Бизнес-поля:
            - category: Optional[str]
            - title: Optional[str]
            - year: Optional[int]
            - is_public: Optional[bool]
            - source: Optional[str]
            Если поле не указано или пустое — будет None.
            
        Returns:
            Fully populated SemanticChunk instance
        """
        # Verify UUIDs
        if source_id is not None and (not isinstance(source_id, str) or not uuid.UUID(source_id, version=4)):
            raise ValueError(f"source_id must be a valid UUIDv4 string: {source_id}")
            
        # Validate links format and UUIDs
        if links:
            for link in links:
                parts = link.split(":", 1)
                if len(parts) != 2 or not parts[0] or not parts[1]:
                    raise ValueError(f"Link must follow 'relation:uuid' format: {link}")
                try:
                    uuid.UUID(parts[1], version=4)
                except (ValueError, AttributeError):
                    raise ValueError(f"Invalid UUID4 in link: {link}")
        
        # Проверка типов для tags и links
        if tags is not None and not isinstance(tags, list):
            raise ValueError("tags must be a list of strings, got: {}".format(type(tags)))
        if links is not None and not isinstance(links, list):
            raise ValueError("links must be a list of strings, got: {}".format(type(links)))
        
        # Convert string types to enums if needed
        if isinstance(chunk_type, str):
            chunk_type = ChunkType(chunk_type)
        if isinstance(role, str) and role:
            role = ChunkRole(role)
        if isinstance(status, str):
            # Case-insensitive mapping handled by Enum _missing_
            status = ChunkStatus(status)
            
        # Prepare metrics
        if metrics is None:
            metrics = ChunkMetrics(
                quality_score=quality_score,
                coverage=coverage,
                cohesion=cohesion,
                boundary_prev=boundary_prev,
                boundary_next=boundary_next,
            )

        # Явно приводим опциональные строковые поля к валидной строке, если пусто
        def valid_str(val, min_len):
            return val if val is not None and val != '' else 'x' * min_len
        project = valid_str(self.project, 1) if self.project is not None else ""
        # UUID4 автозаполнение
        def valid_uuid(val):
            try:
                if val and isinstance(val, str):
                    import re
                    UUID4_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE)
                    if UUID4_PATTERN.match(val):
                        return val
                return str(uuid.uuid4())
            except Exception:
                return str(uuid.uuid4())
        unit_id = valid_uuid(self.unit_id) if self.unit_id is not None else str(uuid.uuid4())
        task_id = valid_uuid(task_id) if task_id is not None else str(uuid.uuid4())
        subtask_id = valid_uuid(subtask_id) if subtask_id is not None else str(uuid.uuid4())
        # Приведение text/body к единому правилу
        if text in (None, "") and body not in (None, ""):
            text = body
        elif body in (None, "") and text not in (None, ""):
            body = text
        body = valid_str(body, 1)
        summary = valid_str(summary, 1)
        source_path = valid_str(source_path, 1)
        
        chunking_version = valid_str(self.chunking_version, 1) if self.chunking_version is not None else "1.0"
        if tags is None:
            tags = []
        if isinstance(tags, str):
            tags = str_to_list(tags, separator=',', allow_none=True)
        elif not isinstance(tags, list):
            raise ValueError(f"tags must be a list of strings, got: {type(tags)}")

        return SemanticChunk(
            uuid=chunk_uuid if chunk_uuid is not None else self.generate_uuid(),
            source_id=source_id,
            project=project,
            task_id=task_id,
            subtask_id=subtask_id,
            unit_id=unit_id,
            type=chunk_type,
            role=role,
            language=language,
            body=body,
            text=text,
            summary=summary,
            source_path=source_path,
            source_lines=source_lines,
            ordinal=ordinal,
            sha256=sha256 if sha256 is not None else self.compute_sha256(text),
            chunking_version=chunking_version,
            status=status,
            links=links or [],
            tags=tags,
            metrics=metrics if metrics is not None else ChunkMetrics(),
            created_at=self._get_iso_timestamp(),
            start=start,
            end=end,
            category=category if category else None,
            title=title if title else None,
            year=year if year is not None else None,
            is_public=is_public if is_public is not None else None,
            source=source if source else None,
        )

    def flat_to_semantic(self, flat_chunk: Dict[str, Any]) -> SemanticChunk:
        """Convert flat dictionary metadata to SemanticChunk model"""
        # tags: str -> List[str]
        tags = str_to_list(flat_chunk.get("tags", ""))
        # links: link_parent/link_related -> List[str]
        links = []
        if flat_chunk.get("link_parent"):
            links.append(f"parent:{flat_chunk['link_parent']}")
        if flat_chunk.get("link_related"):
            links.append(f"related:{flat_chunk['link_related']}")
        # source_lines_start/source_lines_end -> source_lines
        source_lines = None
        if flat_chunk.get("source_lines_start") is not None and flat_chunk.get("source_lines_end") is not None:
            source_lines = [flat_chunk["source_lines_start"], flat_chunk["source_lines_end"]]
        # Метрики (flat) -> ChunkMetrics + FeedbackMetrics
        metrics_fields = [
            "quality_score", "coverage", "cohesion", "boundary_prev", "boundary_next",
            "used_in_generation", "feedback_accepted", "feedback_rejected", "feedback_modifications"
        ]
        metrics_data = {k: flat_chunk.get(k) for k in metrics_fields if k in flat_chunk}
        from chunk_metadata_adapter.semantic_chunk import ChunkMetrics, FeedbackMetrics
        feedback_kwargs = {}
        for k in ["feedback_accepted", "feedback_rejected", "feedback_modifications"]:
            if k in metrics_data:
                feedback_kwargs[k.replace("feedback_", "")] = metrics_data.pop(k)
        metrics = None
        if any(metrics_data.values()) or any(feedback_kwargs.values()):
            if feedback_kwargs:
                metrics_data["feedback"] = FeedbackMetrics(**feedback_kwargs)
            metrics = ChunkMetrics(**metrics_data)
        # block_meta: flat dict -> dict
        block_meta = from_flat_dict(flat_chunk.get("block_meta", {}) or {}) if "block_meta" in flat_chunk else {}
        # Собираем все поля
        chunk_data = {k: v for k, v in flat_chunk.items() if k in SemanticChunk.model_fields}
        # Гарантируем, что body всегда строка
        if chunk_data.get("body") is None:
            chunk_data["body"] = ""
        chunk_data.update({
            "tags": tags,
            "links": links,
            "source_lines": source_lines,
            "metrics": metrics,
            "block_meta": block_meta
        })
        return SemanticChunk(**chunk_data)

    def semantic_to_flat(self, chunk: SemanticChunk) -> Dict[str, Any]:
        """Convert SemanticChunk model to flat dictionary format"""
        from chunk_metadata_adapter.utils import list_to_str, to_flat_dict
        d = chunk.model_dump()
        # tags: List[str] -> str
        d["tags"] = list_to_str(chunk.tags) if chunk.tags else ""
        # links: List[str] -> link_parent/link_related
        d["link_parent"] = None
        d["link_related"] = None
        if chunk.links:
            for l in chunk.links:
                if l.startswith("parent:"):
                    d["link_parent"] = l.split(":", 1)[1]
                elif l.startswith("related:"):
                    d["link_related"] = l.split(":", 1)[1]
        # source_lines: [start, end] -> source_lines_start/source_lines_end
        if chunk.source_lines:
            d["source_lines_start"] = chunk.source_lines[0]
            d["source_lines_end"] = chunk.source_lines[1]
        # sha256: если отсутствует или пустой — вычислить по body (или text)
        if not d.get("sha256"):
            body_val = getattr(chunk, "body", None) or getattr(chunk, "text", "")
            d["sha256"] = self.compute_sha256(body_val)
        # Метрики (ChunkMetrics) -> flat
        if chunk.metrics:
            d.update(chunk.metrics.model_dump())
            # Явно сериализуем feedback
            if hasattr(chunk.metrics, "feedback") and chunk.metrics.feedback:
                d["feedback_accepted"] = chunk.metrics.feedback.accepted
                d["feedback_rejected"] = chunk.metrics.feedback.rejected
                d["feedback_modifications"] = chunk.metrics.feedback.modifications
        # block_meta: dict -> flat dict
        if chunk.block_meta:
            d["block_meta"] = to_flat_dict(chunk.block_meta)
        return d
