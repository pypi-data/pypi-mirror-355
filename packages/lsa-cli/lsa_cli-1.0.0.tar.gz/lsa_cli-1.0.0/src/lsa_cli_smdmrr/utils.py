import json
from typing import Any

from lsa_cli_smdmrr.models import Entity, SourceFileAnnotations


def export_annotations_to_json(model: list[SourceFileAnnotations], file: str) -> None:
    with open(file, "w") as f:
        json.dump(
            {"filesAnnotations": [file_annotation.to_json() for file_annotation in model]},
            f,
            indent=4,
        )


def export_entities_to_json(entities: list[Entity], file: str) -> None:
    with open(file, "w") as f:
        json.dump({"entities": [entity.to_json() for entity in entities]}, f, indent=4)


def import_entities_from_json(file: str) -> list[Entity]:
    with open(file, "r") as f:
        json_file: dict[str, Any] = json.loads(f.read())
        return [Entity.from_json(entity_json) for entity_json in json_file["entities"]]
