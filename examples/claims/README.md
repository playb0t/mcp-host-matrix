# Paired observation claims

These fixtures exercise the importer. Each pair uses identical observation bytes. The selected claims, their rendered text and the hashes of the projection and receipt change between alternatives.

| Fixture | Supported observation | Rejected alternative |
|---|---|---|
| [Connection](connection.json) | Connection established; protected request denied. | The protected handler executed. |
| [Objects](objects.json) | Policy checked A; handler applied the operation to B. The calibration records A to A. | The handler applied the operation to A in the test attempt. |
| [Window](window.json) | Receipt of A was recorded before the observer stopped. | The handler never executed in that interrupted attempt. The separate complete retry has its own ID. |

When a producer opts into exact event statements, put the structured statements in the projection receipt's `claims` array. Each statement identifies a direct public JSON source, an observation attempt, a separate control attempt, an event channel, an object and a predicate (`present` or `absent`). Store the `matrix-observation/1` record under `observation` in that source. The record identifies the case, subject, versions, operation, boundary, observer and monitored channels. Record an actual complete observation window as `complete` and a truncated or unhealthy window as `interrupted`. Use separate records for different recorder configurations.

The importer checks event/object pairs within the designated attempt. Its control must have recorded the channel in a complete window under the same recorder configuration. A positive observation survives interruption. An absence applies only to that channel and object within one complete window. No events are borrowed from a retry. Repetition, event order, causal linkage and independent recorder authenticity require separate evidence and review.

The case's `observations` must match its ordered claims using the form `operation [source, boundary, observer, attempt, control ID]: channel(object) predicate.` All synthetic fixtures use the component boundary. Free prose in limits and other descriptive fields remains subject to review. Existing six pinned observations retain their original format. Producers can also keep readable observations and attach an optional [evidence ground](../../grounds/README.md) to a selected sentence. Omitting a ground makes no machine claim about that sentence.

Run the full importer CLI regression from the repository root:

```console
python -B -m unittest discover -s tests -p test_observation_claims.py
```
