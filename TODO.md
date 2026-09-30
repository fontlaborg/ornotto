<!-- this_file: TODO.md -->

# TODO

- [ ] Run the ollaya engine test (`pytest -m engine tests/test_ollaya.py`) with kev:0.8b in `OLLAYA_MODELS`.
- [ ] Decide whether `jevk5-4b` and `openjev-35b-a3b` are "fine-tuned" (registry) or "dedicated" (book data).

## Follow-ups from the anti-slop review

- [ ] Test the pydantic_ai provider on the ollaya path.
- [ ] Decide whether `calibrated` should pass through the pydantic_ai provider.
- [ ] Stop tests coupling to `Decider._post`; stub the HTTP layer instead.
- [ ] Reduce `_kev_in_store` coupling to the ollaya store layout.
- [ ] Stop hard-coding benchmark counts in registry notes, which go stale.
