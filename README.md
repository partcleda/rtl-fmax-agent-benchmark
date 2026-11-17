# RTL Fmax agent benchmark

**Preliminary results, updated as sessions finish and models are added.**

How far can a stock coding agent raise the maximum clock frequency (Fmax) of real RTL while keeping it
formally equivalent to the original? Each model runs in its own family's official coding CLI (or OpenCode),
with that CLI's own prompt, tools and context management, for one continuous session per design on
[20 open-source designs](docs/benchmarks.md), most of them from the ETH Zurich PULP platform. The agent may
edit only the design's `sources.sv`. It can synthesize and time its RTL with boson, Partcl's
GPU-accelerated EDA tool for synthesis and static timing, and simulate and check equivalence with Verilator
and EQY. Each session has at most 10 candidate evaluations through `./evaluate`: boson synthesis and
unplaced setup timing on the public ASAP7 TT libraries with a 1 ps period search, then an EQY equivalence
proof against the original RTL. A session's score is baseline period / best accepted period; a candidate is
accepted only when it is proven equivalent and faster than the session's best so far.

> **One session per model and design.** There are no repeats, so there are no confidence intervals, and a
> single session's luck can move a model's aggregate. A model's aggregate covers only the designs it has
> finished; the note under the results table says whether every model has finished the same designs.

## Results

<!-- results:start -->
**Status:** 110 of 120 sessions finished (6 models, 20 designs), as of 2026-11-17 00:05 PST. 7 interrupted attempts are excluded from these results while awaiting a valid replacement.

### Coverage

| Model | Developer | Harness | Access | Sessions finished |
|---|---|---|---|---:|
| Claude Fable 5.2 | Anthropic | Claude Code 2.1.322 | Official CLI signed in to a subscription | 20 / 20 |
| GPT-6 Astra | OpenAI | Codex 0.154.0 | Official CLI signed in to a subscription | 20 / 20 |
| Kimi K3.1 Pro | Moonshot AI | Kimi Code 2.5.2 | OpenRouter, pinned to Moonshot AI's own endpoint (MXFP4), fallbacks disabled | 20 / 20 |
| Qwen3.8 2.4T-A95B | Qwen (Alibaba) | Qwen Code 0.27.1 | OpenRouter, one pinned provider (SiliconFlow, FP8) | 20 / 20 |
| Ripple-65B Preview | Ricursive AI | OpenCode 1.19.5 | Self-hosted (SGLang 0.5.19, BF16) for its first 15 designs; OpenRouter pinned to PrimeIntellect (BF16) for later sessions | 20 / 20 |
| Nemotron 3 Ultra 550B-A55B | NVIDIA | OpenCode 1.19.5 | OpenRouter, pinned to DeepInfra (FP4), fallbacks disabled | 10 / 20 |

### Results by model

| Model | Harness | Designs finished | Fmax gain (geomean) | Designs improved | Mean evaluations | Candidates not proven |
|---|---|---:|---:|---:|---:|---:|
| Claude Fable 5.2 | Claude Code | 20 / 20 | +10.39% | 17 / 20 | 5.0 | 42% (42 / 99) |
| GPT-6 Astra | Codex | 20 / 20 | +7.04% | 19 / 20 | 8.4 | 27% (45 / 169) |
| Kimi K3.1 Pro | Kimi Code | 20 / 20 | +3.81% | 16 / 20 | 5.9 | 63% (74 / 118) |
| Qwen3.8 2.4T-A95B | Qwen Code | 20 / 20 | +2.08% | 8 / 20 | 2.1 | 67% (28 / 42) |
| Nemotron 3 Ultra 550B-A55B | OpenCode | 10 / 20 | +0.68% | 3 / 10 | 7.3 | 68% (50 / 73) |
| Ripple-65B Preview | OpenCode | 20 / 20 | +0.00% | 0 / 20 | 0.1 | 100% (3 / 3) |

Fmax gain is the geometric mean of each finished session's Fmax ratio (baseline period / best accepted period) over the designs that model has finished. Models have finished different designs, so this order is provisional, not a like-for-like ranking, until every model covers the same designs. "Candidates not proven" is the share of evaluations whose equivalence proof did not pass.

### Best result by design

| Design | Baseline period (ns) | Sessions finished | Best period (ns) | Fmax gain | Best by |
|---|---:|---:|---:|---:|---|
| `cheshire.default` | 1.047 | 6 | 0.963 | +8.72% | GPT-6 Astra |
| `cv32e40p.default` | 0.657 | 6 | 0.620 | +5.97% | GPT-6 Astra |
| `cva6.default` | 1.038 | 6 | 1.016 | +2.17% | Claude Fable 5.2, GPT-6 Astra |
| `cvfpu.fp32_fma` | 1.401 | 6 | 1.070 | +30.93% | Claude Fable 5.2 |
| `cvfpu.full` | 2.114 | 6 | 1.981 | +6.71% | Claude Fable 5.2 |
| `ibex.full` | 0.935 | 6 | 0.899 | +4.00% | GPT-6 Astra, Kimi K3.1 Pro |
| `ibex.minimal` | 0.716 | 6 | 0.676 | +5.92% | Claude Fable 5.2 |
| `nvdla.top` | 0.789 | 6 | 0.728 | +8.38% | Claude Fable 5.2 |
| `opope.default` | 0.857 | 6 | 0.816 | +5.02% | Kimi K3.1 Pro |
| `serial_link.default` | 0.305 | 5 | 0.270 | +12.96% | Claude Fable 5.2 |
| `spi_host.default` | 0.475 | 5 | 0.365 | +30.14% | Claude Fable 5.2 |
| `snitch_cluster.minimal` | 1.288 | 5 | 1.200 | +7.33% | GPT-6 Astra, Kimi K3.1 Pro |
| `ita.default` | 0.903 | 6 | 0.900 | +0.33% | Claude Fable 5.2 |
| `mempool.minpool` | 2.869 | 5 | 2.342 | +22.50% | GPT-6 Astra |
| `ara.default` | 1.064 | 5 | 0.942 | +12.95% | Claude Fable 5.2 |
| `pulp_c910.default` | 1.005 | 5 | 0.930 | +8.06% | GPT-6 Astra |
| `spatz.default` | 2.266 | 5 | 1.868 | +21.31% | Claude Fable 5.2 |
| `snitch_cluster.default` | 2.128 | 5 | 1.751 | +21.53% | Claude Fable 5.2 |
| `redmule.default` | 1.636 | 5 | 1.542 | +6.10% | Claude Fable 5.2 |
| `snitch_cluster.default_latch` | 2.169 | 5 | 1.871 | +15.93% | Claude Fable 5.2 |

### Early observations

Counts over every finished session of the models above. They describe what happened; with one session per model and design they do not establish causes or rankings.

- 504 candidates evaluated: 145 accepted, 111 proven equivalent but not faster than the session's best, 242 not proven (185 with a partition EQY could not prove, 27 at the proof deadline, 24 over the proof memory budget, 6 for another reason), 6 failed to compile or measure.
- Of 110 finished sessions, 76 ended with the agent finishing on its own, 33 ran to the time budget and 1 ended with an agent error.
- Sessions used 4.6 of the 10 allowed evaluations on average; 18 used all 10.
- Largest single gain so far: `cvfpu.fp32_fma` by Claude Fable 5.2, 1.401 ns to 1.070 ns (+30.93% Fmax).
<!-- results:end -->

## Charts

![Geometric-mean Fmax gain per model over the designs it has finished](charts/model-fmax.png)

![Fmax gain per design and model](charts/design-fmax.png)

Vector versions: [model-fmax.svg](charts/model-fmax.svg), [design-fmax.svg](charts/design-fmax.svg).
The charts are rendered from `results/` by [charts/generate.py](charts/generate.py).

## Documentation and data

- [docs/methodology.md](docs/methodology.md): sessions and evaluations, the exact prompt and `TASK.md`,
  acceptance, budgets, the agent environment, controls, rerun rules, models and harnesses, limitations.
- [docs/benchmarks.md](docs/benchmarks.md): the 20 designs, their origin, baselines and session budgets.
- [results/](results/): `sessions.csv` (one row per model and design), `evaluations.csv` (one row per
  candidate evaluation), `summary.json` (per-model aggregates) and `models.json` (models and harnesses).
  The column definitions are in the methodology.
- The results section above is generated from `results/` by
  [scripts/render_readme.py](scripts/render_readme.py).

## License

Copyright 2026 Partcl. The code in this repository (`charts/generate.py` and `scripts/`) is licensed under
the [Apache License 2.0](LICENSE). The data (`results/`), the charts and the documentation, including this
README, are licensed under [Creative Commons Attribution 4.0 International](LICENSE-CC-BY-4.0).
