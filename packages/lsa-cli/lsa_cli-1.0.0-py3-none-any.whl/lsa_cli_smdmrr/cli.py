import logging
import os
from argparse import ArgumentParser, Namespace

import structlog

from lsa_cli_smdmrr.models import Entity, SourceFileAnnotations
from lsa_cli_smdmrr.utils import export_annotations_to_json, export_entities_to_json
from lsa_cli_smdmrr.validator import validate

from .annotation_parser import AnnotationParser
from .annotations_to_entities_converter import AnnotationsToEntitiesConverter
from .config import AnnotationType, Config

logger: structlog.BoundLogger = structlog.get_logger()
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))


def _parse_and_convert(args: Namespace, config: Config) -> None:
    if not os.path.exists(args.path):
        logger.error(f"Path not found: '{args.path}'")
        return

    parser: AnnotationParser = AnnotationParser(
        config.parser_exclude,
        config.annotations_markers_map[AnnotationType.PREFIX],
        config.extensions_map,
    )

    logger.debug(f"Parsing all annotations from source code from '{args.path}'")
    model: list[SourceFileAnnotations] = parser.parse(args.path)
    if not model:
        logger.debug("No annotations found...")
        return
    logger.debug(f"Found {len(model)} files with annotations")

    if args.annotations:
        export_annotations_to_json(model, config.output_annotations_file)
        logger.debug(f"Annotations saved to '{config.output_annotations_file}'")

    logger.debug("Converting annotations to entities")
    converter: AnnotationsToEntitiesConverter = AnnotationsToEntitiesConverter(
        config.annotations_markers_map
    )
    entities: list[Entity] = converter.convert(model)
    logger.debug(f"Found {len(entities)} entities")
    export_entities_to_json(entities, config.output_entities_file)
    logger.debug(f"Entities saved to '{config.output_entities_file}'")

    print(
        f"Found {len(model)} files with annotations that were converted to {len(entities)} entities."
    )
    print(f"    - entities saved to {config.output_entities_file}")
    if args.annotations:
        print(f"    - annotations saved to {config.output_annotations_file}")
    print(
        "You can use these entities/annotations to visualize them on the webpage: https://markseliverstov.github.io/MFF-bachelor-work"
    )


def run() -> None:
    try:
        parser: ArgumentParser = ArgumentParser(
            description="Parses annotations from source code and convert them to entities."
        )
        parser.add_argument(
            "-p",
            "--path",
            help="Path to file or directory to parse",
            type=str,
        )
        parser.add_argument(
            "-c",
            "--config",
            help="Path to the configuration file",
            type=str,
        )
        parser.add_argument(
            "-a",
            "--annotations",
            help="Parsed annotations will be saved to file if this flag is set",
            action="store_true",
        )
        parser.add_argument(
            "-v",
            "--validate",
            help="Validate and compare two model files (JSON). Provide two file paths.",
            nargs=2,
            metavar=("FILE1", "FILE2"),
            type=str,
        )

        args: Namespace = parser.parse_args()
        if args.validate:
            validate(*args.validate)
            return

        config: Config = (
            Config.from_file(args.config)
            if args.config
            else Config.from_file(Config.DEFAULT_CONFIG_PATH)
        )
        _parse_and_convert(args, config)
    except KeyboardInterrupt:
        pass
