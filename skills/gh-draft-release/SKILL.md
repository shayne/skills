---
name: gh-draft-release
description: "Use when a repository needs a user-facing GitHub release drafted for an explicit version or a patch, minor, or major bump request."
---

# Draft GitHub Release

## Overview

Use this skill to draft public GitHub release notes from the current repository. Work directly with `gh` and git commands in the repo instead of relying on bundled helper scripts.

## Required Inputs

Proceed only when the current user request clearly gives one of:

- an explicit target version such as `v0.1.2`
- a plain-English bump instruction such as `bump patch release`, `prepare the next minor release`, or similar

If the intended version is still ambiguous, stop and ask before drafting.

When you need the original request text, use the current user request verbatim as the source of truth.

## Workflow

1. Inspect the latest published GitHub release to learn the repo's public release-note tone and structure.
   Example commands:
   - `gh release list --exclude-drafts --exclude-pre-releases --limit 1 --json tagName,name`
   - `gh release view <latest-tag> --json tagName,name,body,isDraft,isPrerelease`
2. Detect the repository default branch.
   Example command:
   - `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`
3. Identify the latest stable release tag from git tags by selecting the highest stable semver tag matching `v?MAJOR.MINOR.PATCH`, ignoring prereleases and non-release tags.
   Example command:
   - `git tag --list | rg '^(v)?[0-9]+\\.[0-9]+\\.[0-9]+$' | sort -V | tail -1`
4. Determine the target version from either:
   - the explicit version in the user request
   - or the plain-English bump intent relative to the latest stable tag
5. When applying a bump:
   - preserve a leading `v` if the latest stable tag has one
   - `patch` increments `X.Y.Z` to `X.Y.(Z+1)`
   - `minor` increments `X.Y.Z` to `X.(Y+1).0`
   - `major` increments `X.Y.Z` to `(X+1).0.0`
6. If there is no stable semver tag:
   - and the user provided an explicit version, treat it as a first release
   - and the user only gave bump-style guidance, stop and ask for an explicit version
7. Compare the latest stable tag to the detected default branch using the two-dot range `<stable-tag>..<default-branch>`.
   Example commands:
   - `git log --oneline <stable-tag>..<default-branch>`
   - `git diff --name-only <stable-tag>..<default-branch>`
8. Read commits in that range and inspect changed code as needed to understand what users would notice.
9. Draft user-facing notes only.
10. If there is no published GitHub release yet, use a short generic public-note structure instead of trying to mirror a style that does not exist.
11. Write the drafted release body to `/tmp/gh-draft-release-notes.md`.
12. Resolve the release title:
   - default to the target version itself
   - if the latest published release clearly uses a different public title pattern, mirror that pattern for the new version
13. Check whether the target version already exists as a GitHub release.
   Example command:
   - `gh release view <target-version> --json tagName,name,isDraft,isPrerelease`
14. Handle existing release state:
   - if the release exists and is not a draft, stop and report that the version is already released
   - if the release exists and is a draft, ask whether to overwrite it before editing that draft
   - if the release does not exist, continue
15. Create the draft with:
   - `gh release create <target-version> --draft --target <default-branch> --title "<resolved-title>" --notes-file /tmp/gh-draft-release-notes.md`
16. If the user confirmed overwriting an existing draft, update it in place with:
   - `gh release edit <target-version> --title "<resolved-title>" --notes-file /tmp/gh-draft-release-notes.md`

## Writing Rules

- Write for public app users, not developers.
- Focus on features, fixes, polish, and behavior changes users can notice.
- Translate technical work into user outcomes.
- Reuse the repo's release-note structure when it helps readability.
- Exclude file names, class names, refactors, CI changes, dependency churn, and purely internal work unless users need that detail to understand the change.
- Do not invent claims that are not supported by the commits or code you inspected.
- If there are no notable user-facing changes, say so plainly in a short draft body.

## Guardrails

- Stop if version guidance is unclear.
- Stop if GitHub CLI authentication is required.
- Stop if the target version is already published.
- Ask before overwriting an existing draft release.
- Never publish the release.
- Never run separate `git tag`, `git push --tags`, or tag mutation commands just to prepare the draft.
