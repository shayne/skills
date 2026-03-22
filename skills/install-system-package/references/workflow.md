# Workflow Reference

## Repo And Commands

- Config repo: `~/nixos-config`
- Run repo commands from the repo root.
- Apply changes with `mise run`.

## File Selection

- Shared Nix installs: `systems/base/darwin-configuration.nix`
  - Add packages to `environment.systemPackages`.
- Host-specific Nix installs: `systems/<hostname>/darwin-configuration.nix`
  - Add packages to `environment.systemPackages`.
- Host-specific Homebrew installs: `systems/<hostname>/darwin-configuration.nix`
  - Use `homebrew.brews` for CLI formulae.
  - Use `homebrew.casks` for GUI apps.
- Shared Homebrew requests in v1: edit each Darwin host file directly instead of introducing a new shared Homebrew abstraction unless the user explicitly asks for that refactor.

## Host Detection

- Determine the current host from the machine hostname and match it to `systems/<hostname>/`.
- Treat any `systems/<hostname>/darwin-configuration.nix` file as a Darwin host target.

## Candidate Lookup

- Check `nixpkgs` first.
- If there is no good Nix package, check Homebrew `brew`.
- Use Homebrew `cask` for macOS app bundles.
- Present the recommended option first and list viable alternatives.

## Confirmation And Pre-Apply Checks

- Ask whether the install should be host-specific or shared across hosts.
- Ask the user to confirm the chosen package before editing config.
- Ask again before running `mise run`.
- For small Homebrew changes, prefer targeted sanity checks before rebuild when useful:
  - `nix eval --json .#darwinConfigurations.<host>.config.homebrew.brews`
  - `nix eval --json .#darwinConfigurations.<host>.config.homebrew.casks`

## Verification

- CLI tools: verify with `command -v <command>` and, when helpful, `<command> --version` or `<command> --help`.
- GUI apps: verify the installed app bundle exists in `/Applications` or the expected app path.
- If the package name and the executable or app name differ, verify the actual command or app the user needs.
- If rebuild or verification fails, stop before commit and push.

## Git Behavior

- After successful verification, create a small scope-style commit from `~/nixos-config`.
- Commit only the relevant config files.
- Push to `origin`.

## Prohibited Actions

- Do not use imperative `brew install`.
- Do not use imperative `nix profile install`.
- Do not commit before rebuild and verification succeed.
