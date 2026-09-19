# External audits: provenance record

This directory holds **unmodified third‑party documents** — the review outputs that reached us
as uploads. They are stored verbatim and are never edited here. Provenance lives in this file
rather than inside the documents, so that what is on disk stays byte‑identical to what the
external reviewer produced.

Each audit has a counter‑review in [`../reviews/`](../reviews/), which is our own audit‑of‑the‑audit:
every claim checked against primary sources, and the auditor's own arithmetic recomputed rather
than accepted. The two documents are meant to be read as a pair — the audit, then the pass over it.

## Method note (applies to both)

Both audits came from a single source described below, and the same three‑step protocol decided
every claim in both:

1. **Citation vs. computation kept separate.** For each claim, first whether the paper actually
   says what the audit says it says (checked against the TeX verbatim, not filtered), then whether
   the audit's own arithmetic is right (recomputed, never taken on faith).
2. **Primary sources only.** No quoted number was ever checked against the manuscript under attack;
   measured values were rechecked against the artifacts under `docs/data/` and `docs/reports/` that
   produced them.
3. **The auditor's `verified` column checked too.** A confirmation of something false is the heavier
   kind of finding, so the "verified as correct" items were recomputed, not credited.

The recurring failure mode this protocol is built for: **correct arithmetic applied to the wrong
referent** — a real calculation performed against a quantity or sentence the document does not use.
It is what sank individual claims in both audits; see the two reviews for the instances.

## Documents in this directory

### 1. `2026-09-16_bdh-paper-audit_union-alpha.md`

- **Object audited:** the BDH parent paper — *The Dragon Hatchling: The Missing Link between the
  Transformer and Models of the Brain*, Kosowski et al., Pathway Palo Alto, arXiv:2509.26507.
  Not our manuscript; this audit is of a third party's paper.
- **Primary text it was checked against:** `/a0/usr/uploads/paper.tex`, MD5
  `53c0c31f6e3bc7cfe61a1bac1da9d039`, 2132 lines. Line references in the review point at this file,
  not at arXiv page numbers.
- **MD5 (this file):** `e91a4f9208fcb3b44d76461d36f4219b`, 4463 bytes, 30 lines.
- **Counter‑review:** [`../reviews/2026-09-19_bdh-paper-audit_union-alpha_review.md`](../reviews/2026-09-19_bdh-paper-audit_union-alpha_review.md)
- **Result, in one line:** a mixed pass — two defects in Pathway's text confirmed (the ReLU notation
  self‑contradiction; an `L1`/TVD factor‑of‑2), one marquee claim the audit called numerically falsified
  shown to be unsupported because the right quantity was computed against vectors the paper does not
  define. Blast radius on our own manuscript: **zero** — none of the contested constructs occurs in it.

### 2. `2026-09-17_bdh-cl_append-only-neural-memory-audit_union-alpha.md`

- **Object audited:** **our own manuscript** — *Append‑Only Neural Memory: Storage, Addressing, and
  Growth in a Depth‑Recurrent Language Model*, Revision 4.6, `../papers/rev4-bdh-manuscript.tex`,
  MD5 `dc2731b09bbb71c09b977c07a3e722db`, 1190 lines.
- **MD5 (this file):** `fb8ed65cbede7ca63ee9e26d6ad79c9b`, 15911 bytes, 65 lines.
- **Counter‑review:** [`../reviews/2026-09-19_bdh-cl-append-only-audit_union-alpha_review.md`](../reviews/2026-09-19_bdh-cl-append-only-audit_union-alpha_review.md)
- **Result, in one line:** seventeen claims — ten hold, four hold in part, two do not hold as stated,
  one holds in substance on a figure the audit itself mis‑printed. Blast radius: **not zero** — this
  is our paper heading to publication, and its two most consequential findings are ours to fix.

## Provenance of the reviewer, and why it is bracketed

Both audits carry the handle "Union Alpha" — a stealth OpenRouter listing marketed as
"frontier‑level intelligence", reported to be a router (reported as Pareto 26.9) that may route to
models including Fable and Astra. **The routing decision and the model that actually did the work are
both unknown.**

Neither identity is used in either review, in either direction: no judgement rests on the listing's
marketing, and no judgement rests on the reported router identity. Everything above is decided against
the primary files and the recomputation. The identity is recorded because it is part of what we know
about the provenance; it is bracketed because it is not evidence for or against any claim.

## Integrity

Each audit's MD5 above is reproduced from the upload it arrived as, and re‑verified byte‑for‑byte after
placement under `docs/audits/` (`md5sum -c`). A mismatch between a copy's MD5 and the value listed here
means the file was altered after it was placed — treat the copy as suspect and re‑pull from the upload.
