<!-- this_file: TODO.md -->

# TODO

- [x] Complete all nine remote benchmarks, rebuild all reports, publish and verify the OpenRouter API filter live.

- [x] Add OpenRouter native remote support, all nine IDs, tests and benchmark execution labels.
- [x] Run authenticated smokes for all nine remote models; record Respan as noul-only and enforce its capabilities.

- [x] Publish and verify the 291-run Metal/device audit and interactive benchmark explorer.

- [x] Complete issue 102: all variants measured, models integrated, 290-method report rebuilt and final publication verified live.

- [x] Run the ollaya engine test (`pytest -m engine tests/test_ollaya.py`) with kev:0.8b in `OLLAYA_MODELS`.
- [ ] Decide whether `jevk5-4b` and `openjev-35b-a3b` are "fine-tuned" (registry) or "dedicated" (book data).

## Follow-ups from the anti-slop review

- [ ] Test the pydantic_ai provider on the ollaya path.
- [ ] Decide whether `calibrated` should pass through the pydantic_ai provider.
- [ ] Stop tests coupling to `Decider._post`; stub the HTTP layer instead.
- [ ] Reduce `_kev_in_store` coupling to the ollaya store layout.
- [ ] Stop hard-coding benchmark counts in registry notes, which go stale.

- [x] Publish the 302-run local results and verify the actual HTTPS explorer/assets.
- [ ] Resolve excluded heavy-load and ggmlc Metal failures before further GPU measurements.
- [x] Add and verify the public Laya MLX native integration and a separate current-runtime benchmark.
- [x] Integrate and verify native xDecision F16/Q8 with package tests and full benchmarks.
- [x] Publish and verify the 305-configuration native encoder explorer on HTTPS.

- [x] Publish and verify the 308-configuration GPU provider/head comparison.

- [x] Publish and verify the 309-configuration Weidows MPS comparison.

- [x] Review all 42 historical CPU/mixed/automatic configurations; measure safe useful alternatives and retain explicit failed/refused/deferred exclusions.

## System One expansion

- [x] Register fifteen pinned repositories and implement compatible native or explicitly labelled fallback readouts.
- [x] Complete eleven guarded benchmarks and retain all 309 historical rows.
- [ ] Verify the Rune v3 native endpoint on a host with sufficient safe memory.
- [ ] Resolve CoreAIKit scorer startup memory growth before another guarded inference attempt.
- [ ] Enable FluidInference Gemma when a trained artifact is published, and Nev Lite when its required runtime is accessible.

## Clef and CLM quantizations

- [x] Remove failed-only and below-50 downloads while preserving low results and shared successful weights.
- [x] Integrate fourteen pinned native configurations and verify all nine safely completed benchmarks.
- [x] Preserve all 320 earlier rows and publishable low-scoring CLM measurements after weight pruning.
- [x] Publish the 329-configuration build and verify the actual HTTPS artifacts and explorer.
- [ ] Measure Clef Q3/Q4/Q5, Clef MLX 4-bit and Clef-Flash MLX 8-bit when the unchanged memory preflight permits.

## Native Core AI additions

- [x] Build the pinned native bridge and expose PII spans/redaction with explicit full-input rejection.
- [x] Register Clef-Flash Core AI FP16/int8mix with pinned decoder, head and lexical table.
- [x] Run and verify the separate 20-text PII benchmark while retaining every router measurement.
- [x] Close this benchmark edition with Clef Core AI skipped by user; retain the experimental integration without fabricated measurements.
- [x] Publish the Core AI source/docs update and verify live PII evidence and retained router explorer.

- [x] Publish finalized benchmark and PyPI 0.1.3; verify deployed artifacts, release hashes and clean installed native engines.
