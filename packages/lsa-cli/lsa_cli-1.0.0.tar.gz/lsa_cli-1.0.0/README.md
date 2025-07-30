# LSA (Linking Software Artifacts) CLI

[![Version](https://img.shields.io/pypi/v/lsa-cli?logo=pypi)](https://pypi.org/project/lsa-cli)
[![Python Version](https://img.shields.io/pypi/pyversions/lsa-cli?logo=python&logoColor=white)](https://pypi.org/project/lsa-cli)

The part of [LSA](https://github.com/MarkSeliverstov/MFF-bachelor-work) project,
this CLI tool is used to parse `annotations` from source code and convert them
to `entities`. Entities are then used to visualize the codebase on the
[webpage](https://markseliverstov.github.io/MFF-bachelor-work).

## Installation

```bash
pip install lsa-cli
```

## Usage

```bash
lsa-cli <option>
```

**Options:**

```bash
-p, --path          Parse path
-a, --annotations  Save intermediate annotations model as JSON
-c, --config       Path to the configuration file
-v, --validate     Validate and compare two model files (JSON). Provide two file paths.
```

### Example

The CLI tool parses the source code:

```typescript
// @lc-entity
// @lc-identifier :Annotation
// @lc-name Annotation
// @lc-description Base class for all annotations.
export interface IAnnotation {
  // @lc-property
  // @lc-name name
  name: string
  // @lc-property
  // @lc-name value
  value: string | null
  // @lc-property
  // @lc-name annotationStartPos
  startPos: number
  // @lc-property
  // @lc-name annotationEndPos
  endPos: number
  // @lc-property
  // @lc-name annotationLine
  lineNumber: number
}
```

And generates the entities model by `lsa-cli -p source-file.ts`:

```json
{
  "entities": [
    {
      "name": "Annotation",
      "instances": [
        {
          "from_file": "source-file.ts",
          "identifier": ":Annotation",
          "description": "Base class for all annotations.",
          "properties": [
            {
              "name": "name",
              "description": null
            },
            {
              "name": "value",
              "description": null
            },
            {
              "name": "annotationstartpos",
              "description": null
            },
            {
              "name": "annotationendpos",
              "description": null
            },
            {
              "name": "annotationline",
              "description": null
            }
          ]
        }
      ]
    }
  ]
}
```

<details>
<summary>
Additionally, you can save the intermediate annotations model as JSON:
</summary>

```json
{
    "filesAnnotations": [
        {
            "relativeFilePath": "./source-file.ts",
            "annotations": [
                {
                    "name": "entity",
                    "value": null,
                    "lineNumber": 1
                },
                {
                    "name": "identifier",
                    "value": ":Annotation",
                    "lineNumber": 2
                },
                {
                    "name": "name",
                    "value": "Annotation",
                    "lineNumber": 3
                },
        ...
```

</details>

## Configuration file

Default configuration file is `.lsa-config.json` in the current working directory.
You can specify the path to the configuration file using the `-c` option.

```bash
lsa-cli -c <path-to-config-file> -p <path-to-source-code>
```

If the file is not found, default configuration is used:

```json
{
  "markers": {
    "prefix": "@lc-",
    "identifier": "identifier",
    "name": "name",
    "type": "type",
    "description": "description",
    "entity": "entity",
    "property": "property",
    "method": "method",
    "source": "source"
  },
  "parser": {
    "output": {
      "entities": "entities.json",
      "annotations": "annotations.json"
    },
    "exclude": [],
    "extend": {}
  },
}
```

- `<prefix><marker>` - Defines the annotations, where
  - `prefix` - Prefix for the annotations.
  - `markers` - Annotation markers (for example, `<prefix>entity`).
- `parser` - Parser settings for the CLI.
  - `output` - Output files for the CLI.
  - `exclude` - Paths to exclude from parsing.

    ```json
    "exclude": ["node_modules", ".git", ".venv"]
    ```

  - `extend` - File extensions to extend the parser. Where the key is the
    extension and the value is the MIME type ( you can see the list of supported
    MIME types [here](https://github.com/jeanralphaviles/comment_parser)).

    ```json
    "extend": {
      "cjs": "application/javascript",
      "mjs": "application/javascript",
      "jsx": "application/javascript"
    }
    ```

## Development

<details>

### Installation

```bash
poetry install
```

### Usage

```bash
poetry run lsa-cli
```

### Testing

```bash
pytest -c pyproject.toml
```

### Formatting

```bash
poetry run poe format-code
```

### Pre-commit

```bash
poetry shell
pre-commit install
```

</details>
