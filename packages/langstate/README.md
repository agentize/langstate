# LangState

LangState is a Python library for managing state in language-driven applications.
It models state as a schema-backed graph and keeps two synchronized views:
interpretive state (inferences + confidence) and canonical state (resolved values).
The core `LangState` orchestrator wires together spec extractors, mutators,
projectors, and actions to move from user input to validated state and UI output.

For architecture details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
