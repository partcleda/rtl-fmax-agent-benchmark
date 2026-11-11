# RTL Fmax agent benchmark

**Preliminary results, updated as sessions finish.**

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

> **The ranking is provisional.** Sessions finish at different times, so models have so far finished
> different designs. A model's aggregate covers only its own finished designs, and the order below becomes
> a like-for-like ranking only once every model covers the same designs. There is one session per model
> and design, so there are no confidence intervals.

## Results

<!-- results:start -->
**Status:** 16 of 95 sessions finished (5 models, 20 designs), as of 2026-11-11 12:03 PST.

### Coverage

| Model | Developer | Harness | Access | Sessions finished |
|---|---|---|---|---:|
| Claude Fable 5.2 | Anthropic | Claude Code 2.1.322 | Official CLI signed in to a subscription | 0 / 20 |
| GPT-6 Astra | OpenAI | Codex 0.154.0 | Official CLI signed in to a subscription | 0 / 20 |
| Kimi K3.1 Pro | Moonshot AI | Kimi Code 2.5.2 | OpenRouter, no provider pin | 16 / 20 |
| Qwen3.8 2.4T-A95B | Qwen (Alibaba) | Qwen Code 0.27.1 | OpenRouter, one pinned provider (SiliconFlow, FP8) | 0 / 20 |
| Ripple-65B Preview | Ricursive AI | OpenCode 1.19.5 | Self-hosted (SGLang 0.5.19, BF16) | 0 / 15 |

### Results by model

| Model | Harness | Designs finished | Fmax gain (geomean) | Designs improved | Mean evaluations | Candidates not proven |
|---|---|---:|---:|---:|---:|---:|
| Kimi K3.1 Pro | Kimi Code | 16 / 20 | +3.72% | 13 / 16 | 6.4 | 56% (58 / 103) |

Fmax gain is the geometric mean of each finished session's Fmax ratio (baseline period / best accepted period) over the designs that model has finished. Models have finished different designs, so this order is provisional, not a like-for-like ranking, until every model covers the same designs. "Candidates not proven" is the share of evaluations whose equivalence proof did not pass.

### Best result by design

| Design | Baseline period (ns) | Sessions finished | Best period (ns) | Fmax gain | Best by |
|---|---:|---:|---:|---:|---|
| `cheshire.default` | 1.047 | 1 | 0.973 | +7.61% | Kimi K3.1 Pro |
| `cv32e40p.default` | 0.657 | 1 | 0.630 | +4.29% | Kimi K3.1 Pro |
| `cva6.default` | 1.038 | 1 | 1.002 | +3.59% | Kimi K3.1 Pro |
| `cvfpu.fp32_fma` | 1.401 | 1 | 1.367 | +2.49% | Kimi K3.1 Pro |
| `cvfpu.full` | 2.114 | 1 | 2.085 | +1.39% | Kimi K3.1 Pro |
| `ibex.full` | 0.935 | 1 | 0.899 | +4.00% | Kimi K3.1 Pro |
| `ibex.minimal` | 0.716 | 1 | 0.703 | +1.85% | Kimi K3.1 Pro |
| `nvdla.top` | 0.789 | 1 | 0.789 | +0.00% | no improvement yet |
| `opope.default` | 0.857 | 1 | 0.857 | +0.00% | no improvement yet |
| `serial_link.default` | 0.305 | 1 | 0.269 | +13.38% | Kimi K3.1 Pro |
| `spi_host.default` | 0.475 | 1 | 0.437 | +8.70% | Kimi K3.1 Pro |
| `snitch_cluster.minimal` | 1.288 | 1 | 1.201 | +7.24% | Kimi K3.1 Pro |
| `ita.default` | 0.903 | 1 | 0.900 | +0.33% | Kimi K3.1 Pro |
| `mempool.minpool` | 2.869 | 1 | 2.869 | +0.00% | no improvement yet |
| `ara.default` | 1.064 | 1 | 1.049 | +1.43% | Kimi K3.1 Pro |
| `pulp_c910.default` | 1.005 | 1 | 0.964 | +4.25% | Kimi K3.1 Pro |
| `spatz.default` | 2.266 | 0 | — | — | — |
| `snitch_cluster.default` | 2.128 | 0 | — | — | — |
| `redmule.default` | 1.636 | 0 | — | — | — |
| `snitch_cluster.default_latch` | 2.169 | 0 | — | — | — |

### Early observations

Counts over every finished session of the models above. They describe what happened; with one session per model and design they do not establish causes or rankings.

- 103 candidates evaluated: 20 accepted, 25 proven equivalent but not faster than the session's best, 58 not proven (50 with a partition EQY could not prove, 2 at the proof deadline, 6 over the proof memory budget), 0 failed to compile or measure.
- Of 16 finished sessions, 16 ended with the agent finishing on its own.
- Sessions used 6.4 of the 10 allowed evaluations on average; 3 used all 10.
- Largest single gain so far: `serial_link.default` by Kimi K3.1 Pro, 0.305 ns to 0.269 ns (+13.38% Fmax).
- No finished session has improved `nvdla.top`, `opope.default`, `mempool.minpool` yet.
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
