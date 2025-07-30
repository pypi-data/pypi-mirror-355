#!/usr/bin/env python3
"""
Example usage of the codex-apply-patch Python library.

This script demonstrates the main functionality of the library.
"""

import codex_apply_patch as cap
import tempfile
import os


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===")
    
    # Create a simple patch
    patch = """*** Begin Patch
*** Add File: hello.py
+def greet(name):
+    print(f"Hello, {name}!")
+
+if __name__ == "__main__":
+    greet("World")
*** End Patch"""

    print("Patch to apply:")
    print(patch)
    print()

    # Parse the patch to understand its structure
    hunks = cap.parse_patch(patch)
    print(f"Patch contains: {hunks}")
    print()

    # Apply the patch to disk (in a temporary directory)
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = cap.apply_patch(patch)
            print("Apply result:")
            print(result)
            print()
            
            # Verify the file was created
            if os.path.exists("hello.py"):
                with open("hello.py", "r") as f:
                    content = f.read()
                print("Created file content:")
                print(content)
        finally:
            os.chdir(original_cwd)


def example_in_memory_usage():
    """In-memory usage example."""
    print("\n=== In-Memory Usage Example ===")
    
    # Start with some files in memory
    files = {
        "main.py": """def main():
    print("Original version")

if __name__ == "__main__":
    main()
""",
        "utils.py": """def helper():
    return "original helper"
""",
    }

    print("Original files:")
    for path, content in files.items():
        print(f"--- {path} ---")
        print(content)

    # Create a patch that modifies existing files and adds a new one
    patch = """*** Begin Patch
*** Update File: main.py
@@
 def main():
-    print("Original version")
+    print("Updated version!")
+    print("With new functionality")

*** Update File: utils.py
@@
 def helper():
-    return "original helper"
+    return "enhanced helper with new features"

*** Add File: config.py
+DEBUG = True
+VERSION = "1.0.0"
+
+def get_config():
+    return {"debug": DEBUG, "version": VERSION}
*** End Patch"""

    print("\nApplying patch...")
    result = cap.apply_patch_in_memory(patch, files)
    
    print(f"\nPatch application summary:")
    print(f"- Files added: {result.added}")
    print(f"- Files modified: {result.modified}")
    print(f"- Files deleted: {result.deleted}")
    
    print(f"\nFiles after patch application:")
    for path, content in result.files.items():
        print(f"--- {path} ---")
        print(content)


def example_error_handling():
    """Error handling example."""
    print("\n=== Error Handling Example ===")
    
    # Try to apply a malformed patch
    bad_patch = """*** Begin Patch
*** Invalid Operation: some_file.py
This is not a valid patch format
*** End Patch"""

    try:
        cap.parse_patch(bad_patch)
    except Exception as e:
        print(f"Caught expected error: {e}")

    # Try to update a non-existent file in memory
    empty_files = {}
    patch_for_missing_file = """*** Begin Patch
*** Update File: nonexistent.py
@@
-some content
+new content
*** End Patch"""

    try:
        cap.apply_patch_in_memory(patch_for_missing_file, empty_files)
    except Exception as e:
        print(f"Caught expected error: {e}")


def example_tool_instructions():
    """Show the tool instructions."""
    print("\n=== Tool Instructions ===")
    
    instructions = cap.get_tool_instructions()
    print("Tool instructions (first 500 chars):")
    print(instructions[:500] + "..." if len(instructions) > 500 else instructions)


if __name__ == "__main__":
    print("Codex Apply Patch - Python Library Example")
    print("=" * 50)
    
    example_basic_usage()
    example_in_memory_usage() 
    example_error_handling()
    example_tool_instructions()
    
    print("\n" + "=" * 50)
    print("Example completed successfully!") 