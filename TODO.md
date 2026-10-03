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

- [ ] Publish and verify the 308-configuration GPU provider/head comparison.
