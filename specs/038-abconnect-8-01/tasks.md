# Implementation checkpoints

## Core contracts and transport (implemented locally)

- [x] Source-check inventory, handling units, shipping collections, rates, and shipment controllers at server release `23a8a00cd3883b4e4783de76f3e5e8c8b901660a`.
- [x] Add strict nested requests and typed responses, preserving explicit nulls for nullable packing/export fields.
- [x] Implement 4 inventory, 17 handling-unit, 1 shipping collection, 2 rate, and 5 explicit shipment routes.
- [x] Keep shipping-record IDs, quote UUIDs, and carrier shipment IDs distinct.
- [x] Cover invalid selectors, nested validation, relationships, array bodies, export round trips, concurrency fields, and multiple/archived/conflicting shipping selection with deterministic tests.
- [x] Add supported-request warnings, and guard legacy booking/delete/export mutations against ambiguous shipping collections.
- [x] Add runnable operator-selected examples, generated reference pages, and migration guidance.
- [x] Reconcile route/stub counts and regenerate progress without changing the gate baseline.

## Remaining release work

- [x] Reconcile removed parcel/freight/item write methods and helpers with lossless adapters or explicit unsupported errors; current old write methods are not certified for 8_01.
- [x] Reconcile legacy rate/accessorial methods with the new rates and transportation-add-on contracts.
- [x] Update freight-provider list/filter/final-override/final-quote contracts (the controller returns TransportationQuote and no longer accepts the old provider-list write).
- [x] Reconcile remaining changed tracking/document/form/payment routes and response shapes against server source, including every removed Swagger operation.
- [x] Implement company inventory/packing support needed by certified end-to-end scenarios.
- [x] Capture and review real requests/responses for new models and replace fixture-test skips with verified evidence.
- [x] Verify packing mutations/cleanup on an empty LIVE estimate and targeted export isolation with two active shipments.
- [x] Extend live isolation coverage to nonempty materials, rates, booking validation, and approved carrier booking/cancellation scenarios.
- [x] Complete compatibility matrix and warning checks for every affected public entry point.
- [x] Prepare the supported Python CI matrix and build/validate 0.3.0 artifacts.

The user authorized all staging data as disposable. See [validation.md](validation.md)
for observed results, retained test records, and the distinction between failed
normal carrier cancellation and successful forced ABConnect removal.

- [x] Hosted release closure: Python CI matrix, PyPI upload/fresh install, mirrored
  tag, exact Read the Docs build, and stable/root routing. Verified; see the
  GitHub release and validation.md for URLs and exact commits.
