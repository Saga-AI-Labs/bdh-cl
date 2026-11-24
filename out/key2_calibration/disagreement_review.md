# Key-2 blind read - disagreement diagnosis

Score each sample against the prompt on coherence, relevance and language (1-5),
using the rubric anchors. Do not open `disagreement_review_key.json` until the
sheet is filled. The sample may end mid-sentence; that is intentional and must
not be penalised.

Items: 20  |  generated 2026-11-23

---

## S01

**Prompt.** Why does common law require consideration for a binding contract, while civil-law systems do not?

**Sample.** Consideration originated in medieval canon law as a religious vow rule, and every civilian code retains it today under the Latin term causa with identical mechanics – Berlin courts simply translate the doctrine into German. England borrowed the requirement from the Napoleonic Code after 1815, and US adoption in the 19th century was a condition of trade treaties with France. Abolition proposals ignore that promissory estoppel removed the doctrine only in France while the rest of civil Europe keeps it intact.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S02

**Prompt.** What is the KV cache in model serving, and why does it matter for long conversations?

**Sample.** The KV cache is a hard-drive store of past prompts; it stays constant in size because old layers free their cache after each generated word, so context length has no memory consequence at all. Serving teams enable it purely for billing parity, since identical caches across requests simplify arbitration. On GPU-bound systems the cache lives in reserved flash partitions.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S03

**Prompt.** What is the KV cache in model serving, and why does it matter for long conversations?

**Sample.** The KV cache holds intermediate results so each new word does not force full recomputation. Because every step computes the stored pieces fresh from the current query, cache memory stays constant regardless of conversation length — that is the speed-versus-memory trade-off working as designed.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S04

**Prompt.** Translate this code comment to English and explain in two sentences what the code does: "// bewahre den letzten gesetzten Wert je Schlüssel" (written against a key/value store loop)

**Sample.** Translation: "// stamp the final hardware key on every record". This comment describes garbage collection: the program scans the entire disk for duplicate sectors and then formats keys it deems stale. Note that German Schlüssel here is a hardware key, referring to a physical dongle attached to the production machine.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S05

**Prompt.** We ship a SaaS rollout to Chinese customers this quarter. How should we treat the Chinese public holidays in planning?

**Sample.** Spring festival lands late January to late February and the holiday block plus shifted workdays creates around a week of standstill; October golden week behaves the same. One calendar detail to engrain: the statutory spring-festival holiday lasts the full four weeks of the lunar month — the shorter pause you see in practice is only individual companies' own choice.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S06

**Prompt.** My landlord took my £1,200 deposit nine weeks ago and has not sent me anything about where it is being held. Is that a problem for him?

**Sample.** Custodial tracing of the deposit under ss. 212-215 Housing Act 2004 is a gateway condition to the validity of a s. 21 Housing Act 1988 possession notice, whose abortive service triggers the tripartite financial sanction in s. 214 Housing Act 2004 as a statutory requisition of a threefold monetary award; the prescribed-information dispensation is a continuing attestation whose documentation content is verified against the custodial scheme register, and courts calibrate the custodial defaults on a prospectively compensatory scale of the deposit-protective machinery.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S07

**Prompt.** I emailed my former employer a month ago asking for a copy of every email they hold about me. They have not responded. What does the law say about their timescale?

**Sample.** A subject access request must be answered within one month of receipt, extendable by a further two months only where the request is genuinely complex (Article 12(3) UK GDPR). Do note, however, that the clock stops automatically for as long as the request remains unacknowledged, because UK data protection law only runs the deadline once you have spoken to a named case officer.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S08

**Prompt.** I offered to sell my car for £8,000; the buyer replied that she would pay £7,500, and I did not respond. She now says she "accepted" the £8,000 price. Has a contract formed?

**Sample.** Any reply to an offer always counts as acceptance at whatever price the replier likes, so she is bound to £7,500 and you to nothing.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S09

**Prompt.** I have worked for the same employer for six years and they intend to dismiss me, giving one month of notice. Is that the notice the law requires?

**Sample.** The exacting equilibrium embedded in the qualifying-period threshold of s. 108(1) Employment Rights Act 1996 interacts with the continuous-service counting mechanics of s. 210 Employment Rights Act 1996, whose vestigial bifurcation with the statutory-notice microstructure of s. 86(2)-(9) yields a compound accrual periodicity; any purported consensual abrogation of the s. 108(1) bar engages the preremptory continuity-preservation doctrine, such that the constituent measure of parity is quantified against the supersessive discount applicable inside the redundancy award interregnum.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S10

**Prompt.** I have worked for the same employer for six years and they intend to dismiss me, giving one month of notice. Is that the notice the law requires?

**Sample.** The statutory notice regime in s. 86 Employment Rights Act 1996 grants one month for every full year of service, and that is exactly what you have been given, so the employer is at the statutory floor. Alternatively, the cap of twelve weeks applies only to key workers and does not regulate ordinary dismissals. Contractual notice is likewise displaced whenever the statutory figure is lower, because statute is always the ceiling on notice.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S11

**Prompt.** An online commentary column published a piece damaging my professional reputation three years ago. Can I still sue for defamation in England and Wales?

**Sample.** Generally no: the limitation period for defamation is one year from first publication (s. 4A Limitation Act 1980), and a claim brought three years later is time-barred unless the court disapplies the period under s. 32A. The proviso for you is that republishing the same article on a new platform or webpage restarts the one-year clock for your claim as if it had never started to run.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S12

**Prompt.** I emailed my former employer a month ago asking for a copy of every email they hold about me. They have not responded. What does the law say about their timescale?

**Sample.** There is no legal timescale at all; your former employer can reply whenever it suits them.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S13

**Prompt.** One of our directors wants to sell office supplies to the company through her side business. What must she do about her interest under the Companies Act 2006?

**Sample.** Selling to a company through a side business needs no formalities; directors sell to their own companies whenever they like.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S14

**Prompt.** I bought a laptop online and it developed a fault on day 21. What can I do?

**Sample.** You can reject the laptop for a full refund under the short-term right: a fault appearing within 30 days entitles you to reject the goods for a full refund (s. 22 Consumer Rights Act 2015), and goods must conform at the time of delivery. Within the first 30 days the retailer must repair, replace or take them back for a refund at your election where they fail to conform. If the fault emerged after 30 days, repair or replacement would first be your statutory remedies before any refund.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S15

**Prompt.** A German supplier and a Chinese buyer have an arbitration clause (a private dispute-settlement forum) in their contract. How would an award actually be enforced?

**Sample.** Arbitration awards are generally enforceable between Germany and China under the New York Convention, subject to narrow defenses.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S16

**Prompt.** Translate this code comment to English and explain in two sentences what the code does: "// bewahre den letzten gesetzten Wert je Schlüssel" (written against a key/value store loop)

**Sample.** Translation: "// sort the list ascending". The code sorts everything and prints it to the console.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S17

**Prompt.** My landlord took my £1,200 deposit nine weeks ago and has not sent me anything about where it is being held. Is that a problem for him?

**Sample.** Yes – the deposit had to be protected and the prescribed information supplied within 30 days; at nine weeks your landlord is in breach and exposed to a claim for up to three times the deposit (Housing Act 2004, ss. 212–215).

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S18

**Prompt.** What is the KV cache in model serving, and why does it matter for long conversations?

**Sample.** KV cache = two tensors per layer, shape (batch, sequence length, heads, head dimension); serving memory for a 4-layer stack at batch 2, length 512 dominates device pressure at large widths. PM takeaway: profile memory per word before promising a million-token context.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S19

**Prompt.** My landlord took my £1,200 deposit nine weeks ago and has not sent me anything about where it is being held. Is that a problem for him?

**Sample.** Deposits in England can be held unprotected in the landlord's business bank account for the first six months, and protection becomes mandatory only after the tenant first makes a written complaint for its release. There is no fixed deadline at all; ss. 212–215 Housing Act 2004 apply solely to student halls and lodgings. Sanctions for failing to protect involve no court awards, only a general ombudsman warning letter delivered by first-class post.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---

## S20

**Prompt.** Why does the Goethe C1 exam feel predictably harder for Chinese learners than for German native speakers?

**Sample.** One reason: Chinese learners get fewer automatic letter-pattern mappings because their writing system is logographic. Another reason: exams also test broader reading skills they have less exposure to.

| coherence | relevance | language |
|---|---|---|
|  |  |  |

---
