<!-- this_file: PLAN.md -->

# Plan

OpenRouter support is implemented using the existing System One vocabulary,
httpx transport and TypeSafe integration. Nine exact model IDs are discoverable;
other decision IDs are accepted explicitly. Unit and transport tests verify
authentication, typed answers, usage, malformed replies and errors without
billable inference. The private benchmark harness opts into selected remote
IDs with `OPENROUTER_MODELS` and exports their execution as R.

Authenticated verification completed using the existing key in ~/.env. Six
models accept all three question kinds; the three Respan variants accept only
noul. Capability checks reject unsupported requests before inference. Private
smoke evidence records resolved model, provider and usage. These are protocol
checks. Full 67-query benchmarks are complete for all nine endpoints,
with frozen translations and an explicit noul OVR readout for Respan. All public tables and diagrams are rebuilt and published from main:/docs.
Fresh live browser checks verify the OpenRouter API engine filter against all
nine measured rows, the 300-run report and its chart/download interactions.
Package publication remains a separate release through `publish.sh`.
