# RTL Fmax agent benchmark

**Preliminary results, updated as sessions finish and models are added.**

![Fmax gain and normalized score per model over the designs it has finished](charts/model-fmax.png)

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
**Status:** 143 of 160 sessions finished (8 models, 20 designs), as of 2026-11-18 20:43 PST.

### Coverage

| Model | Developer | Harness | Access | Sessions finished |
|---|---|---|---|---:|
| Claude Fable 5.2 | Anthropic | Claude Code 2.1.322 | Official CLI signed in to a subscription | 20 / 20 |
| GPT-6 Astra | OpenAI | Codex 0.154.0 | Official CLI signed in to a subscription | 20 / 20 |
| Kimi K3.1 Pro | Moonshot AI | Kimi Code 2.5.2 | OpenRouter, pinned to Moonshot AI's own endpoint (MXFP4), fallbacks disabled | 20 / 20 |
| Qwen3.8 2.4T-A95B | Qwen (Alibaba) | Qwen Code 0.27.1 | OpenRouter, one pinned provider (SiliconFlow, FP8) | 20 / 20 |
| Ripple-65B Preview | Ricursive AI | OpenCode 1.19.5 | Self-hosted (SGLang 0.5.19, BF16) for its first 15 designs; OpenRouter pinned to PrimeIntellect (BF16) for later sessions | 20 / 20 |
| Nemotron 3 Ultra 550B-A55B | NVIDIA | OpenCode 1.19.5 | OpenRouter, pinned to DeepInfra (FP4), fallbacks disabled | 20 / 20 |
| GPT-6.2 Astra | OpenAI | Codex 0.169.1 | Official CLI signed in to a subscription; reasoning effort medium, as GPT-6 Astra ran | 6 / 20 |
| Claude Opus 5.5 | Anthropic | Claude Code 2.1.322 | Official CLI signed in to a subscription | 17 / 20 |

### Results by model

| Model | Harness | Designs finished | Fmax gain (geomean) | Normalized score | Designs improved | Mean evaluations | Candidates not proven |
|---|---|---:|---:|---:|---:|---:|---:|
| Claude Fable 5.2 | Claude Code | 20 / 20 | +10.39% | 77.1 | 17 / 20 | 5.0 | 42% (42 / 99) |
| Claude Opus 5.5 | Claude Code | 17 / 20 | +9.66% | 73.3 | 16 / 17 | 4.5 | 36% (28 / 77) |
| GPT-6.2 Astra | Codex | 6 / 20 | +7.21% | 53.9 | 6 / 6 | 8.0 | 54% (26 / 48) |
| GPT-6 Astra | Codex | 20 / 20 | +7.04% | 58.4 | 19 / 20 | 8.4 | 27% (45 / 169) |
| Kimi K3.1 Pro | Kimi Code | 20 / 20 | +3.81% | 37.0 | 16 / 20 | 5.9 | 63% (74 / 118) |
| Qwen3.8 2.4T-A95B | Qwen Code | 20 / 20 | +2.08% | 12.0 | 8 / 20 | 2.1 | 67% (28 / 42) |
| Nemotron 3 Ultra 550B-A55B | OpenCode | 20 / 20 | +0.79% | 8.2 | 4 / 20 | 6.2 | 72% (89 / 123) |
| Ripple-65B Preview | OpenCode | 20 / 20 | +0.00% | 0.0 | 0 / 20 | 0.1 | 100% (3 / 3) |

Fmax gain is the geometric mean of each finished session's Fmax ratio (baseline period / best accepted period) over the designs that model has finished. Normalized score is the mean of its gain on each design as a percentage of the best gain any model here reached on that design (100: the best result on every design), so every design counts equally however much headroom it had. Models have finished different designs, so this order is provisional, not a like-for-like ranking, until every model covers the same designs. "Candidates not proven" is the share of evaluations whose equivalence proof did not pass.

### Best result by design

| Design | Baseline period (ns) | Sessions finished | Best period (ns) | Fmax gain | Best by |
|---|---:|---:|---:|---:|---|
| `cheshire.default` | 1.047 | 7 | 0.957 | +9.40% | Claude Opus 5.5 |
| `cv32e40p.default` | 0.657 | 7 | 0.620 | +5.97% | GPT-6 Astra |
| `cva6.default` | 1.038 | 7 | 1.005 | +3.28% | Claude Opus 5.5 |
| `cvfpu.fp32_fma` | 1.401 | 7 | 1.070 | +30.93% | Claude Fable 5.2 |
| `cvfpu.full` | 2.114 | 7 | 1.976 | +6.98% | Claude Opus 5.5 |
| `ibex.full` | 0.935 | 7 | 0.899 | +4.00% | GPT-6 Astra, Kimi K3.1 Pro |
| `ibex.minimal` | 0.716 | 7 | 0.676 | +5.92% | Claude Fable 5.2 |
| `nvdla.top` | 0.789 | 6 | 0.728 | +8.38% | Claude Fable 5.2 |
| `opope.default` | 0.857 | 6 | 0.816 | +5.02% | Kimi K3.1 Pro |
| `serial_link.default` | 0.305 | 7 | 0.266 | +14.66% | Claude Opus 5.5 |
| `spi_host.default` | 0.475 | 6 | 0.365 | +30.14% | Claude Fable 5.2 |
| `snitch_cluster.minimal` | 1.288 | 7 | 1.200 | +7.33% | GPT-6 Astra, Kimi K3.1 Pro |
| `ita.default` | 0.903 | 7 | 0.900 | +0.33% | Claude Fable 5.2 |
| `mempool.minpool` | 2.869 | 7 | 1.913 | +49.97% | Claude Opus 5.5 |
| `ara.default` | 1.064 | 8 | 0.926 | +14.90% | GPT-6.2 Astra |
| `pulp_c910.default` | 1.005 | 8 | 0.902 | +11.42% | Claude Opus 5.5 |
| `spatz.default` | 2.266 | 8 | 1.868 | +21.31% | Claude Fable 5.2 |
| `snitch_cluster.default` | 2.128 | 8 | 1.751 | +21.53% | Claude Fable 5.2 |
| `redmule.default` | 1.636 | 8 | 1.542 | +6.10% | Claude Fable 5.2 |
| `snitch_cluster.default_latch` | 2.169 | 8 | 1.871 | +15.93% | Claude Fable 5.2 |

### Early observations

Counts over every finished session of the models above. They describe what happened; with one session per model and design they do not establish causes or rankings.

- 679 candidates evaluated: 197 accepted, 139 proven equivalent but not faster than the session's best, 335 not proven (243 with a partition EQY could not prove, 40 at the proof deadline, 46 over the proof memory budget, 6 for another reason), 8 failed to compile or measure.
- Of 143 finished sessions, 97 ended with the agent finishing on its own, 45 ran to the time budget and 1 ended with an agent error.
- Sessions used 4.7 of the 10 allowed evaluations on average; 22 used all 10.
- Largest single gain so far: `mempool.minpool` by Claude Opus 5.5, 2.869 ns to 1.913 ns (+49.97% Fmax).
<!-- results:end -->

## Charts

The chart at the top shows each model's aggregates. This one shows every session:

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
