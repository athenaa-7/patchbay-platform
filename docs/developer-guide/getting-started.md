# Getting started

## Requirements
- Python 3.12 or newer
- uv
- Git

## Set up
```bash
git clone https://github.com/athenaa-7/patchbay-platform.git
cd patchbay-platform
uv sync --all-packages
```

## Validate and run the example
```bash
uv run patchbay plugin list
uv run patchbay plugin validate plugins/examples/hello-world
uv run patchbay plugin run org.patchbay.examples.hello-world --input '{"name":"Developer"}'
```

Only run plugins you trust. Phase 1 imports plugin code into the current Python process and does not sandbox it.
