# Path Template Worker

Updates document path (and title) based on DocumentType.path_template


## Install Deps

    uv sync

## Run Tests

    uv sync --extra dev
    pytest


## Start Worker

    uv run task worker

## Example of .envok.yaml Config

```yaml
dev:
  PAPERMERGE__DATABASE__URL: postgresql://eugen:eugen@127.0.0.1:5432/paperdb
  PAPERMERGE__REDIS__URL: redis://localhost:6379/0
  PAPERMERGE__MAIN__LOGGING_CFG: /home/eugen/Projects/PathTmplWorker/logging.yaml

dev_no_redis:
  PAPERMERGE__DATABASE__URL: postgresql://eugen:eugen@127.0.0.1:5432/paperdb

test:
  PAPERMERGE__DATABASE__URL: postgresql://pmguser:pmgpass@127.0.0.1:5432/pmgdb_test
```
