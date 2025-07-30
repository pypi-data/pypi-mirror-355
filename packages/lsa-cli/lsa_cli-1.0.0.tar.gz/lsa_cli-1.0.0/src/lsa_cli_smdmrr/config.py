import json
import os
from enum import Enum
from typing import Any

from structlog import BoundLogger, get_logger

logger: BoundLogger = get_logger()


class AnnotationType(Enum):
    PREFIX = "@lc-"
    IDENTIFIER = "identifier"
    NAME = "name"
    TYPE = "type"
    DESCRIPTION = "description"
    ENTITY = "entity"
    PROPERTY = "property"
    METHOD = "method"
    SOURCE = "source"


class Config:
    DEFAULT_CONFIG_PATH: str = ".lsa-config.json"
    extensions_map: dict[str, str] = {
        "ts": "application/javascript",
        "js": "application/javascript",
        "py": "text/x-python",
        "html": "text/html",
        "java": "text/x-java-source",
        "c": "text/x-c",
        "h": "text/x-c",
        "cpp": "text/x-c++",
        "hpp": "text/x-c++",
        "xml": "text/xml",
    }
    annotations_markers_map: dict[AnnotationType, str] = {
        annotation_type: annotation_type.value for annotation_type in AnnotationType
    }
    output_entities_file: str = "lsa-entities.json"
    output_annotations_file: str = "lsa-annotations.json"
    parser_exclude: list[str] = []

    def __init__(
        self,
        output_entities_file: str = output_entities_file,
        output_annotations_file: str = output_annotations_file,
        parser_exclude: list[str] = parser_exclude,
        parser_extend: dict[str, str] = {},
        user_markers: dict[str, str] = {},
    ):
        self.output_entities_file = output_entities_file
        self.output_annotations_file = output_annotations_file
        self.parser_exclude = parser_exclude
        self.extensions_map.update(parser_extend)
        for annotation_type in AnnotationType:
            self.annotations_markers_map[annotation_type] = user_markers.get(
                annotation_type.name.lower(), self.annotations_markers_map[annotation_type]
            )

    @classmethod
    def from_file(cls, path: str) -> "Config":
        if not os.path.exists(path):
            logger.warning(f"Config file '{path}' not found, using default configuration.")
            return Config()

        with open(path) as f:
            user_config: dict[Any, Any] = json.load(f)

        parser: dict[Any, Any] = user_config.get("parser", {})
        output: dict[Any, Any] = parser.get("output", {})
        config: Config = Config(
            output_entities_file=output.get("entities", cls.output_entities_file),
            output_annotations_file=output.get("annotations", cls.output_annotations_file),
            parser_exclude=parser.get("exclude", cls.parser_exclude),
            parser_extend=parser.get("extend", {}),
            user_markers=user_config.get("markers", {}),
        )

        return config
