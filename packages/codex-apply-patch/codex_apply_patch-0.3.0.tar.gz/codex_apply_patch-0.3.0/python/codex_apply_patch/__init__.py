"""
Codex Apply Patch - Python library for applying patches using a custom format.

This library provides functionality to parse and apply patches in a custom format
designed for AI coding assistants.
"""

# Import the Rust module
from . import codex_apply_patch as _rust_module

# Expose the functions with cleaner names
apply_patch = _rust_module.py_apply_patch
apply_patch_in_memory = _rust_module.py_apply_patch_in_memory
parse_patch = _rust_module.py_parse_patch
get_tool_instructions = _rust_module.py_get_tool_instructions
get_api_instructions = _rust_module.py_get_api_instructions

# Expose the classes with cleaner names
ApplyPatchError = _rust_module.PyApplyPatchError
InMemoryPatchResult = _rust_module.PyInMemoryPatchResult

__version__ = "0.3.0"
__all__ = [
    "apply_patch",
    "apply_patch_in_memory", 
    "parse_patch",
    "get_tool_instructions",
    "get_api_instructions",
    "ApplyPatchError",
    "InMemoryPatchResult",
] 