---
name: install-system-package
description: Install missing or useful system packages declaratively on macOS hosts managed by nix-darwin. Use when a command needed for the current task is missing, when installing a CLI or GUI app would materially help complete work, or when the user explicitly asks to install software. Prefer nixpkgs packages first, then Homebrew brews, then Homebrew casks. Ask the user to confirm the package choice and whether the install should be host-specific or shared before editing config or running the rebuild.
---

# Install System Package

## Overview

Treat package installation as a declarative config change in `~/nixos-config`, not an imperative machine action. Read `references/workflow.md` at the start to get the repo-specific paths, edit targets, rebuild command, verification rules, and git behavior.

## Workflow

1. Confirm that a package is actually needed.
   - Trigger when a required command is missing, when a better tool would materially simplify the task, or when the user asks to install software.
   - Do not silently switch to a weaker fallback just because a package is missing.
2. Find install candidates in this order.
   - `nixpkgs` package
   - Homebrew brew
   - Homebrew cask
   - If none are viable, stop and explain that no declarative install candidate was found.
3. Present options and ask for approval.
   - Recommend the best option first and explain why.
   - Include viable alternatives when they exist.
   - Ask whether the install should be host-specific or shared across hosts.
   - Ask for confirmation before editing config.
4. Edit the declarative config.
   - Follow the file-selection rules in `references/workflow.md`.
   - Keep the diff narrow.
   - Preserve local formatting and list ordering.
5. Ask again before applying the change.
   - Confirm before running the rebuild command.
   - Use targeted config evaluation when it helps confirm the edit before rebuild.
6. Rebuild and verify.
   - Run the repo rebuild command from the config repo.
   - Verify the installed result directly, not just the rebuild.
   - If verification fails, do not commit or push.
7. Finalize.
   - Commit only the relevant config changes.
   - Push to `origin`.
   - Report what was installed and where it was declared.

## Candidate Selection Rules

- Prefer Nix whenever a maintained `nixpkgs` package satisfies the need.
- Prefer Homebrew `brew` over `cask` for CLI tools that exist in both.
- Use `cask` for GUI applications or app bundles.
- If the package name differs from the executable or app name, track both names before you present options.

## Required Confirmation Points

- Before editing config.
- When choosing host-specific versus shared scope.
- Before running the rebuild command.

## Verification Rules

- For CLI tools, verify with `command -v <command>` and a lightweight version or help check when sensible.
- For GUI apps, verify the app bundle exists at the expected macOS application path.
- If the rebuild succeeds but the tool or app is not usable, treat the installation as failed.

## Hard Rules

- Never use imperative `brew install`, `brew upgrade`, `nix profile install`, or similar one-off package installs.
- Never hide package choice or scope from the user.
- Never commit or push before rebuild and verification succeed.
- Never include unrelated working tree changes in the commit.
- If package lookup is ambiguous, show the ambiguity and ask the user.

## Examples

- A task needs `rg`, the command is missing, and `ripgrep` would unblock the work. Propose `pkgs.ripgrep` first, show any viable Homebrew fallback, ask about host-specific versus shared scope, then proceed declaratively if the user approves.
- The user asks to install a GUI app such as Google Chrome. Prefer a cask when there is no suitable Nix package, ask about scope, edit the declared Homebrew config, rebuild, verify the app bundle, then commit and push.
