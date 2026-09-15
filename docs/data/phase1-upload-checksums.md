# Phase-1 upload checksums (RA2b) — pre-upload provenance

Generated 2026-09-15T17:30:29 by Quinn (A0 seat) from captured staging-marker digests and the remote tree API response, recorded before the `hf_phase1_upload/` staging folder was deleted.

## Why this file exists

The RA2b local staging and its `.metadata` markers were deleted after upload to free gx10 space. Without this join, the claim "the remote bytes equal the bytes that produced the published curves" is circular: rebuilding the digest list from HF's tree API compares HF-to-HF. The rows below preserve the **pre-upload sha256** (computed from the on-disk bytes before any transfer) side-by-side with the **remote LFS oid** HF reports, which is the non-circular link. Raised by pi-50 (HAK #301).

Remote source: `GET https://huggingface.co/api/datasets/Saga-AI-Labs/bdh-cl_phase-1/tree/main?recursive=true&full=true`.

Result: **40/40 files** match on size AND sha256; total 163,125,408,976 B. All identical — RA2b integrity confirmed.

| file | size (B) | pre-upload sha256 | remote LFS oid | match |
|---|---:|---|---|:--:|
| bdh_europarl_ladRA2b-bg_best.pt | 4,229,029,295 | `9e552dbb2c51277f41492d0f92b094ddfd139822e3d4b7cdb57c2b2fd0fc157a` | `9e552dbb2c51277f41492d0f92b094ddfd139822e3d4b7cdb57c2b2fd0fc157a` | ok |
| bdh_europarl_ladRA2b-bg_last.pt | 4,229,029,295 | `81b60f6a1d87ca75581a89598364e0abf0d3e02182ec577c1d7d51116067a9ca` | `81b60f6a1d87ca75581a89598364e0abf0d3e02182ec577c1d7d51116067a9ca` | ok |
| bdh_europarl_ladRA2b-cs_best.pt | 2,719,038,895 | `9c22d8e17169fe4440bbf090dbdd8762311f781afa81492256fd47a379fa4c6b` | `9c22d8e17169fe4440bbf090dbdd8762311f781afa81492256fd47a379fa4c6b` | ok |
| bdh_europarl_ladRA2b-cs_last.pt | 2,719,038,895 | `4da87fe90d1ecc33985201008875047fa17dc0d3943db83a130e999314610568` | `4da87fe90d1ecc33985201008875047fa17dc0d3943db83a130e999314610568` | ok |
| bdh_europarl_ladRA2b-da_best.pt | 3,021,036,975 | `ed204c6c209d8bc2739724a3744991cc54b0e9dabbfcedea738ff1b16475d7c0` | `ed204c6c209d8bc2739724a3744991cc54b0e9dabbfcedea738ff1b16475d7c0` | ok |
| bdh_europarl_ladRA2b-da_last.pt | 3,021,036,975 | `79f740e4430d23bcb096fe9deb8b15ab6d5645f287f95c00524a768e6fe8c5ac` | `79f740e4430d23bcb096fe9deb8b15ab6d5645f287f95c00524a768e6fe8c5ac` | ok |
| bdh_europarl_ladRA2b-de_best.pt | 2,417,040,815 | `a0542c258b6ba43abd1f1665c232ca1ea8a20eaffd99cda6195f95bb7eba3860` | `a0542c258b6ba43abd1f1665c232ca1ea8a20eaffd99cda6195f95bb7eba3860` | ok |
| bdh_europarl_ladRA2b-de_last.pt | 2,417,040,815 | `0990bf367f264fea9f29dae6a01714b5586eb99b7202736a4ec6f355651f751c` | `0990bf367f264fea9f29dae6a01714b5586eb99b7202736a4ec6f355651f751c` | ok |
| bdh_europarl_ladRA2b-el_best.pt | 5,135,023,579 | `a497536445bfa82b2cc0b1dea6615aaf3cb6b2b3d68b1d376c51af14d55a786e` | `a497536445bfa82b2cc0b1dea6615aaf3cb6b2b3d68b1d376c51af14d55a786e` | ok |
| bdh_europarl_ladRA2b-el_last.pt | 5,135,023,579 | `fa07ddf942abbd34334b6c2261821d15aeb28b9c0488b54ce3a4c93ad2398200` | `fa07ddf942abbd34334b6c2261821d15aeb28b9c0488b54ce3a4c93ad2398200` | ok |
| bdh_europarl_ladRA2b-en_best.pt | 1,211,147,355 | `8445696168605b16daeaeb0f63a50d7079b74ac1ad9f5998b17c5db487806e5e` | `8445696168605b16daeaeb0f63a50d7079b74ac1ad9f5998b17c5db487806e5e` | ok |
| bdh_europarl_ladRA2b-en_last.pt | 1,211,147,355 | `68aa631faef8dfb7ce86d51677d672ecdefc66a587b6d4eb8674bbcd5d2ddc84` | `68aa631faef8dfb7ce86d51677d672ecdefc66a587b6d4eb8674bbcd5d2ddc84` | ok |
| bdh_europarl_ladRA2b-es_best.pt | 1,511,046,575 | `2fa9890ae4399fff1fe136cb93e1aa3a70ca2dba29368d8962f8ed533b401d79` | `2fa9890ae4399fff1fe136cb93e1aa3a70ca2dba29368d8962f8ed533b401d79` | ok |
| bdh_europarl_ladRA2b-es_last.pt | 1,511,046,575 | `f129e7188e8b3c2b3c6010f5036b1e6fc8f7d5a2988674a8def29102a4fb24d8` | `f129e7188e8b3c2b3c6010f5036b1e6fc8f7d5a2988674a8def29102a4fb24d8` | ok |
| bdh_europarl_ladRA2b-et_best.pt | 4,833,025,499 | `644962b2c1de16f2e618bf9445d534c4f18327d047359d3879de4a8e308f177b` | `644962b2c1de16f2e618bf9445d534c4f18327d047359d3879de4a8e308f177b` | ok |
| bdh_europarl_ladRA2b-et_last.pt | 4,833,025,499 | `ae670c3af29443ff0438e852bb40753f584e796d86169d219e143eecd2cf1015` | `ae670c3af29443ff0438e852bb40753f584e796d86169d219e143eecd2cf1015` | ok |
| bdh_europarl_ladRA2b-fi_best.pt | 3,625,033,135 | `040789e753fe7030851bdbffdc625672966da0d69047d50ddae4908dcd3be05b` | `040789e753fe7030851bdbffdc625672966da0d69047d50ddae4908dcd3be05b` | ok |
| bdh_europarl_ladRA2b-fi_last.pt | 3,625,033,135 | `1274c3fb95e2451a53ea3277a68e23940d4f1b040da54bdc121d971c81baa157` | `1274c3fb95e2451a53ea3277a68e23940d4f1b040da54bdc121d971c81baa157` | ok |
| bdh_europarl_ladRA2b-fr_best.pt | 2,115,042,735 | `2c5a64180b8a385f6ea84ca8774052c4def41fd432a8fd396758b577e2f15c7f` | `2c5a64180b8a385f6ea84ca8774052c4def41fd432a8fd396758b577e2f15c7f` | ok |
| bdh_europarl_ladRA2b-fr_last.pt | 2,115,042,735 | `a9174bdf68c8c62e35e7fa3e95a12db7c5bf86832a194e8e074a2fc0d71c42d8` | `a9174bdf68c8c62e35e7fa3e95a12db7c5bf86832a194e8e074a2fc0d71c42d8` | ok |
| bdh_europarl_ladRA2b-hu_best.pt | 3,927,031,215 | `bd4e309f82f4ede093b9c32164eb61272420742d5738f845674cb657edb8a97c` | `bd4e309f82f4ede093b9c32164eb61272420742d5738f845674cb657edb8a97c` | ok |
| bdh_europarl_ladRA2b-hu_last.pt | 3,927,031,215 | `2ec10702dda8a040618bde3f7ef4d5178998d85883a0944f4aea22839ba20379` | `2ec10702dda8a040618bde3f7ef4d5178998d85883a0944f4aea22839ba20379` | ok |
| bdh_europarl_ladRA2b-it_best.pt | 4,531,027,407 | `3873609ac927dfae1d8840e930db1f4949fb6bbf04a22dfa8b76eaf62fda8a77` | `3873609ac927dfae1d8840e930db1f4949fb6bbf04a22dfa8b76eaf62fda8a77` | ok |
| bdh_europarl_ladRA2b-it_last.pt | 4,531,027,407 | `cca00b484dd91c600becdfbe99ef080c43d9f6780176c20370d94ea6dab00196` | `cca00b484dd91c600becdfbe99ef080c43d9f6780176c20370d94ea6dab00196` | ok |
| bdh_europarl_ladRA2b-lt_best.pt | 6,947,012,095 | `bb2789d3c2059bab7b8608e94eb88e1dfc960ab1191949c82d0f7dd6179faff6` | `bb2789d3c2059bab7b8608e94eb88e1dfc960ab1191949c82d0f7dd6179faff6` | ok |
| bdh_europarl_ladRA2b-lt_last.pt | 6,947,012,095 | `cada61d704ea15795056c18bbb99afd4bb49fc4ccdf1cdef7cad4ed6937c908c` | `cada61d704ea15795056c18bbb99afd4bb49fc4ccdf1cdef7cad4ed6937c908c` | ok |
| bdh_europarl_ladRA2b-nl_best.pt | 6,343,015,923 | `e2c3b13a879a49545aed4be2dc203b1369a06c32c761dec89bc1b17fd68b896a` | `e2c3b13a879a49545aed4be2dc203b1369a06c32c761dec89bc1b17fd68b896a` | ok |
| bdh_europarl_ladRA2b-nl_last.pt | 6,343,015,923 | `84776453bdb081b8c37e145633d885f4ac798e55b4aba9f87189e68750d5c9bc` | `84776453bdb081b8c37e145633d885f4ac798e55b4aba9f87189e68750d5c9bc` | ok |
| bdh_europarl_ladRA2b-pl_best.pt | 1,813,044,655 | `df2cb509f708a86483def5ccb39bdd2ce9d4ac619fc2be54daec4ac192488be9` | `df2cb509f708a86483def5ccb39bdd2ce9d4ac619fc2be54daec4ac192488be9` | ok |
| bdh_europarl_ladRA2b-pl_last.pt | 1,813,044,655 | `3a1a34ff1d14e21653c3824b77c11d1f6a446dfa9e3e95892fd58a15ffb886dc` | `3a1a34ff1d14e21653c3824b77c11d1f6a446dfa9e3e95892fd58a15ffb886dc` | ok |
| bdh_europarl_ladRA2b-pt_best.pt | 3,323,035,055 | `5c0e21a69350d582151f0850936afa5dfde91a70bcd413cb04a50a422fa50407` | `5c0e21a69350d582151f0850936afa5dfde91a70bcd413cb04a50a422fa50407` | ok |
| bdh_europarl_ladRA2b-pt_last.pt | 3,323,035,055 | `5e06e757fd6c32a2120561353c7ab40144b7a86a8fed784d5baab55739bea8ea` | `5e06e757fd6c32a2120561353c7ab40144b7a86a8fed784d5baab55739bea8ea` | ok |
| bdh_europarl_ladRA2b-ro_best.pt | 6,041,017,843 | `6caa26f524ef1114b463b546b04c569ad789cbce78f60d4d807ca4c4791c7da0` | `6caa26f524ef1114b463b546b04c569ad789cbce78f60d4d807ca4c4791c7da0` | ok |
| bdh_europarl_ladRA2b-ro_last.pt | 6,041,017,843 | `6f4fb88f6e7cc485a25ef6e66f73fb7dc84c7f3efaf41764e8007722979f905f` | `6f4fb88f6e7cc485a25ef6e66f73fb7dc84c7f3efaf41764e8007722979f905f` | ok |
| bdh_europarl_ladRA2b-sk_best.pt | 5,437,021,659 | `d341319cb709f4c2ea30163afb014dd676cc7403094e3c1c9b1e6cd7f9c2d13a` | `d341319cb709f4c2ea30163afb014dd676cc7403094e3c1c9b1e6cd7f9c2d13a` | ok |
| bdh_europarl_ladRA2b-sk_last.pt | 5,437,021,659 | `30e846bf55c1818b1daa66726e373871897b5dcfaa0c536d05402d0652ad0d12` | `30e846bf55c1818b1daa66726e373871897b5dcfaa0c536d05402d0652ad0d12` | ok |
| bdh_europarl_ladRA2b-sl_best.pt | 6,645,014,015 | `206cb8b882cb39c3b53c69c224e554c6e3684f6fdc627f7ab8a168bbee6a31dd` | `206cb8b882cb39c3b53c69c224e554c6e3684f6fdc627f7ab8a168bbee6a31dd` | ok |
| bdh_europarl_ladRA2b-sl_last.pt | 6,645,014,015 | `a98e927ebd088c8e6285fb634209277731fdef287072ed9fd7a0f56ca162bff4` | `a98e927ebd088c8e6285fb634209277731fdef287072ed9fd7a0f56ca162bff4` | ok |
| bdh_europarl_ladRA2b-sv_best.pt | 5,739,019,763 | `764d3e9161b8c49d49fe7ea3cd24ff963587e30e98a6c7599934fc01b767c312` | `764d3e9161b8c49d49fe7ea3cd24ff963587e30e98a6c7599934fc01b767c312` | ok |
| bdh_europarl_ladRA2b-sv_last.pt | 5,739,019,763 | `81988e39245158ad6029afb45436badb3390e9a94f754da25b7b06aa7fde0f47` | `81988e39245158ad6029afb45436badb3390e9a94f754da25b7b06aa7fde0f47` | ok |

## Reproduction

To re-verify at any later date: download each file from the HF repo, `sha256sum` it, compare against the pre-upload sha256 column. Any single mismatch is data damage; a match against the pre-upload digest (not the current oid alone) breaks the circularity that pi-50 named.
