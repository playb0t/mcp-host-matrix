# Evidence for two historical observations

## R01: provider revocation windows

Absence of a provider revocation request was confirmed in 12 of 12 retrospectively selected base windows across 6 routes with 2 authentication profiles per route. Confirmation requires at least 60 seconds of observation after the operation acknowledgement.

[Declared run IDs and computed counts](R01.json) · [Base windows and control](../disconnect/bench/RESULTS.json) · [Recorded excerpts](../disconnect/bench/receipts/R01.json)

## R04: bridge log order

The bridge logged that it treated the still-running helper as the browser. It reported success 1 ms later. The bridge logged helper exit 0 another 127 ms after success.

[Messages, line numbers and intervals](R04.json) · [Reviewed capture](r04-timing.json) · [Recorded excerpts](../matrix/receipts/R04.json)

## Reproduce

From the repository root:

```console
python -B tools/receipt_import.py --ground R01
python -B tools/receipt_import.py --ground R04
python -B tools/validate.py
```

The two read-only commands return the reader statement and a separately computed result. The validator runs both calculations against manifest-listed files. For R01 and R04, the CLI generates the statement from the computed result using a fixed form. The validator also compares the saved reader section above with the generated text. Other editorial prose remains subject to review. The R01 control recorded logout and a refused refresh; the R04 helper was an inert recorder. The original rows, receipts and coverage totals retain their published bytes.

**Cohort.** An explicit set of unique base run IDs defines the denominator. Controls and other timing windows have their own IDs. A healthy negative window must meet the minimum duration and show a completed observation of the operation. An interrupted or short window remains in the denominator with an unknown result. A recorded request contradicts the absence claim. The evaluator reconciles the recorded string and object forms with the normalized projection; an absence accompanied by a request ID or response is inconsistent. Retrospective selection is explicit. A before-measurement selection additionally requires a matching plan and a journal linking its seal, each start and its recorded verdict. This checks the recorded chronology; provenance of the journal still requires review.

**Order.** Each event reference names a run, clock and log fingerprint. A single capture supplies the numbered messages. The checker reads their embedded UTC times, verifies the emitter and message, orders them by line and time, and computes the adjacent intervals. The retained extract has the original bytes of the source named in the published receipt. The mapping from extract to full run log was reviewed separately. An OS exit time or browser launch would need its own witness.

## Optional use in new projections

Free-text observations remain supported. A producer may attach a ground to one sentence in a projection receipt:

```json
{"grounds":[{"observation_index":0,"logical_path":"evidence/ground.json","sha256":"<ground SHA-256>"}]}
```

The ground and each of its JSON sources must be direct public artifacts in the research receipt. The case ID and linked sentence must match. A window cohort or event order requires a registered statement form for its case. The importer rejects these grounds for an unregistered case. When a form is added for a new cell, its source receipt must also identify the subject and versions. The two historical adapters accept the revoke-bench projection and the numbered bridge-log capture shapes shown above. Applying them to a different recorder requires compatible evidence. Use the returned structured result when testing a machine claim; acceptance cannot establish that arbitrary prose is true or that a recorder was honest.

For simple event pairs, use `kind: atomic_events`, `parameters.claims` as in the [paired examples](../examples/claims/README.md), and `expected.events` for the canonical event labels. This keeps the evidence separate from the reader's sentence. Existing receipts that explicitly use top-level `claims` retain their exact-label check. A receipt without optional grounds continues through the existing import checks.
