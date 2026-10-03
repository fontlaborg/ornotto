---
this_file: src_docs/md/results/explorer.md
---

# Find the fastest useful answer

An extra correct answer can cost hundreds of milliseconds. Choose the score you need, then compare the runs that meet it. The default floor is **50 correct answers out of 67**. Laya on MLX clears it at **52/67 in 6.9 ms** on translated text; a model does not have to top the accuracy table to be useful.

These are 302 recorded configurations, not 302 different models. Each point names its engine, quantization and execution device. Set **Direct** to compare original multilingual queries; its chart uses the recorded direct-mode latency. The translated-mode latency covers classification alone and excludes the translation step.

--8<-- "tables/explorer.html"

## OpenRouter: nine remote models

All nine requested endpoints were measured on the same 67 queries, in translated and direct modes, on 3 October 2026. Translations and local results are retained from the earlier runs. Each endpoint received 106 distinct inputs, sequentially, with duplicate inputs reused across modes. Latency includes the network trip and provider processing; **R** means the provider did not disclose CPU/GPU placement or weight precision.

Six endpoints use a native five-way **choice**. Respan's three endpoints support **noul** only: each request contains five independent yes/no questions using the same task descriptions. We choose the largest P(true), then normalize the five values for the routing report. This **noul OVR** readout is labelled separately; its values are not calibrated exclusive-choice probabilities. Choose **OpenRouter API** in the explorer's engine filter to select all nine endpoints. Its table shows the readout for each run.

--8<-- "tables/remote.html"

## Read the frontier

A run is on the **Pareto frontier** when no other visible run is both at least as accurate and at least as fast (or small), with a strict improvement in one. Equal points remain tied. Change a filter and the frontier is recalculated within that subset. It is a description of these measurements, not statistical evidence that one model is better.

- **Speed frontier** compares accuracy with mean classification latency. A hosted point includes its network trip; local points include their runtime and loopback overhead. Device filters let you compare CPU runs with CPU runs, or GPU runs with GPU runs.
- **Size frontier** compares accuracy with recorded storage size in decimal GB (weight files, or the complete prepared Splash package). It excludes runs with no recorded size, including hosted Jev. It does not measure peak memory, KV cache or computation buffers.
- **Fastest qualifying runs** sorts the current selection by latency. With “Pareto frontier only” checked, that bar chart, the table and the CSV show the speed frontier; the size plot shows its own frontier.

Hover to inspect a point, click for execution evidence, drag to zoom, and double-click to reset the chart. The camera control exports an SVG. Filter settings are stored in the URL so you can share a view. A blank direct score means an English-only run and is excluded from Direct mode.

## Rune Q4: the device changed the result

The fresh full-Metal Q4 run requested all layers with `--gpu-layers -1`; the server reported `MTL0`. It measured **124.8 ms/query**, with **63/67 translated and 64/67 direct**, against **487.1 ms/query** for the earlier CPU-weight/Metal-compute configuration. That is **3.9× faster** with the same answers. Both rows are retained: search `rune q4` and lower the minimum score if necessary.

Q3 and the new Q4/Q5 configurations request GPU weights. The historical Q5 keeps CPU weights with Metal computation and KV offload (**C+G**). Q8 is CPU-only (**C**). Their timings must not be read as a pure quantization comparison. See the [CPU audit](details.md#cpu-and-mixed-runs) for the other CPU and mixed pipelines.

## Rune Q5 and Splash: two completed October runs

The separate **Rune Q5 full-Metal** run scores **64/67 in both modes**, at **153.3 ms/query translated** and **152.8 ms direct**. It is **6.3× faster** than the retained mixed CPU-weight/Metal-compute run at 962.3 ms, but changes one answer in each mode and loses one correct answer. The weights and frozen translations are the same; changed device arithmetic is not evidence of identical predictions. Search `rune q5` to compare both configurations.

**Ornith 1.5 35B-A3B on Splash 1.1.0** scores **62/67 translated at 322.4 ms** and **63/67 direct at 328.5 ms**. Select **Splash (Metal)** to see its single completed row. The native System One endpoint reads five option probabilities without generating text. These timings do not measure speculative decoding throughput. Calibration on this task is unverified. Its **20.95 GB** is the prepared package's storage size, including target, draft and tokenizer, rather than runtime memory; the packed MoE format has mixed q4/q8 sections. It is a fine-tuned model, and package geometry limits compatibility. See the [Splash source and runtime documentation](https://github.com/incoai/splash).

Each new method has 106 successful distinct-input records, reused to evaluate all 67 queries in both modes. All 300 earlier public rows and their underlying query records and translations are retained unchanged.

### Runs excluded from the charts

Qwen3.6 Splash was refused before loading: 33 GiB available versus the unchanged conservative 40 GiB requirement. Swift Splash loading coincided with a host kernel panic involving the storage stack; its root cause remains unresolved. Dense Qwen3.8 Splash and Rune Q8 full-Metal remain untried and excluded. Laya Q8 on ggmlc Metal loaded but aborted on its first question with unsupported operation `MAP_CUSTOM2`; no successful benchmark records were saved. The F16 and Q4 alternatives are deferred because they use the same runtime path. None is a zero-score chart point or a completed run.

The GPU audit retains existing faster native alternatives for CPU dohnuts and Laya. ONNX CPU rows remain labelled CPU: a Core ML provider setting would permit fallback and needs a separately verified run. Automatic Core ML/Core AI placement stays A. Jev-Omni and Neutron retain GPU encoders with CPU heads; pooled embeddings or GPU heads need probability agreement checks before measurement. Lower-scoring CLM pipelines are not priority retries. GPU preference follows measured score and latency, not a launch flag.

## Devices and evidence

**C** means CPU inference; **G** means GPU inference on Metal, MLX or PyTorch MPS. **C+G** identifies an explicit CPU model/head component plus GPU work, and **C+N** permits CPU and Neural Engine. Routine CPU tokenization and orchestration do not turn every GPU run into C+G. **A** means automatic CPU/GPU/Neural Engine placement whose exact assignment was not recorded. **R** means a remote service whose hardware is undisclosed; **?** is reserved for missing CPU/GPU evidence.

Most historical labels are reconstructed from recorded launch settings and runtime recipes and marked **configured**. The fresh Rune Q4/Q5 labels are **observed** from its Metal server log. These labels do not claim that every operation was profiled. Four automatic-placement runs cannot honestly be labelled CPU-only or GPU-only.

## Download or regenerate

[Download the self-contained explorer](../downloads/benchmark-explorer.html). Save the HTML file and open it locally: its results, chart library and controls are embedded, so it works offline. The CSV button exports the currently selected runs with their device descriptions and evidence.

The tool is [`src_docs/gen_diagrams.py`](https://github.com/fontlaborg/ornotto/blob/main/src_docs/gen_diagrams.py). Run `python3 src_docs/gen_diagrams.py --data src_docs/data/classifiers.json --out explorer.html` from the repository. `./docs.sh` regenerates the book's explorer and offline download automatically. Plotly.js 3.1.0 is bundled under its MIT licence.

## How this compares with the Decision Index

The [Jev Decision Index](https://huggingface.co/spaces/multimodalart/jev-decision-index) uses a broad, chance-corrected benchmark panel. This report measures one five-way FontLab routing task, with 67 queries in 30 languages. Its **52/67** is a count of correct routing answers, not 52 Decision Index points. The suites, metrics and latency protocols differ, so their scores and timings cannot be ranked together.

Our contribution is a detailed comparison of local runtimes, quantizations and devices, with the hosted Jev reference measured on the same routing inputs. For the prompts, timing boundaries and limitations, read [How we measured](../05-method.md). A difference of one or two answers on this small set needs a larger, held-out test before it guides a close choice.
