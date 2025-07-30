from typing import Any

import structlog

from lsa_cli_smdmrr.models import Entity, EntityInstance, Property
from lsa_cli_smdmrr.utils import import_entities_from_json

logger: structlog.BoundLogger = structlog.get_logger()


def entity_key(entity: Entity) -> str:
    return entity.name or ""


def instance_key(instance: EntityInstance) -> str:
    return instance.identifier


def property_key(prop: Property) -> str:
    return f"{prop.name}:{prop.description}"


def print_diff(title: str, items: list[Any]) -> None:
    if items:
        print(f"{title}:")
        for item in items:
            print(f"  - {item}")


def validate(first_file_name: str, second_file_name: str) -> None:
    try:
        list1: list[Entity] = import_entities_from_json(first_file_name)
        list2: list[Entity] = import_entities_from_json(second_file_name)
    except Exception as exc:
        logger.error(f"Error when reading files:  {str(exc)}")
        return

    entities1 = {entity_key(e): e for e in list1}
    entities2 = {entity_key(e): e for e in list2}

    all_keys = set(entities1) | set(entities2)
    for key in sorted(all_keys):
        e1 = entities1.get(key)
        e2 = entities2.get(key)

        if e1 and not e2:
            print(f"Entity only in {first_file_name}: {key}")
        elif e2 and not e1:
            print(f"Entity only in {second_file_name}: {key}")
        else:
            assert e2 and e1, "Enitites should exist in this stage"

            i1_dict = {instance_key(i): i for i in e1.instances}
            i2_dict = {instance_key(i): i for i in e2.instances}
            all_instance_keys = set(i1_dict) | set(i2_dict)

            for ikey in sorted(all_instance_keys):
                inst1 = i1_dict.get(ikey)
                inst2 = i2_dict.get(ikey)

                if inst1 and not inst2:
                    print(f"Instance '{ikey}' only in {first_file_name} in entity '{key}'")
                elif inst2 and not inst1:
                    print(f"Instance '{ikey}' only in {second_file_name} in entity '{key}'")
                else:
                    assert inst1 and inst2, "instances should exist in this stage"

                    if inst1.description != inst2.description:
                        print(f"Different description in instance '{ikey}' of entity '{key}':")
                        print(f"  {first_file_name}: {inst1.description}")
                        print(f"  {first_file_name}: {inst2.description}")

                    p1 = {property_key(p) for p in inst1.properties}
                    p2 = {property_key(p) for p in inst2.properties}
                    only_in_1 = p1 - p2
                    only_in_2 = p2 - p1

                    if only_in_1 or only_in_2:
                        print(f"Different properties in instance '{ikey}' of entity '{key}':")
                        print_diff(f"  Properties only in {first_file_name}", list(only_in_1))
                        print_diff(f"  Properties only in {second_file_name}", list(only_in_2))

    print("Validation done.")
