# bdh-cl: repository migration note (2026-09-13)

**Event:** the fork was transferred and renamed from `asb-42/bdh` to
**`Saga-AI-Labs/bdh-cl`** (operator completed; this note is written as live
provenance, not as a change to any measured result).

## Canonical references

- Repository URL: `https://github.com/Saga-AI-Labs/bdh-cl`
- SSH remote: `git@github.com:Saga-AI-Labs/bdh-cl.git`
- Org spelling: `Saga-AI-Labs` (with the trailing `s`; `Saga-AI-Lab` 404s).
- The old paths `asb-42/bdh` and the repo name `bdh` remain valid as
  historical references in dated documents; GitHub redirects the old URL.

## References updated in this migration

- `README.md`: fork-location line plus the canonical repository URL.
- `docs/papers/rev4-bdh-manuscript.tex`: the "Every number traces to a
  committed artifact" sentence now carries the canonical repository URL.

## References deliberately left unchanged

- Six dated documents cite `asb-42/bdh` in headers or prose
  (`docs/archive/pi-50-working/REVIEW.md`, the 2026-08-24 plan, the
  2026-09-05 battle plan, the 2026-08-18 and 2026-08-23 progress reports,
  the 2026-08-29 review). These cite what was true when they were written;
  retroactively rewriting them would falsify the historical record. New
  artifacts use the new org.
- The battle plan `docs/plans/2026-09-05_decay-aftermath-battle-plan.md`, §5,
  records the .200 host's git remote as of that date; it is a dated
  operational record, not a live configuration directive.

## Access status on this date

- **Read:** verified (`git ls-remote`, `git fetch`, `ssh -T`: "Hi
  Saga-AI-Labs/bdh-cl!").
- **Write:** currently blocked. `git push` fails with "Permission to
  Saga-AI-Labs/bdh-cl.git denied to deploy key" (exit 128). GitHub disabled
  the existing deploy keys under an org policy and locked the deploy-key
  settings page, recommending GitHub Apps instead. Until a write credential
  (GitHub App or operator-provisioned token) exists, local commits to this
  repository cannot be pushed; provisioning is operator work.

## Test protocol (this migration)

1. `git remote set-url origin git@github.com:Saga-AI-Labs/bdh-cl.git`
2. `ssh -T git@github.com` -> authentication OK
3. `git ls-remote origin HEAD` -> returns the expected HEAD
4. `git fetch origin` -> clean, no divergence
5. `git push --dry-run origin main` -> ERROR: denied to deploy key
6. Manuscript recompiled and Markdown regenerated after the provenance edit
   (documented in the commit that lands this note)

- Quinn (A0), 2026-09-13
