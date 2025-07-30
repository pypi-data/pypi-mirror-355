## Apply Patch Format Instructions

This document describes the patch format for applying changes to files. Use this format when creating patches that modify, add, or delete files.

### Patch Structure

Every patch must begin with `*** Begin Patch` and end with `*** End Patch`:

```
*** Begin Patch
[YOUR_PATCH_CONTENT]
*** End Patch
```

### File Operations

The patch format supports three types of file operations:

#### Add File
```
*** Add File: path/to/file
+content line 1
+content line 2
+content line 3
```

#### Delete File
```
*** Delete File: path/to/file
```

#### Update File
```
*** Update File: path/to/file
[optional: *** Move to: new/path/to/file]
[change chunks]
```

### Change Chunks for Update Operations

For each section of code that needs to be changed, use this format:

```
[context_before]
- [old_code]
+ [new_code]  
[context_after]
```

### Context Guidelines

- **Default Context**: Show 3 lines of code immediately above and 3 lines immediately below each change
- **Avoid Duplication**: If changes are within 3 lines of each other, do NOT duplicate context lines between changes
- **Unique Identification**: If 3 lines of context is insufficient to uniquely identify the code location, use `@@` operators to specify the class or function context

### Using @@ Context Markers

#### Single Context Level
```
@@ class BaseClass
[3 lines of pre-context]
- [old_code]
+ [new_code]
[3 lines of post-context]
```

#### Multiple Context Levels  
```
@@ class BaseClass
@@ 	def method():
[3 lines of pre-context]
- [old_code]
+ [new_code]
[3 lines of post-context]
```

### Change Line Prefixes

- **Context lines** (unchanged): Prefix with ` ` (space)
- **Removed lines**: Prefix with `-` (minus)
- **Added lines**: Prefix with `+` (plus)

### Example Patch

```
*** Begin Patch
*** Update File: pygorithm/searching/binary_search.py
@@ class BaseClass
@@     def search():
-        pass
+        raise NotImplementedError()
@@ class Subclass  
@@     def search():
-        pass
+        raise NotImplementedError()
*** End Patch
```

### Path Requirements

- File paths must be relative, never absolute
- Use forward slashes `/` as path separators regardless of operating system

### Notes

- The format does not use line numbers - context is sufficient to uniquely identify code locations
- Empty lines can be represented without any prefix character
- For end-of-file operations, use `*** End of File` marker when needed 