# Codex Apply Patch

A CLI tool and Python library for applying patches using a custom patch format designed for AI coding assistants.

This project is based on [OpenAI's original codex apply-patch tool](https://github.com/openai/codex/tree/main/codex-rs/apply-patch) and extends it with additional functionality.

## Changes from Original

This fork adds the following enhancements to the original OpenAI tool:

1. **In-Memory Patch Application**: New functionality to apply patches to files in memory without touching the filesystem, useful for testing and preview scenarios.

2. **Python Library Support**: Complete Python bindings using PyO3, allowing the patch functionality to be used directly from Python code.

3. **PyPI Distribution**: The library is packaged and distributed via PyPI for easy installation.

## Installation

### Python Package

```bash
pip install codex-apply-patch
```

### From Source

```bash
# Install Rust if you haven't already
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Clone and build
git clone https://github.com/openai/codex-apply-patch
cd codex-apply-patch
cargo build --release

# For Python development
pip install maturin
maturin develop --release
```

## Usage

### Command Line

```bash
# Apply patch from stdin
echo "*** Begin Patch
*** Add File: hello.txt
+Hello, World!
*** End Patch" | codex_apply_patch
```

### Python Library

```python
import codex_apply_patch as cap

# Apply patch to files on disk
patch = """*** Begin Patch
*** Add File: hello.py
+print("Hello, World!")
*** End Patch"""

result = cap.apply_patch(patch)
print(result)

# Apply patch in memory (new feature)
files = {
    "main.py": "def main():\n    print('old version')\n"
}

patch = """*** Begin Patch
*** Update File: main.py
@@
 def main():
-    print('old version')
+    print('new version')
*** End Patch"""

result = cap.apply_patch_in_memory(patch, files)
print("Modified files:", result.files)
print("Summary:", f"Added: {len(result.added)}, Modified: {len(result.modified)}, Deleted: {len(result.deleted)}")
```

### Python API Reference

- `apply_patch(patch_str)` - Apply patch to files on disk
- `apply_patch_in_memory(patch_str, files_dict)` - Apply patch to in-memory files 
- `parse_patch(patch_str)` - Parse patch and return structure information
- `get_tool_instructions()` - Get the CLI tool instructions for AI assistants
- `get_api_instructions()` - Get the patch format instructions (without CLI specifics)

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

This project extends the original OpenAI codex apply-patch tool, which is also licensed under Apache-2.0.
