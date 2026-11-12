# Benchmark designs

Twenty designs from public open-source RTL, most of them from the
[PULP platform](https://pulp-platform.org/) of ETH Zurich and the University of Bologna. Each design is
one SystemVerilog file (`sources.sv`) with a fixed timing constraint file and a fixed top module, usually
a synthesis wrapper around the project's own top. The agent may change only `sources.sv`.

## Origin

| Design | Project (public RTL) | What it is |
|---|---|---|
| `cvfpu.fp32_fma` | CVFPU (FPnew), OpenHW Group / ETH Zurich | Floating-point unit, FP32 fused multiply-add configuration |
| `cvfpu.full` | CVFPU (FPnew), OpenHW Group / ETH Zurich | Floating-point unit, full configuration |
| `serial_link.default` | PULP Serial Link, ETH Zurich | Chip-to-chip serial link |
| `ibex.full` | Ibex, lowRISC | RISC-V core, full configuration |
| `ibex.minimal` | Ibex, lowRISC | RISC-V core, minimal configuration |
| `opope.default` | PULP, ETH Zurich | Floating-point dot-product and accumulation engine |
| `nvdla.top` | NVDLA, NVIDIA | Deep-learning accelerator, top level |
| `cheshire.default` | Cheshire, ETH Zurich | RISC-V SoC built around CVA6 |
| `cv32e40p.default` | CV32E40P, OpenHW Group | RISC-V microcontroller-class core |
| `spi_host.default` | OpenTitan SPI host, lowRISC | SPI host controller |
| `snitch_cluster.minimal` | Snitch cluster, ETH Zurich | Compute cluster, minimal configuration |
| `snitch_cluster.default` | Snitch cluster, ETH Zurich | Compute cluster, default configuration |
| `snitch_cluster.default_latch` | Snitch cluster, ETH Zurich | Default configuration with latch-based storage |
| `ita.default` | ITA, ETH Zurich | Integer transformer accelerator |
| `mempool.minpool` | MemPool, ETH Zurich | Many-core cluster, MinPool configuration |
| `pulp_c910.default` | PULP platform version of the XuanTie C910 (T-Head) | Out-of-order RISC-V core |
| `cva6.default` | CVA6, OpenHW Group | Application-class RISC-V core |
| `ara.default` | Ara, ETH Zurich | RISC-V vector processor |
| `spatz.default` | Spatz, ETH Zurich | Vector compute cluster |
| `redmule.default` | RedMulE, ETH Zurich | Matrix-multiplication engine |

## Baselines and budgets

The baseline is the original RTL measured by the evaluator: boson synthesis and unplaced setup timing on
the public ASAP7 TT libraries, with a 1 ps period search. "Passing period" is the shortest clock period
whose setup WNS meets the design's rule. Cell counts and area are boson's figures for the baseline netlist;
area is reported, not optimized. "Measurement" is the time one evaluation of the original RTL took, as
stated to the agent in `TASK.md`. "Proof deadline" is the fixed wall-clock limit of a candidate's
equivalence proof (no deadline is stated in `TASK.md` for the three designs marked "—").

| Design | Top module | Baseline passing period (ns) | Cells | Sequential cells | Area (µm²) | Passing rule | Measurement (min) | Proof deadline (min) | Session budget (min) |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| `cvfpu.fp32_fma` | `cvfpu_fp32_fma_synth` | 1.401 | 5,891 | 0 | 548 | WNS ≥ 1 ps | 1 | — | 90 |
| `cvfpu.full` | `cvfpu_full_synth` | 2.114 | 162,557 | 5,947 | 15,895 | WNS ≥ 1 ps | 2 | 20 | 90 |
| `serial_link.default` | `serial_link_synth` | 0.305 | 6,182 | 2,311 | 1,158 | WNS ≥ 1 ps | 1 | 20 | 90 |
| `ibex.full` | `ibex_full_synth` | 0.935 | 210,865 | 64,684 | 32,090 | WNS ≥ 1 ps | 2 | 20 | 90 |
| `ibex.minimal` | `ibex_minimal_synth` | 0.716 | 12,068 | 2,013 | 1,584 | WNS ≥ 1 ps | 1 | — | 90 |
| `opope.default` | `opope_wrap` | 0.857 | 403,950 | 45,797 | 47,463 | WNS ≥ 1 ps | 4 | 20 | 90 |
| `nvdla.top` | `NV_nvdla` | 0.789 | 589,788 | 147,514 | 83,884 | WNS ≥ 1 ps | 5 | 20 | 90 |
| `cheshire.default` | `cheshire_synth` | 1.047 | 401,234 | 89,742 | 59,862 | WNS ≥ 1 ps | 5 | 20 | 90 |
| `cv32e40p.default` | `cv32e40p_core` | 0.657 | 16,721 | 2,211 | 2,129 | WNS ≥ 1 ps | 1 | 20 | 90 |
| `spi_host.default` | `spi_host_synth` | 0.475 | 13,752 | 5,435 | 2,267 | WNS ≥ 1 ps | 1 | — | 90 |
| `snitch_cluster.minimal` | `snitch_cluster_wrapper` | 1.288 | 585,195 | 210,305 | 101,876 | WNS ≥ 1 ps | 8 | 35 | 115 |
| `snitch_cluster.default` | `snitch_cluster_default_synth` | 2.128 | 1,797,484 | 255,106 | 233,253 | WNS ≥ 1 ps | 46 | 189 | 490 |
| `snitch_cluster.default_latch` | `snitch_cluster_default_synth` | 2.169 | 1,815,613 | 255,726 | 229,176 | WNS ≥ 0 | 60 | 207 | 600 |
| `ita.default` | `ita` | 0.903 | 463,043 | 43,871 | 55,141 | WNS ≥ 0 | 16 | 50 | 190 |
| `mempool.minpool` | `mempool_system` | 2.869 | 683,590 | 151,626 | 99,678 | WNS ≥ 0 | 17 | 48 | 205 |
| `pulp_c910.default` | `pulp_c910_synth` | 1.005 | 664,511 | 93,426 | 87,402 | WNS ≥ 1 ps | 18 | 55 | 215 |
| `cva6.default` | `cva6` | 1.038 | 178,360 | 23,858 | 23,269 | WNS ≥ 1 ps | 5 | 51 | 90 |
| `ara.default` | `ara_synth` | 1.064 | 728,007 | 63,093 | 81,603 | WNS ≥ 1 ps | 18 | 33 | 210 |
| `spatz.default` | `spatz_cluster_wrapper` | 2.266 | 1,257,667 | 139,684 | 143,502 | WNS ≥ 0 | 42 | 96 | 450 |
| `redmule.default` | `redmule_synth` | 1.636 | 4,357,056 | 630,877 | 569,087 | WNS ≥ 1 ps | 50 | 28 | 530 |

### Measurement-time classes

| Class | One measurement | Session budget | Designs |
|---|---|---|---|
| Short | 1–5 min | 90 min | `cvfpu.*`, `serial_link`, `ibex.*`, `opope`, `nvdla`, `cheshire`, `cv32e40p`, `spi_host`, `cva6` |
| Medium | 8–18 min | 115–215 min | `snitch_cluster.minimal`, `ita`, `mempool.minpool`, `pulp_c910`, `ara` |
| Long | 42–60 min | 450–600 min | `snitch_cluster.default`, `snitch_cluster.default_latch`, `spatz`, `redmule` |

The budget is 90 minutes, or 30 minutes plus ten times one baseline measurement where that is longer,
capped at 600 minutes. It is elapsed time and includes waiting for measurements.

## Notes

- **Passing rule.** Most designs pass at setup WNS ≥ 1 ps. The four designs with latch-based timing
  (`ita`, `mempool.minpool`, `snitch_cluster.default_latch`, `spatz`) pass at WNS ≥ 0.
- **Ara and CVA6 use a weaker negative control.** Their equivalence check runs on a naming-only variant of
  the proof setup: it changes only how design names are matched, and the acceptance rule is unchanged.
  On these two designs, a deliberately broken copy of the design was not proven equivalent before the proof
  deadline, so it would not be accepted, but the checker did not produce a counterexample. On every other
  design the checker rejects the broken copy with a counterexample.
- **Out of scope.** Full MemPool, TeraPool and Occamy are not in the benchmark: a single measurement of
  each takes several hours, which no session budget could hold ten times.
- **Coverage.** All five models are scheduled on all 20 designs. Ripple’s first 15 designs used self-hosted
  serving; `ara`, `snitch_cluster.default`, `snitch_cluster.default_latch`, `spatz` and `redmule` use the
  pinned PrimeIntellect BF16 endpoint through OpenRouter.
