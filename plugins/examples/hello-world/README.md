# Hello World

A minimal example of a trusted local Patchbay plugin.

```bash
uv run patchbay plugin validate plugins/examples/hello-world
uv run patchbay plugin run org.patchbay.examples.hello-world --input '{"name":"Developer"}'
```

Do not use the in-process loader for untrusted code.
