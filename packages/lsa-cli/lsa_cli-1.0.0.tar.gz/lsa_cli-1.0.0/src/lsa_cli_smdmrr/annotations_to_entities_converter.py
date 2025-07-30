from .config import AnnotationType
from .models import Entity, EntityInstance, Property, SourceFileAnnotations


class AnnotationsToEntitiesConverter:
    def __init__(self, annotations_markers_map: dict[AnnotationType, str]) -> None:
        self.annotations_markers_map: dict[AnnotationType, str] = annotations_markers_map
        self.entities: list[Entity] = []

    def _add_instance(self, name: str | None, instance: EntityInstance) -> None:
        entity: Entity | None = next(
            (entity for entity in self.entities if entity.name == name), None
        )
        if entity:
            entity.instances.append(instance)
        else:
            self.entities.append(Entity(name=name, instances=[instance]))

    def _convert_annotations_to_entities(self, annotations: list[SourceFileAnnotations]) -> None:
        current_instance: EntityInstance | None = None
        current_property: Property | None = None
        current_entity_name: str | None = None

        for file_annotation in annotations:
            current_file_path = file_annotation.relative_file_path

            for annotation in file_annotation.annotations:
                if annotation.name == self.annotations_markers_map[AnnotationType.ENTITY]:
                    if current_instance:
                        self._add_instance(current_entity_name, current_instance)
                    current_entity_name = None
                    current_property = None

                elif annotation.name == self.annotations_markers_map[AnnotationType.PROPERTY]:
                    if current_instance and current_property:
                        current_instance.properties.append(
                            Property(
                                name=current_property.name,
                                description=current_property.description,
                            )
                        )
                    current_property = Property(name=None, description=None)

                elif annotation.name == self.annotations_markers_map[AnnotationType.IDENTIFIER]:
                    assert annotation.value
                    current_instance = EntityInstance(
                        from_file=current_file_path, identifier=annotation.value, description=None
                    )

                elif annotation.name == self.annotations_markers_map[AnnotationType.NAME]:
                    if current_instance:
                        if current_property:
                            current_property.name = annotation.value
                        else:
                            current_entity_name = annotation.value

                elif annotation.name == self.annotations_markers_map[AnnotationType.DESCRIPTION]:
                    if current_instance:
                        if current_property:
                            current_property.description = annotation.value
                        else:
                            current_instance.description = annotation.value

        if current_instance:
            if current_property:
                current_instance.properties.append(
                    Property(
                        name=current_property.name,
                        description=current_property.description,
                    )
                )
            self._add_instance(current_entity_name, current_instance)

    def convert(self, annotations: list[SourceFileAnnotations]) -> list[Entity]:
        self.entities = []
        self._convert_annotations_to_entities(annotations)
        return self.entities
