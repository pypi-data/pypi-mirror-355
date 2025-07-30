mod parser;
mod seek_sequence;

use std::collections::HashMap;
use std::path::Path;
use std::path::PathBuf;
use std::str::Utf8Error;

use anyhow::Context;
use anyhow::Result;
pub use parser::Hunk;
pub use parser::ParseError;
use parser::ParseError::*;
use parser::UpdateFileChunk;
pub use parser::parse_patch;
use similar::TextDiff;
use thiserror::Error;
use tree_sitter::LanguageError;
use tree_sitter::Parser;
use tree_sitter_bash::LANGUAGE as BASH;

/// Detailed instructions for gpt-4.1 on how to use the `apply_patch` tool.
pub const APPLY_PATCH_TOOL_INSTRUCTIONS: &str = include_str!("../apply_patch_tool_instructions.md");

/// Instructions for using the apply_patch format directly with the API (without shell/CLI).
pub const APPLY_PATCH_API_INSTRUCTIONS: &str = include_str!("../apply_patch_api_instructions.md");

#[derive(Debug, Error, PartialEq)]
pub enum ApplyPatchError {
    #[error(transparent)]
    ParseError(#[from] ParseError),
    #[error(transparent)]
    IoError(#[from] IoError),
    /// Error that occurs while computing replacements when applying patch chunks
    #[error("{0}")]
    ComputeReplacements(String),
}

impl From<std::io::Error> for ApplyPatchError {
    fn from(err: std::io::Error) -> Self {
        ApplyPatchError::IoError(IoError {
            context: "I/O error".to_string(),
            source: err,
        })
    }
}

#[derive(Debug, Error)]
#[error("{context}: {source}")]
pub struct IoError {
    context: String,
    #[source]
    source: std::io::Error,
}

impl PartialEq for IoError {
    fn eq(&self, other: &Self) -> bool {
        self.context == other.context && self.source.to_string() == other.source.to_string()
    }
}

#[derive(Debug, PartialEq)]
pub enum MaybeApplyPatch {
    Body(Vec<Hunk>),
    ShellParseError(ExtractHeredocError),
    PatchParseError(ParseError),
    NotApplyPatch,
}

pub fn maybe_parse_apply_patch(argv: &[String]) -> MaybeApplyPatch {
    match argv {
        [cmd, body] if cmd == "apply_patch" => match parse_patch(body) {
            Ok(hunks) => MaybeApplyPatch::Body(hunks),
            Err(e) => MaybeApplyPatch::PatchParseError(e),
        },
        [bash, flag, script]
            if bash == "bash"
                && flag == "-lc"
                && script.trim_start().starts_with("apply_patch") =>
        {
            match extract_heredoc_body_from_apply_patch_command(script) {
                Ok(body) => match parse_patch(&body) {
                    Ok(hunks) => MaybeApplyPatch::Body(hunks),
                    Err(e) => MaybeApplyPatch::PatchParseError(e),
                },
                Err(e) => MaybeApplyPatch::ShellParseError(e),
            }
        }
        _ => MaybeApplyPatch::NotApplyPatch,
    }
}

#[derive(Debug, PartialEq)]
pub enum ApplyPatchFileChange {
    Add {
        content: String,
    },
    Delete,
    Update {
        unified_diff: String,
        move_path: Option<PathBuf>,
        /// new_content that will result after the unified_diff is applied.
        new_content: String,
    },
}

#[derive(Debug, PartialEq)]
pub enum MaybeApplyPatchVerified {
    /// `argv` corresponded to an `apply_patch` invocation, and these are the
    /// resulting proposed file changes.
    Body(ApplyPatchAction),
    /// `argv` could not be parsed to determine whether it corresponds to an
    /// `apply_patch` invocation.
    ShellParseError(ExtractHeredocError),
    /// `argv` corresponded to an `apply_patch` invocation, but it could not
    /// be fulfilled due to the specified error.
    CorrectnessError(ApplyPatchError),
    /// `argv` decidedly did not correspond to an `apply_patch` invocation.
    NotApplyPatch,
}

#[derive(Debug, PartialEq)]
/// ApplyPatchAction is the result of parsing an `apply_patch` command. By
/// construction, all paths should be absolute paths.
pub struct ApplyPatchAction {
    changes: HashMap<PathBuf, ApplyPatchFileChange>,
}

impl ApplyPatchAction {
    pub fn is_empty(&self) -> bool {
        self.changes.is_empty()
    }

    /// Returns the changes that would be made by applying the patch.
    pub fn changes(&self) -> &HashMap<PathBuf, ApplyPatchFileChange> {
        &self.changes
    }

    /// Should be used exclusively for testing. (Not worth the overhead of
    /// creating a feature flag for this.)
    pub fn new_add_for_test(path: &Path, content: String) -> Self {
        if !path.is_absolute() {
            panic!("path must be absolute");
        }

        let changes = HashMap::from([(path.to_path_buf(), ApplyPatchFileChange::Add { content })]);
        Self { changes }
    }
}

/// cwd must be an absolute path so that we can resolve relative paths in the
/// patch.
pub fn maybe_parse_apply_patch_verified(argv: &[String], cwd: &Path) -> MaybeApplyPatchVerified {
    match maybe_parse_apply_patch(argv) {
        MaybeApplyPatch::Body(hunks) => {
            let mut changes = HashMap::new();
            for hunk in hunks {
                let path = hunk.resolve_path(cwd);
                match hunk {
                    Hunk::AddFile { contents, .. } => {
                        changes.insert(path, ApplyPatchFileChange::Add { content: contents });
                    }
                    Hunk::DeleteFile { .. } => {
                        changes.insert(path, ApplyPatchFileChange::Delete);
                    }
                    Hunk::UpdateFile {
                        move_path, chunks, ..
                    } => {
                        let ApplyPatchFileUpdate {
                            unified_diff,
                            content: contents,
                        } = match unified_diff_from_chunks(&path, &chunks) {
                            Ok(diff) => diff,
                            Err(e) => {
                                return MaybeApplyPatchVerified::CorrectnessError(e);
                            }
                        };
                        changes.insert(
                            path,
                            ApplyPatchFileChange::Update {
                                unified_diff,
                                move_path: move_path.map(|p| cwd.join(p)),
                                new_content: contents,
                            },
                        );
                    }
                }
            }
            MaybeApplyPatchVerified::Body(ApplyPatchAction { changes })
        }
        MaybeApplyPatch::ShellParseError(e) => MaybeApplyPatchVerified::ShellParseError(e),
        MaybeApplyPatch::PatchParseError(e) => MaybeApplyPatchVerified::CorrectnessError(e.into()),
        MaybeApplyPatch::NotApplyPatch => MaybeApplyPatchVerified::NotApplyPatch,
    }
}

/// Attempts to extract a heredoc_body object from a string bash command like:
/// Optimistically
///
/// ```bash
/// bash -lc 'apply_patch <<EOF\n***Begin Patch\n...EOF'
/// ```
///
/// # Arguments
///
/// * `src` - A string slice that holds the full command
///
/// # Returns
///
/// This function returns a `Result` which is:
///
/// * `Ok(String)` - The heredoc body if the extraction is successful.
/// * `Err(anyhow::Error)` - An error if the extraction fails.
///
fn extract_heredoc_body_from_apply_patch_command(
    src: &str,
) -> std::result::Result<String, ExtractHeredocError> {
    if !src.trim_start().starts_with("apply_patch") {
        return Err(ExtractHeredocError::CommandDidNotStartWithApplyPatch);
    }

    let lang = BASH.into();
    let mut parser = Parser::new();
    parser
        .set_language(&lang)
        .map_err(ExtractHeredocError::FailedToLoadBashGrammar)?;
    let tree = parser
        .parse(src, None)
        .ok_or(ExtractHeredocError::FailedToParsePatchIntoAst)?;

    let bytes = src.as_bytes();
    let mut c = tree.root_node().walk();

    loop {
        let node = c.node();
        if node.kind() == "heredoc_body" {
            let text = node
                .utf8_text(bytes)
                .map_err(ExtractHeredocError::HeredocNotUtf8)?;
            return Ok(text.trim_end_matches('\n').to_owned());
        }

        if c.goto_first_child() {
            continue;
        }
        while !c.goto_next_sibling() {
            if !c.goto_parent() {
                return Err(ExtractHeredocError::FailedToFindHeredocBody);
            }
        }
    }
}

#[derive(Debug, PartialEq)]
pub enum ExtractHeredocError {
    CommandDidNotStartWithApplyPatch,
    FailedToLoadBashGrammar(LanguageError),
    HeredocNotUtf8(Utf8Error),
    FailedToParsePatchIntoAst,
    FailedToFindHeredocBody,
}

/// Applies the patch and prints the result to stdout/stderr.
pub fn apply_patch(
    patch: &str,
    stdout: &mut impl std::io::Write,
    stderr: &mut impl std::io::Write,
) -> Result<(), ApplyPatchError> {
    let hunks = match parse_patch(patch) {
        Ok(hunks) => hunks,
        Err(e) => {
            match &e {
                InvalidPatchError(message) => {
                    writeln!(stderr, "Invalid patch: {message}").map_err(ApplyPatchError::from)?;
                }
                InvalidHunkError {
                    message,
                    line_number,
                } => {
                    writeln!(
                        stderr,
                        "Invalid patch hunk on line {line_number}: {message}"
                    )
                    .map_err(ApplyPatchError::from)?;
                }
            }
            return Err(ApplyPatchError::ParseError(e));
        }
    };

    apply_hunks(&hunks, stdout, stderr)?;

    Ok(())
}

/// Applies hunks and continues to update stdout/stderr
pub fn apply_hunks(
    hunks: &[Hunk],
    stdout: &mut impl std::io::Write,
    stderr: &mut impl std::io::Write,
) -> Result<(), ApplyPatchError> {
    let _existing_paths: Vec<&Path> = hunks
        .iter()
        .filter_map(|hunk| match hunk {
            Hunk::AddFile { .. } => {
                // The file is being added, so it doesn't exist yet.
                None
            }
            Hunk::DeleteFile { path } => Some(path.as_path()),
            Hunk::UpdateFile {
                path, move_path, ..
            } => match move_path {
                Some(move_path) => {
                    if std::fs::metadata(move_path)
                        .map(|m| m.is_file())
                        .unwrap_or(false)
                    {
                        Some(move_path.as_path())
                    } else {
                        None
                    }
                }
                None => Some(path.as_path()),
            },
        })
        .collect::<Vec<&Path>>();

    // Delegate to a helper that applies each hunk to the filesystem.
    match apply_hunks_to_files(hunks) {
        Ok(affected) => {
            print_summary(&affected, stdout).map_err(ApplyPatchError::from)?;
        }
        Err(err) => {
            writeln!(stderr, "{err:?}").map_err(ApplyPatchError::from)?;
        }
    }

    Ok(())
}

/// Applies each parsed patch hunk to the filesystem.
/// Returns an error if any of the changes could not be applied.
/// Tracks file paths affected by applying a patch.
#[derive(Debug, PartialEq)]
pub struct AffectedPaths {
    pub added: Vec<PathBuf>,
    pub modified: Vec<PathBuf>,
    pub deleted: Vec<PathBuf>,
}

/// Apply the hunks to the filesystem, returning which files were added, modified, or deleted.
/// Returns an error if the patch could not be applied.
fn apply_hunks_to_files(hunks: &[Hunk]) -> anyhow::Result<AffectedPaths> {
    if hunks.is_empty() {
        anyhow::bail!("No files were modified.");
    }

    let mut added: Vec<PathBuf> = Vec::new();
    let mut modified: Vec<PathBuf> = Vec::new();
    let mut deleted: Vec<PathBuf> = Vec::new();
    for hunk in hunks {
        match hunk {
            Hunk::AddFile { path, contents } => {
                if let Some(parent) = path.parent() {
                    if !parent.as_os_str().is_empty() {
                        std::fs::create_dir_all(parent).with_context(|| {
                            format!("Failed to create parent directories for {}", path.display())
                        })?;
                    }
                }
                std::fs::write(path, contents)
                    .with_context(|| format!("Failed to write file {}", path.display()))?;
                added.push(path.clone());
            }
            Hunk::DeleteFile { path } => {
                std::fs::remove_file(path)
                    .with_context(|| format!("Failed to delete file {}", path.display()))?;
                deleted.push(path.clone());
            }
            Hunk::UpdateFile {
                path,
                move_path,
                chunks,
            } => {
                let AppliedPatch { new_contents, .. } =
                    derive_new_contents_from_chunks(path, chunks)?;
                if let Some(dest) = move_path {
                    if let Some(parent) = dest.parent() {
                        if !parent.as_os_str().is_empty() {
                            std::fs::create_dir_all(parent).with_context(|| {
                                format!(
                                    "Failed to create parent directories for {}",
                                    dest.display()
                                )
                            })?;
                        }
                    }
                    std::fs::write(dest, new_contents)
                        .with_context(|| format!("Failed to write file {}", dest.display()))?;
                    std::fs::remove_file(path)
                        .with_context(|| format!("Failed to remove original {}", path.display()))?;
                    modified.push(dest.clone());
                } else {
                    std::fs::write(path, new_contents)
                        .with_context(|| format!("Failed to write file {}", path.display()))?;
                    modified.push(path.clone());
                }
            }
        }
    }
    Ok(AffectedPaths {
        added,
        modified,
        deleted,
    })
}

struct AppliedPatch {
    original_contents: String,
    new_contents: String,
}

/// Return *only* the new file contents (joined into a single `String`) after
/// applying the chunks to the file at `path`.
fn derive_new_contents_from_chunks(
    path: &Path,
    chunks: &[UpdateFileChunk],
) -> std::result::Result<AppliedPatch, ApplyPatchError> {
    let original_contents = match std::fs::read_to_string(path) {
        Ok(contents) => contents,
        Err(err) => {
            return Err(ApplyPatchError::IoError(IoError {
                context: format!("Failed to read file to update {}", path.display()),
                source: err,
            }));
        }
    };

    let mut original_lines: Vec<String> = original_contents
        .split('\n')
        .map(|s| s.to_string())
        .collect();

    // Drop the trailing empty element that results from the final newline so
    // that line counts match the behaviour of standard `diff`.
    if original_lines.last().is_some_and(|s| s.is_empty()) {
        original_lines.pop();
    }

    let replacements = compute_replacements(&original_lines, path, chunks)?;
    let new_lines = apply_replacements(original_lines, &replacements);
    let mut new_lines = new_lines;
    if !new_lines.last().is_some_and(|s| s.is_empty()) {
        new_lines.push(String::new());
    }
    let new_contents = new_lines.join("\n");
    Ok(AppliedPatch {
        original_contents,
        new_contents,
    })
}

/// Compute a list of replacements needed to transform `original_lines` into the
/// new lines, given the patch `chunks`. Each replacement is returned as
/// `(start_index, old_len, new_lines)`.
fn compute_replacements(
    original_lines: &[String],
    path: &Path,
    chunks: &[UpdateFileChunk],
) -> std::result::Result<Vec<(usize, usize, Vec<String>)>, ApplyPatchError> {
    let mut replacements: Vec<(usize, usize, Vec<String>)> = Vec::new();
    let mut line_index: usize = 0;

    for chunk in chunks {
        // If a chunk has a `change_context`, we use seek_sequence to find it, then
        // adjust our `line_index` to continue from there.
        if let Some(ctx_line) = &chunk.change_context {
            if let Some(idx) =
                seek_sequence::seek_sequence(original_lines, &[ctx_line.clone()], line_index, false)
            {
                line_index = idx + 1;
            } else {
                return Err(ApplyPatchError::ComputeReplacements(format!(
                    "Failed to find context '{}' in {}",
                    ctx_line,
                    path.display()
                )));
            }
        }

        if chunk.old_lines.is_empty() {
            // Pure addition (no old lines). We'll add them at the end or just
            // before the final empty line if one exists.
            let insertion_idx = if original_lines.last().is_some_and(|s| s.is_empty()) {
                original_lines.len() - 1
            } else {
                original_lines.len()
            };
            replacements.push((insertion_idx, 0, chunk.new_lines.clone()));
            continue;
        }

        // Otherwise, try to match the existing lines in the file with the old lines
        // from the chunk. If found, schedule that region for replacement.
        // Attempt to locate the `old_lines` verbatim within the file.  In many
        // real‑world diffs the last element of `old_lines` is an *empty* string
        // representing the terminating newline of the region being replaced.
        // This sentinel is not present in `original_lines` because we strip the
        // trailing empty slice emitted by `split('\n')`.  If a direct search
        // fails and the pattern ends with an empty string, retry without that
        // final element so that modifications touching the end‑of‑file can be
        // located reliably.

        let mut pattern: &[String] = &chunk.old_lines;
        let mut found =
            seek_sequence::seek_sequence(original_lines, pattern, line_index, chunk.is_end_of_file);

        let mut new_slice: &[String] = &chunk.new_lines;

        if found.is_none() && pattern.last().is_some_and(|s| s.is_empty()) {
            // Retry without the trailing empty line which represents the final
            // newline in the file.
            pattern = &pattern[..pattern.len() - 1];
            if new_slice.last().is_some_and(|s| s.is_empty()) {
                new_slice = &new_slice[..new_slice.len() - 1];
            }

            found = seek_sequence::seek_sequence(
                original_lines,
                pattern,
                line_index,
                chunk.is_end_of_file,
            );
        }

        if let Some(start_idx) = found {
            replacements.push((start_idx, pattern.len(), new_slice.to_vec()));
            line_index = start_idx + pattern.len();
        } else {
            return Err(ApplyPatchError::ComputeReplacements(format!(
                "Failed to find expected lines {:?} in {}",
                chunk.old_lines,
                path.display()
            )));
        }
    }

    Ok(replacements)
}

/// Apply the `(start_index, old_len, new_lines)` replacements to `original_lines`,
/// returning the modified file contents as a vector of lines.
fn apply_replacements(
    mut lines: Vec<String>,
    replacements: &[(usize, usize, Vec<String>)],
) -> Vec<String> {
    // We must apply replacements in descending order so that earlier replacements
    // don't shift the positions of later ones.
    for (start_idx, old_len, new_segment) in replacements.iter().rev() {
        let start_idx = *start_idx;
        let old_len = *old_len;

        // Remove old lines.
        for _ in 0..old_len {
            if start_idx < lines.len() {
                lines.remove(start_idx);
            }
        }

        // Insert new lines.
        for (offset, new_line) in new_segment.iter().enumerate() {
            lines.insert(start_idx + offset, new_line.clone());
        }
    }

    lines
}

/// Intended result of a file update for apply_patch.
#[derive(Debug, Eq, PartialEq)]
pub struct ApplyPatchFileUpdate {
    unified_diff: String,
    content: String,
}

pub fn unified_diff_from_chunks(
    path: &Path,
    chunks: &[UpdateFileChunk],
) -> std::result::Result<ApplyPatchFileUpdate, ApplyPatchError> {
    unified_diff_from_chunks_with_context(path, chunks, 1)
}

pub fn unified_diff_from_chunks_with_context(
    path: &Path,
    chunks: &[UpdateFileChunk],
    context: usize,
) -> std::result::Result<ApplyPatchFileUpdate, ApplyPatchError> {
    let AppliedPatch {
        original_contents,
        new_contents,
    } = derive_new_contents_from_chunks(path, chunks)?;
    let text_diff = TextDiff::from_lines(&original_contents, &new_contents);
    let unified_diff = text_diff.unified_diff().context_radius(context).to_string();
    Ok(ApplyPatchFileUpdate {
        unified_diff,
        content: new_contents,
    })
}

/// Print the summary of changes in git-style format.
/// Write a summary of changes to the given writer.
pub fn print_summary(
    affected: &AffectedPaths,
    out: &mut impl std::io::Write,
) -> std::io::Result<()> {
    writeln!(out, "Success. Updated the following files:")?;
    for path in &affected.added {
        writeln!(out, "A {}", path.display())?;
    }
    for path in &affected.modified {
        writeln!(out, "M {}", path.display())?;
    }
    for path in &affected.deleted {
        writeln!(out, "D {}", path.display())?;
    }
    Ok(())
}

/// Result of applying a patch to in-memory files
#[derive(Debug, PartialEq)]
pub struct InMemoryPatchResult {
    /// Files that were added or modified, mapping path to new content
    pub files: HashMap<PathBuf, String>,
    /// Files that were deleted
    pub deleted: Vec<PathBuf>,
    /// Summary of what was affected
    pub affected: AffectedPaths,
}

/// Applies a patch to in-memory files instead of the filesystem
///
/// # Arguments
/// * `patch` - The patch string to apply
/// * `files` - Map of file paths to their current contents
/// * `stdout` - Writer for success messages
/// * `stderr` - Writer for error messages
///
/// # Returns
/// The result containing modified file contents and summary of changes
pub fn apply_patch_in_memory(
    patch: &str,
    files: &HashMap<PathBuf, String>,
    stdout: &mut impl std::io::Write,
    stderr: &mut impl std::io::Write,
) -> Result<InMemoryPatchResult, ApplyPatchError> {
    let hunks = match parse_patch(patch) {
        Ok(hunks) => hunks,
        Err(e) => {
            match &e {
                InvalidPatchError(message) => {
                    writeln!(stderr, "Invalid patch: {message}").map_err(ApplyPatchError::from)?;
                }
                InvalidHunkError {
                    message,
                    line_number,
                } => {
                    writeln!(
                        stderr,
                        "Invalid patch hunk on line {line_number}: {message}"
                    )
                    .map_err(ApplyPatchError::from)?;
                }
            }
            return Err(ApplyPatchError::ParseError(e));
        }
    };

    let result = apply_hunks_in_memory(&hunks, files)?;
    print_summary(&result.affected, stdout).map_err(ApplyPatchError::from)?;
    Ok(result)
}

/// Applies hunks to in-memory files instead of the filesystem
pub fn apply_hunks_in_memory(
    hunks: &[Hunk],
    files: &HashMap<PathBuf, String>,
) -> Result<InMemoryPatchResult, ApplyPatchError> {
    if hunks.is_empty() {
        return Err(ApplyPatchError::ComputeReplacements(
            "No files were modified.".to_string(),
        ));
    }

    let mut result_files = HashMap::new();
    let mut added = Vec::new();
    let mut modified = Vec::new();
    let mut deleted = Vec::new();

    for hunk in hunks {
        match hunk {
            Hunk::AddFile { path, contents } => {
                result_files.insert(path.clone(), contents.clone());
                added.push(path.clone());
            }
            Hunk::DeleteFile { path } => {
                // Verify the file exists in the input
                if !files.contains_key(path) {
                    return Err(ApplyPatchError::ComputeReplacements(format!(
                        "Cannot delete file that doesn't exist: {}",
                        path.display()
                    )));
                }
                deleted.push(path.clone());
            }
            Hunk::UpdateFile {
                path,
                move_path,
                chunks,
            } => {
                let current_content = files.get(path).ok_or_else(|| {
                    ApplyPatchError::ComputeReplacements(format!(
                        "Cannot update file that doesn't exist: {}",
                        path.display()
                    ))
                })?;

                let AppliedPatch { new_contents, .. } =
                    derive_new_contents_from_content(current_content, path, chunks)?;

                if let Some(dest) = move_path {
                    result_files.insert(dest.clone(), new_contents);
                    modified.push(dest.clone());
                } else {
                    result_files.insert(path.clone(), new_contents);
                    modified.push(path.clone());
                }
            }
        }
    }

    Ok(InMemoryPatchResult {
        files: result_files,
        deleted: deleted.clone(),
        affected: AffectedPaths {
            added,
            modified,
            deleted,
        },
    })
}

/// Return the new file contents after applying chunks to the provided content
fn derive_new_contents_from_content(
    original_contents: &str,
    path: &Path,
    chunks: &[UpdateFileChunk],
) -> std::result::Result<AppliedPatch, ApplyPatchError> {
    let mut original_lines: Vec<String> = original_contents
        .split('\n')
        .map(|s| s.to_string())
        .collect();

    // Drop the trailing empty element that results from the final newline so
    // that line counts match the behaviour of standard `diff`.
    if original_lines.last().is_some_and(|s| s.is_empty()) {
        original_lines.pop();
    }

    let replacements = compute_replacements(&original_lines, path, chunks)?;
    let new_lines = apply_replacements(original_lines, &replacements);
    let mut new_lines = new_lines;
    if !new_lines.last().is_some_and(|s| s.is_empty()) {
        new_lines.push(String::new());
    }
    let new_contents = new_lines.join("\n");
    Ok(AppliedPatch {
        original_contents: original_contents.to_string(),
        new_contents,
    })
}

#[cfg(test)]
mod tests {
    #![allow(clippy::unwrap_used)]

    use super::*;
    use pretty_assertions::assert_eq;
    use std::fs;
    use tempfile::tempdir;

    /// Helper to construct a patch with the given body.
    fn wrap_patch(body: &str) -> String {
        format!("*** Begin Patch\n{}\n*** End Patch", body)
    }

    fn strs_to_strings(strs: &[&str]) -> Vec<String> {
        strs.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn test_literal() {
        let args = strs_to_strings(&[
            "apply_patch",
            r#"*** Begin Patch
*** Add File: foo
+hi
*** End Patch
"#,
        ]);

        match maybe_parse_apply_patch(&args) {
            MaybeApplyPatch::Body(hunks) => {
                assert_eq!(
                    hunks,
                    vec![Hunk::AddFile {
                        path: PathBuf::from("foo"),
                        contents: "hi\n".to_string()
                    }]
                );
            }
            result => panic!("expected MaybeApplyPatch::Body got {:?}", result),
        }
    }

    #[test]
    fn test_heredoc() {
        let args = strs_to_strings(&[
            "bash",
            "-lc",
            r#"apply_patch <<'PATCH'
*** Begin Patch
*** Add File: foo
+hi
*** End Patch
PATCH"#,
        ]);

        match maybe_parse_apply_patch(&args) {
            MaybeApplyPatch::Body(hunks) => {
                assert_eq!(
                    hunks,
                    vec![Hunk::AddFile {
                        path: PathBuf::from("foo"),
                        contents: "hi\n".to_string()
                    }]
                );
            }
            result => panic!("expected MaybeApplyPatch::Body got {:?}", result),
        }
    }

    #[test]
    fn test_add_file_hunk_creates_file_with_contents() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("add.txt");
        let patch = wrap_patch(&format!(
            r#"*** Add File: {}
+ab
+cd"#,
            path.display()
        ));
        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        apply_patch(&patch, &mut stdout, &mut stderr).unwrap();
        // Verify expected stdout and stderr outputs.
        let stdout_str = String::from_utf8(stdout).unwrap();
        let stderr_str = String::from_utf8(stderr).unwrap();
        let expected_out = format!(
            "Success. Updated the following files:\nA {}\n",
            path.display()
        );
        assert_eq!(stdout_str, expected_out);
        assert_eq!(stderr_str, "");
        let contents = fs::read_to_string(path).unwrap();
        assert_eq!(contents, "ab\ncd\n");
    }

    #[test]
    fn test_delete_file_hunk_removes_file() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("del.txt");
        fs::write(&path, "x").unwrap();
        let patch = wrap_patch(&format!("*** Delete File: {}", path.display()));
        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        apply_patch(&patch, &mut stdout, &mut stderr).unwrap();
        let stdout_str = String::from_utf8(stdout).unwrap();
        let stderr_str = String::from_utf8(stderr).unwrap();
        let expected_out = format!(
            "Success. Updated the following files:\nD {}\n",
            path.display()
        );
        assert_eq!(stdout_str, expected_out);
        assert_eq!(stderr_str, "");
        assert!(!path.exists());
    }

    #[test]
    fn test_update_file_hunk_modifies_content() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("update.txt");
        fs::write(&path, "foo\nbar\n").unwrap();
        let patch = wrap_patch(&format!(
            r#"*** Update File: {}
@@
 foo
-bar
+baz"#,
            path.display()
        ));
        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        apply_patch(&patch, &mut stdout, &mut stderr).unwrap();
        // Validate modified file contents and expected stdout/stderr.
        let stdout_str = String::from_utf8(stdout).unwrap();
        let stderr_str = String::from_utf8(stderr).unwrap();
        let expected_out = format!(
            "Success. Updated the following files:\nM {}\n",
            path.display()
        );
        assert_eq!(stdout_str, expected_out);
        assert_eq!(stderr_str, "");
        let contents = fs::read_to_string(&path).unwrap();
        assert_eq!(contents, "foo\nbaz\n");
    }

    #[test]
    fn test_update_file_hunk_can_move_file() {
        let dir = tempdir().unwrap();
        let src = dir.path().join("src.txt");
        let dest = dir.path().join("dst.txt");
        fs::write(&src, "line\n").unwrap();
        let patch = wrap_patch(&format!(
            r#"*** Update File: {}
*** Move to: {}
@@
-line
+line2"#,
            src.display(),
            dest.display()
        ));
        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        apply_patch(&patch, &mut stdout, &mut stderr).unwrap();
        // Validate move semantics and expected stdout/stderr.
        let stdout_str = String::from_utf8(stdout).unwrap();
        let stderr_str = String::from_utf8(stderr).unwrap();
        let expected_out = format!(
            "Success. Updated the following files:\nM {}\n",
            dest.display()
        );
        assert_eq!(stdout_str, expected_out);
        assert_eq!(stderr_str, "");
        assert!(!src.exists());
        let contents = fs::read_to_string(&dest).unwrap();
        assert_eq!(contents, "line2\n");
    }

    /// Verify that a single `Update File` hunk with multiple change chunks can update different
    /// parts of a file and that the file is listed only once in the summary.
    #[test]
    fn test_multiple_update_chunks_apply_to_single_file() {
        // Start with a file containing four lines.
        let dir = tempdir().unwrap();
        let path = dir.path().join("multi.txt");
        fs::write(&path, "foo\nbar\nbaz\nqux\n").unwrap();
        // Construct an update patch with two separate change chunks.
        // The first chunk uses the line `foo` as context and transforms `bar` into `BAR`.
        // The second chunk uses `baz` as context and transforms `qux` into `QUX`.
        let patch = wrap_patch(&format!(
            r#"*** Update File: {}
@@
 foo
-bar
+BAR
@@
 baz
-qux
+QUX"#,
            path.display()
        ));
        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        apply_patch(&patch, &mut stdout, &mut stderr).unwrap();
        let stdout_str = String::from_utf8(stdout).unwrap();
        let stderr_str = String::from_utf8(stderr).unwrap();
        let expected_out = format!(
            "Success. Updated the following files:\nM {}\n",
            path.display()
        );
        assert_eq!(stdout_str, expected_out);
        assert_eq!(stderr_str, "");
        let contents = fs::read_to_string(&path).unwrap();
        assert_eq!(contents, "foo\nBAR\nbaz\nQUX\n");
    }

    /// A more involved `Update File` hunk that exercises additions, deletions and
    /// replacements in separate chunks that appear in non‑adjacent parts of the
    /// file.  Verifies that all edits are applied and that the summary lists the
    /// file only once.
    #[test]
    fn test_update_file_hunk_interleaved_changes() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("interleaved.txt");

        // Original file: six numbered lines.
        fs::write(&path, "a\nb\nc\nd\ne\nf\n").unwrap();

        // Patch performs:
        //  • Replace `b` → `B`
        //  • Replace `e` → `E` (using surrounding context)
        //  • Append new line `g` at the end‑of‑file
        let patch = wrap_patch(&format!(
            r#"*** Update File: {}
@@
 a
-b
+B
@@
 c
 d
-e
+E
@@
 f
+g
*** End of File"#,
            path.display()
        ));

        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        apply_patch(&patch, &mut stdout, &mut stderr).unwrap();

        let stdout_str = String::from_utf8(stdout).unwrap();
        let stderr_str = String::from_utf8(stderr).unwrap();

        let expected_out = format!(
            "Success. Updated the following files:\nM {}\n",
            path.display()
        );
        assert_eq!(stdout_str, expected_out);
        assert_eq!(stderr_str, "");

        let contents = fs::read_to_string(&path).unwrap();
        assert_eq!(contents, "a\nB\nc\nd\nE\nf\ng\n");
    }

    /// Ensure that patches authored with ASCII characters can update lines that
    /// contain typographic Unicode punctuation (e.g. EN DASH, NON-BREAKING
    /// HYPHEN). Historically `git apply` succeeds in such scenarios but our
    /// internal matcher failed requiring an exact byte-for-byte match.  The
    /// fuzzy-matching pass that normalises common punctuation should now bridge
    /// the gap.
    #[test]
    fn test_update_line_with_unicode_dash() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("unicode.py");

        // Original line contains EN DASH (\u{2013}) and NON-BREAKING HYPHEN (\u{2011}).
        let original = "import asyncio  # local import \u{2013} avoids top\u{2011}level dep\n";
        std::fs::write(&path, original).unwrap();

        // Patch uses plain ASCII dash / hyphen.
        let patch = wrap_patch(&format!(
            r#"*** Update File: {}
@@
-import asyncio  # local import - avoids top-level dep
+import asyncio  # HELLO"#,
            path.display()
        ));

        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        apply_patch(&patch, &mut stdout, &mut stderr).unwrap();

        // File should now contain the replaced comment.
        let expected = "import asyncio  # HELLO\n";
        let contents = std::fs::read_to_string(&path).unwrap();
        assert_eq!(contents, expected);

        // Ensure success summary lists the file as modified.
        let stdout_str = String::from_utf8(stdout).unwrap();
        let expected_out = format!(
            "Success. Updated the following files:\nM {}\n",
            path.display()
        );
        assert_eq!(stdout_str, expected_out);

        // No stderr expected.
        assert_eq!(String::from_utf8(stderr).unwrap(), "");
    }

    #[test]
    fn test_unified_diff() {
        // Start with a file containing four lines.
        let dir = tempdir().unwrap();
        let path = dir.path().join("multi.txt");
        fs::write(&path, "foo\nbar\nbaz\nqux\n").unwrap();
        let patch = wrap_patch(&format!(
            r#"*** Update File: {}
@@
 foo
-bar
+BAR
@@
 baz
-qux
+QUX"#,
            path.display()
        ));
        let patch = parse_patch(&patch).unwrap();

        let update_file_chunks = match patch.as_slice() {
            [Hunk::UpdateFile { chunks, .. }] => chunks,
            _ => panic!("Expected a single UpdateFile hunk"),
        };
        let diff = unified_diff_from_chunks(&path, update_file_chunks).unwrap();
        let expected_diff = r#"@@ -1,4 +1,4 @@
 foo
-bar
+BAR
 baz
-qux
+QUX
"#;
        let expected = ApplyPatchFileUpdate {
            unified_diff: expected_diff.to_string(),
            content: "foo\nBAR\nbaz\nQUX\n".to_string(),
        };
        assert_eq!(expected, diff);
    }

    #[test]
    fn test_unified_diff_first_line_replacement() {
        // Replace the very first line of the file.
        let dir = tempdir().unwrap();
        let path = dir.path().join("first.txt");
        fs::write(&path, "foo\nbar\nbaz\n").unwrap();

        let patch = wrap_patch(&format!(
            r#"*** Update File: {}
@@
-foo
+FOO
 bar
"#,
            path.display()
        ));

        let patch = parse_patch(&patch).unwrap();
        let chunks = match patch.as_slice() {
            [Hunk::UpdateFile { chunks, .. }] => chunks,
            _ => panic!("Expected a single UpdateFile hunk"),
        };

        let diff = unified_diff_from_chunks(&path, chunks).unwrap();
        let expected_diff = r#"@@ -1,2 +1,2 @@
-foo
+FOO
 bar
"#;
        let expected = ApplyPatchFileUpdate {
            unified_diff: expected_diff.to_string(),
            content: "FOO\nbar\nbaz\n".to_string(),
        };
        assert_eq!(expected, diff);
    }

    #[test]
    fn test_unified_diff_last_line_replacement() {
        // Replace the very last line of the file.
        let dir = tempdir().unwrap();
        let path = dir.path().join("last.txt");
        fs::write(&path, "foo\nbar\nbaz\n").unwrap();

        let patch = wrap_patch(&format!(
            r#"*** Update File: {}
@@
 foo
 bar
-baz
+BAZ
"#,
            path.display()
        ));

        let patch = parse_patch(&patch).unwrap();
        let chunks = match patch.as_slice() {
            [Hunk::UpdateFile { chunks, .. }] => chunks,
            _ => panic!("Expected a single UpdateFile hunk"),
        };

        let diff = unified_diff_from_chunks(&path, chunks).unwrap();
        let expected_diff = r#"@@ -2,2 +2,2 @@
 bar
-baz
+BAZ
"#;
        let expected = ApplyPatchFileUpdate {
            unified_diff: expected_diff.to_string(),
            content: "foo\nbar\nBAZ\n".to_string(),
        };
        assert_eq!(expected, diff);
    }

    #[test]
    fn test_unified_diff_insert_at_eof() {
        // Insert a new line at end‑of‑file.
        let dir = tempdir().unwrap();
        let path = dir.path().join("insert.txt");
        fs::write(&path, "foo\nbar\nbaz\n").unwrap();

        let patch = wrap_patch(&format!(
            r#"*** Update File: {}
@@
+quux
*** End of File
"#,
            path.display()
        ));

        let patch = parse_patch(&patch).unwrap();
        let chunks = match patch.as_slice() {
            [Hunk::UpdateFile { chunks, .. }] => chunks,
            _ => panic!("Expected a single UpdateFile hunk"),
        };

        let diff = unified_diff_from_chunks(&path, chunks).unwrap();
        let expected_diff = r#"@@ -3 +3,2 @@
 baz
+quux
"#;
        let expected = ApplyPatchFileUpdate {
            unified_diff: expected_diff.to_string(),
            content: "foo\nbar\nbaz\nquux\n".to_string(),
        };
        assert_eq!(expected, diff);
    }

    #[test]
    fn test_unified_diff_interleaved_changes() {
        // Original file with six lines.
        let dir = tempdir().unwrap();
        let path = dir.path().join("interleaved.txt");
        fs::write(&path, "a\nb\nc\nd\ne\nf\n").unwrap();

        // Patch replaces two separate lines and appends a new one at EOF using
        // three distinct chunks.
        let patch_body = format!(
            r#"*** Update File: {}
@@
 a
-b
+B
@@
 d
-e
+E
@@
 f
+g
*** End of File"#,
            path.display()
        );
        let patch = wrap_patch(&patch_body);

        // Extract chunks then build the unified diff.
        let parsed = parse_patch(&patch).unwrap();
        let chunks = match parsed.as_slice() {
            [Hunk::UpdateFile { chunks, .. }] => chunks,
            _ => panic!("Expected a single UpdateFile hunk"),
        };

        let diff = unified_diff_from_chunks(&path, chunks).unwrap();

        let expected_diff = r#"@@ -1,6 +1,7 @@
 a
-b
+B
 c
 d
-e
+E
 f
+g
"#;

        let expected = ApplyPatchFileUpdate {
            unified_diff: expected_diff.to_string(),
            content: "a\nB\nc\nd\nE\nf\ng\n".to_string(),
        };

        assert_eq!(expected, diff);

        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        apply_patch(&patch, &mut stdout, &mut stderr).unwrap();
        let contents = fs::read_to_string(path).unwrap();
        assert_eq!(
            contents,
            r#"a
B
c
d
E
f
g
"#
        );
    }

    #[test]
    fn test_apply_patch_should_resolve_absolute_paths_in_cwd() {
        let session_dir = tempdir().unwrap();
        let relative_path = "source.txt";

        // Note that we need this file to exist for the patch to be "verified"
        // and parsed correctly.
        let session_file_path = session_dir.path().join(relative_path);
        fs::write(&session_file_path, "session directory content\n").unwrap();

        let argv = vec![
            "apply_patch".to_string(),
            r#"*** Begin Patch
*** Update File: source.txt
@@
-session directory content
+updated session directory content
*** End Patch"#
                .to_string(),
        ];

        let result = maybe_parse_apply_patch_verified(&argv, session_dir.path());

        // Verify the patch contents - as otherwise we may have pulled contents
        // from the wrong file (as we're using relative paths)
        assert_eq!(
            result,
            MaybeApplyPatchVerified::Body(ApplyPatchAction {
                changes: HashMap::from([(
                    session_dir.path().join(relative_path),
                    ApplyPatchFileChange::Update {
                        unified_diff: r#"@@ -1 +1 @@
-session directory content
+updated session directory content
"#
                        .to_string(),
                        move_path: None,
                        new_content: "updated session directory content\n".to_string(),
                    },
                )]),
            })
        );
    }

    #[test]
    fn test_apply_patch_in_memory_add_file() {
        let files = HashMap::new();
        let patch = wrap_patch(
            r#"*** Add File: new.txt
+hello
+world"#,
        );

        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        let result = apply_patch_in_memory(&patch, &files, &mut stdout, &mut stderr).unwrap();

        assert!(result.files.contains_key(&PathBuf::from("new.txt")));
        assert_eq!(result.files[&PathBuf::from("new.txt")], "hello\nworld\n");
        assert_eq!(result.affected.added, vec![PathBuf::from("new.txt")]);
        assert!(result.affected.modified.is_empty());
        assert!(result.affected.deleted.is_empty());
    }

    #[test]
    fn test_apply_patch_in_memory_update_file() {
        let mut files = HashMap::new();
        files.insert(PathBuf::from("test.txt"), "foo\nbar\nbaz\n".to_string());

        let patch = wrap_patch(
            r#"*** Update File: test.txt
@@
 foo
-bar
+BAR
 baz"#,
        );

        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        let result = apply_patch_in_memory(&patch, &files, &mut stdout, &mut stderr).unwrap();

        assert!(result.files.contains_key(&PathBuf::from("test.txt")));
        assert_eq!(result.files[&PathBuf::from("test.txt")], "foo\nBAR\nbaz\n");
        assert_eq!(result.affected.modified, vec![PathBuf::from("test.txt")]);
        assert!(result.affected.added.is_empty());
        assert!(result.affected.deleted.is_empty());
    }

    #[test]
    fn test_apply_patch_in_memory_delete_file() {
        let mut files = HashMap::new();
        files.insert(PathBuf::from("delete.txt"), "content\n".to_string());

        let patch = wrap_patch(r#"*** Delete File: delete.txt"#);

        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        let result = apply_patch_in_memory(&patch, &files, &mut stdout, &mut stderr).unwrap();

        assert!(!result.files.contains_key(&PathBuf::from("delete.txt")));
        assert_eq!(result.deleted, vec![PathBuf::from("delete.txt")]);
        assert_eq!(result.affected.deleted, vec![PathBuf::from("delete.txt")]);
        assert!(result.affected.added.is_empty());
        assert!(result.affected.modified.is_empty());
    }

    #[test]
    fn test_apply_patch_in_memory_move_file() {
        let mut files = HashMap::new();
        files.insert(PathBuf::from("old.txt"), "content\nline\n".to_string());

        let patch = wrap_patch(
            r#"*** Update File: old.txt
*** Move to: new.txt
@@
 content
-line
+modified line"#,
        );

        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        let result = apply_patch_in_memory(&patch, &files, &mut stdout, &mut stderr).unwrap();

        assert!(!result.files.contains_key(&PathBuf::from("old.txt")));
        assert!(result.files.contains_key(&PathBuf::from("new.txt")));
        assert_eq!(
            result.files[&PathBuf::from("new.txt")],
            "content\nmodified line\n"
        );
        assert_eq!(result.affected.modified, vec![PathBuf::from("new.txt")]);
        assert!(result.affected.added.is_empty());
        assert!(result.affected.deleted.is_empty());
    }

    #[test]
    fn test_apply_patch_in_memory_error_missing_file() {
        let files = HashMap::new();
        let patch = wrap_patch(
            r#"*** Update File: nonexistent.txt
@@
-some content
+new content"#,
        );

        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        let result = apply_patch_in_memory(&patch, &files, &mut stdout, &mut stderr);

        assert!(result.is_err());
        match result.unwrap_err() {
            ApplyPatchError::ComputeReplacements(msg) => {
                assert!(msg.contains("Cannot update file that doesn't exist"));
            }
            _ => panic!("Expected ComputeReplacements error"),
        }
    }

    #[test]
    fn test_apply_patch_in_memory_error_delete_missing_file() {
        let files = HashMap::new();
        let patch = wrap_patch(r#"*** Delete File: nonexistent.txt"#);

        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        let result = apply_patch_in_memory(&patch, &files, &mut stdout, &mut stderr);

        assert!(result.is_err());
        match result.unwrap_err() {
            ApplyPatchError::ComputeReplacements(msg) => {
                assert!(msg.contains("Cannot delete file that doesn't exist"));
            }
            _ => panic!("Expected ComputeReplacements error"),
        }
    }
}

// Python bindings using PyO3
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyModule;
#[cfg(feature = "python")]
use std::collections::HashMap as StdHashMap;

/// Python wrapper for ApplyPatchError
#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone)]
pub struct PyApplyPatchError {
    pub message: String,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyApplyPatchError {
    #[new]
    fn new(message: String) -> Self {
        Self { message }
    }

    fn __str__(&self) -> String {
        self.message.clone()
    }

    fn __repr__(&self) -> String {
        format!("PyApplyPatchError({})", self.message)
    }
}

#[cfg(feature = "python")]
impl From<ApplyPatchError> for PyApplyPatchError {
    fn from(err: ApplyPatchError) -> Self {
        Self {
            message: err.to_string(),
        }
    }
}

/// Python wrapper for InMemoryPatchResult
#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone)]
pub struct PyInMemoryPatchResult {
    #[pyo3(get)]
    pub files: StdHashMap<String, String>,
    #[pyo3(get)]
    pub deleted: Vec<String>,
    #[pyo3(get)]
    pub added: Vec<String>,
    #[pyo3(get)]
    pub modified: Vec<String>,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyInMemoryPatchResult {
    fn __repr__(&self) -> String {
        format!(
            "PyInMemoryPatchResult(files={}, deleted={}, added={}, modified={})",
            self.files.len(),
            self.deleted.len(),
            self.added.len(),
            self.modified.len()
        )
    }
}

#[cfg(feature = "python")]
impl From<InMemoryPatchResult> for PyInMemoryPatchResult {
    fn from(result: InMemoryPatchResult) -> Self {
        Self {
            files: result
                .files
                .into_iter()
                .map(|(k, v)| (k.to_string_lossy().to_string(), v))
                .collect(),
            deleted: result
                .deleted
                .into_iter()
                .map(|p| p.to_string_lossy().to_string())
                .collect(),
            added: result
                .affected
                .added
                .into_iter()
                .map(|p| p.to_string_lossy().to_string())
                .collect(),
            modified: result
                .affected
                .modified
                .into_iter()
                .map(|p| p.to_string_lossy().to_string())
                .collect(),
        }
    }
}

/// Apply a patch to files on disk
#[cfg(feature = "python")]
#[pyfunction]
fn py_apply_patch(patch: &str) -> PyResult<String> {
    let mut stdout = Vec::new();
    let mut stderr = Vec::new();

    match apply_patch(patch, &mut stdout, &mut stderr) {
        Ok(()) => {
            let output = String::from_utf8(stdout).unwrap_or_else(|_| "Success".to_string());
            Ok(output)
        }
        Err(e) => {
            let error_output = String::from_utf8(stderr).unwrap_or_else(|_| e.to_string());
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                error_output,
            ))
        }
    }
}

/// Apply a patch to in-memory files
#[cfg(feature = "python")]
#[pyfunction]
fn py_apply_patch_in_memory(
    patch: &str,
    files: StdHashMap<String, String>,
) -> PyResult<PyInMemoryPatchResult> {
    // Convert Python dict to PathBuf HashMap
    let files_map: StdHashMap<PathBuf, String> = files
        .into_iter()
        .map(|(k, v)| (PathBuf::from(k), v))
        .collect();

    let mut stdout = Vec::new();
    let mut stderr = Vec::new();

    match apply_patch_in_memory(&patch, &files_map, &mut stdout, &mut stderr) {
        Ok(result) => Ok(result.into()),
        Err(e) => {
            let error_output = String::from_utf8(stderr).unwrap_or_else(|_| e.to_string());
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                error_output,
            ))
        }
    }
}

/// Parse a patch string and return the hunks
#[cfg(feature = "python")]
#[pyfunction]
fn py_parse_patch(patch: &str) -> PyResult<Vec<String>> {
    match parse_patch(patch) {
        Ok(hunks) => {
            let hunk_descriptions: Vec<String> = hunks
                .into_iter()
                .map(|hunk| match hunk {
                    Hunk::AddFile { path, .. } => format!("AddFile: {}", path.display()),
                    Hunk::DeleteFile { path } => format!("DeleteFile: {}", path.display()),
                    Hunk::UpdateFile {
                        path,
                        move_path,
                        chunks,
                    } => {
                        let move_info = match move_path {
                            Some(dest) => format!(" -> {}", dest.display()),
                            None => String::new(),
                        };
                        format!(
                            "UpdateFile: {}{} ({} chunks)",
                            path.display(),
                            move_info,
                            chunks.len()
                        )
                    }
                })
                .collect();
            Ok(hunk_descriptions)
        }
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            e.to_string(),
        )),
    }
}

/// Get the tool instructions for apply_patch
#[cfg(feature = "python")]
#[pyfunction]
fn py_get_tool_instructions() -> &'static str {
    APPLY_PATCH_TOOL_INSTRUCTIONS
}

/// Get the API instructions for apply_patch (without shell/CLI specifics)
#[cfg(feature = "python")]
#[pyfunction]
fn py_get_api_instructions() -> &'static str {
    APPLY_PATCH_API_INSTRUCTIONS
}

/// Python module definition
#[cfg(feature = "python")]
#[pymodule]
fn codex_apply_patch(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_apply_patch, m)?)?;
    m.add_function(wrap_pyfunction!(py_apply_patch_in_memory, m)?)?;
    m.add_function(wrap_pyfunction!(py_parse_patch, m)?)?;
    m.add_function(wrap_pyfunction!(py_get_tool_instructions, m)?)?;
    m.add_function(wrap_pyfunction!(py_get_api_instructions, m)?)?;
    m.add_class::<PyApplyPatchError>()?;
    m.add_class::<PyInMemoryPatchResult>()?;
    m.add("__version__", "0.1.0")?;
    Ok(())
}
