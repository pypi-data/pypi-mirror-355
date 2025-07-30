import os

import structlog
from comment_parser import comment_parser  # type: ignore[import-untyped]
from comment_parser.parsers.common import Comment  # type: ignore[import-untyped]

from .models import Annotation, SourceFileAnnotations

logger: structlog.BoundLogger = structlog.get_logger()


class AnnotationParser:
    def __init__(
        self,
        parser_exclude: list[str],
        annotation_prefix: str,
        extensions_map: dict[str, str],
    ) -> None:
        self.parser_exclude: list[str] = parser_exclude
        self.annotation_prefix: str = annotation_prefix
        self.extensions_map: dict[str, str] = extensions_map

    def parse(self, path: str) -> list[SourceFileAnnotations]:
        if any(ex in path for ex in self.parser_exclude):
            return []

        if os.path.isfile(path):
            annotation: SourceFileAnnotations | None = self._parse_file(path)
            return [annotation] if annotation and len(annotation.annotations) > 0 else []

        elif os.path.isdir(path):
            sourceFileAnnotations: list[SourceFileAnnotations] = []
            for root, _, files in os.walk(path):
                for file in files:
                    sourceFileAnnotations.extend(self.parse(os.path.join(root, file)))
            return sourceFileAnnotations
        else:
            raise ValueError(f"Invalid path: {path}")

    def _parse_file(self, path: str) -> SourceFileAnnotations | None:
        try:
            return SourceFileAnnotations(
                relative_file_path=path,
                annotations=[
                    annotation
                    for comment in self._parse_comments(path)
                    if (annotation := self._convert_comment_to_annotation(comment))
                ],
            )
        except Exception as e:
            logger.debug(f"Error parsing file: {path}: {e}")
        return None

    def _parse_comments(self, path: str) -> list[Comment]:
        file_extension: str = os.path.splitext(path)[1].lstrip(".")
        mime: str | None = self.extensions_map.get(file_extension, None)
        comments: list[Comment] = comment_parser.extract_comments(path, mime)
        return comments

    def _convert_comment_to_annotation(self, comment: Comment) -> Annotation | None:
        tokens: list[str] = comment.text().strip().split(" ")

        annotation: str = tokens[0].strip()
        if not annotation.startswith(self.annotation_prefix):
            return None

        annotation_name: str = annotation[len(self.annotation_prefix) :]
        value: str | None = " ".join(tokens[1:]) if len(tokens) > 1 else None
        return Annotation(name=annotation_name, value=value, line_number=comment.line_number())
