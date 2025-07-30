use std::io::{self, Read};
use std::process;

use codex_apply_patch::apply_patch;

fn main() {
    // Read the entire patch from stdin
    let mut patch = String::new();
    if let Err(err) = io::stdin().read_to_string(&mut patch) {
        eprintln!("Error reading patch from stdin: {}", err);
        process::exit(1);
    }

    let stdout = io::stdout();
    let mut stdout_lock = stdout.lock();
    let stderr = io::stderr();
    let mut stderr_lock = stderr.lock();

    // Apply the patch and print outputs
    if apply_patch(&patch, &mut stdout_lock, &mut stderr_lock).is_err() {
        // apply_patch already wrote error messages to stderr
        process::exit(2);
    }

    process::exit(0);
}
