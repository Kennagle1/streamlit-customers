---
name: audit-app
description: Architectural audit of a Streamlit / Python app. Runs four parallel specialist agents covering cloud-native readiness, self-service UX, code quality / efficiency, and security. Returns a consolidated P1 / P2 / P3 findings list the user can action in priority order. Use when the user asks for a "full audit", "architectural review", "production-readiness check", or wants to identify bugs / issues before a handover.
---

# Audit App

Run a four-agent architectural audit of a Streamlit / Python app and consolidate findings into a priority-grouped action list.

## When to use

- User asks "audit the app", "full review", "architectural review", "is this production ready".
- User mentions handing the app over to non-technical owners and wants it self-sufficient.
- User mentions a bug or issue and wants to know "what else might be broken".
- Before pushing a large release or going live.

## How to run

1. **Confirm the scope.** The audit defaults to the directory the user names (e.g. "audit the L&D Hub"). Ask for the path if not obvious. Establish:
   - The app root (e.g. `C:\Users\DNeale\Analytics\Learning_Development\`).
   - Any directories or files to exclude (e.g. `docs/`, `data/drop/`).
   - Deployment context (Streamlit Cloud? private repo? who are the end users?).

2. **Spawn four agents in parallel**, each with a tightly-scoped brief. Do NOT run them sequentially -- each one runs independently against the same codebase and they do not need each other's output. Spawn all four in a single message with multiple Agent tool calls.

   Agents:

   **Agent 1 - Cloud-native audit (Explore)**
   Find anything that breaks when running without the developer's laptop:
   - Local-only paths (absolute Windows paths, sibling directories not in the git checkout).
   - Writes to `data/` that do NOT commit back via the project's GitHub sync helper -- ephemeral on Cloud.
   - Subprocess calls to `git` / local tools that may not exist on the hosting platform.
   - Error messages that tell the user to edit a CSV in GitHub or run a local script.
   - Streamlit secret reads without try/except -- would crash without a secrets.toml file.
   - Dead / orphaned files that would confuse a future maintainer.

   **Agent 2 - Self-service UX audit (Explore)**
   Find anything a non-technical user can't resolve without a developer:
   - Dead-end messages referencing actions they can't take (edit file, push commit, contact dev).
   - Missing in-app controls for features that are hardcoded in config.
   - Confusing labels / captions that reference technical concepts (git, branches, cache, mtime, glob, SHA, webhook) without plain-language explanation.
   - Destructive actions without confirmation.
   - Stale / misleading documentation strings referencing removed features.
   - First-time user journey: does the landing page explain what the app does, or lead with a dev-focused view?

   **Agent 3 - Code quality / efficiency audit (Explore)**
   Find engineering debt:
   - Dead code (unused imports, functions, constants, entire modules).
   - Duplicated logic across files (common offenders: GitHub commit helpers, date parsing, email normalisation, data loading patterns).
   - Inefficient patterns (O(n^2) merges, missing caches, re-reading large files, pandas `apply` where vectorised ops would do).
   - Broken or unreachable imports.
   - Cache key bugs (stale caches, missing `@st.cache_data`, TTL misalignment).
   - Silent swallowed exceptions (`except Exception: pass`) that hide real failures.
   - Style inconsistency across files.
   - Potential correctness bugs (date format mismatches, email matching without normalisation).
   - Call out the top 3 highest-impact items at the end.

   **Agent 4 - Security audit (Explore)**
   Find risks:
   - Secrets in code or committed CSVs.
   - Secrets in logs or error messages (especially anywhere headers could leak tokens).
   - Sensitive data (emails, HR info) rendered to UI via exception text.
   - Unsafe HTML rendering (`unsafe_allow_html=True` with uninterpolated user data).
   - Path traversal in upload / file-handling code.
   - Webhook / API signed URLs echoed into the UI.
   - Missing access control on sensitive actions.
   - File-size / abuse vectors (unbounded log growth, glob patterns deleting the wrong files).
   - Assign severity High / Medium / Low.

3. **Each agent's prompt MUST include:**
   - Absolute path to the app root.
   - An exhaustive list of what to look for (bulleted, from above).
   - Report format: bulleted findings grouped by category, each with file:line + one-sentence problem + one-sentence fix.
   - Word limit (400-500 words is plenty).
   - Explicit instruction NOT to fix anything, just report.
   - Explicit instruction NOT to touch files other agents may be editing (if you're also doing fixes in parallel).

4. **Consolidate** the four reports into a single priority-grouped list for the user:
   - **P1 -- Fix this week** (correctness / reliability blockers, cross-cutting silent failures, duplicated logic with drift risk).
   - **P2 -- Self-service readiness** (anything a non-dev user can't action, jargon in captions, missing in-app paths for admin work).
   - **P3 -- Security / robustness** (High- and Medium-severity security findings, HTML escape, RBAC).
   - **P4 -- Non-blocking** (style, minor dead code, cache TTL alignment).

5. **Present a table** per priority level: number, issue, file:line, impact.

6. **Recommend a sequencing** -- which pass to run first, estimated effort, whether items are safely parallelisable.

7. **Offer to execute the fixes** with the same parallel-agents pattern: one agent per concern area, non-overlapping file scopes, each reports back in under 350 words before committing. Only commit and push after all three come back clean and a smoke test passes.

## Rules

- Use `subagent_type: Explore` for audit agents (they only read files, don't mutate).
- If the user later asks to fix the findings, switch to `subagent_type: general-purpose` and give each fix-agent a non-overlapping file scope.
- Do NOT commit during the audit. Read-only.
- Keep agent prompts self-contained: they haven't seen the conversation.
- Preserve absolute paths when referencing files, so the user can click through.
- If the user has UK English conventions / no-em-dashes / no-emojis in CLAUDE.md, carry those through to every agent prompt so their reports match house style.

## Output

End-of-audit message to the user should include:

- **Summary**: one-line health call (e.g. "Broadly production-ready with 4 P1 items and 2 P3 security items worth addressing before handover").
- **Priority tables**: P1, P2, P3, P4 each as a compact table.
- **Recommended sequencing**: which order to tackle, which items can run in parallel.
- **Ask**: "Shall I execute the P1 + P2 + P3 fixes across parallel agents, same pattern as last time?"

## Reference runs

- 24 Apr 2026: L&D Hub (`C:\Users\DNeale\Analytics\Learning_Development\`). Four agents, ~5 minutes total. 15 findings across four categories. Subsequent fix pass: three parallel general-purpose agents, ~15 minutes, 12 files changed, production hardening complete.
