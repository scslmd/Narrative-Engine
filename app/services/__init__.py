"""Service package.

Keep package initialization lightweight so submodule imports do not trigger
unrelated runtime dependencies and circular imports.
"""

__all__: list[str] = []
