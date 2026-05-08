# Site Documentation

This folder is the single source of truth for why the site looks/behaves the way it does and how recurring tasks are run.

## Files

- `site-rules.md`: canonical working document for site rules, processes, corrections, and ongoing operating decisions.
- `design-decisions.md`: design and product decisions (what, why, impact).
- `automations.md`: automation inventory and runbooks.
- `drive-article-sync.md`: Google Drive publishing inbox format and setup.

## Update Rule

Whenever you change visual behavior, content structure, or automation flow:

1. Update `site-rules.md` first if the change affects rules, process, corrections, or operating behavior.
2. Add or update an entry in `design-decisions.md` for durable product/design decisions.
3. If a script/process is added or changed, update `automations.md`.
4. Keep entries short, dated, and reversible where possible.
