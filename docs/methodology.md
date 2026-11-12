# Methodology

This benchmark measures how far a stock coding agent can raise the maximum clock frequency (Fmax) of real
RTL while keeping it formally equivalent to the original. Each model runs in its own family's official
coding CLI, or in OpenCode where the family has none, with the CLI's own system prompt, tools and context
management. The agent can synthesize and time its RTL with boson, Partcl's GPU-accelerated EDA tool for
synthesis and static timing, the same tool and settings the evaluator scores with.

A result belongs to a complete agent configuration: model, harness and harness version, access route and
the settings below. It does not separate model capability from the harness.

## Sessions and evaluations

- A **session** is one continuous run of one agent on one design, starting from the original RTL. There is
  one session per model and design, with a fresh workspace and a fresh home directory; nothing carries over
  between sessions.
- The agent receives the prompt below once, plus a workspace holding `TASK.md`, the original
  `sources.sv`, the design's timing constraints, baseline scalar metrics (`baseline-metrics.json`), the
  baseline's critical-path source locations (`baseline-hotspots.json`), `measure.tcl` and the `./evaluate`
  client. It receives no other model's results and no earlier optimized RTL.
- An **evaluation** is one call to `./evaluate`. It snapshots `sources.sv`, synthesizes and times it, runs
  a formal equivalence proof against the original RTL, and returns the passing period and the proof status.
  There is no separate notion of a "turn": between evaluations the agent works freely, with no cap on file
  reads, edits, shell commands or its own boson runs. A session has at most **ten evaluations**; candidates
  that fail to compile or fail the proof count. `./evaluate --status` and `./evaluate --restore-best` are free.
- A candidate is **accepted** when its equivalence proof passes and its passing period is strictly shorter
  than the session's best so far. The session's score is its best accepted period:
  **Fmax ratio = baseline period / best accepted period**. A session with no accepted candidate scores 1.0.
- The session ends when the agent stops, or at its elapsed-time **budget**: 90 minutes, or 30 minutes plus
  ten times one baseline measurement where that is longer, capped at 600 minutes (see
  [benchmarks.md](benchmarks.md)). The budget includes measurement waits. An evaluation already submitted
  at the limit finishes and counts.
- The session's CPUs, memory and GPU slice are reserved before its clock starts, so queueing for compute
  never uses a session's budget.

Evaluation statuses in `results/evaluations.csv`:

| Status | Meaning |
|---|---|
| `accepted` | Proven equivalent and faster than the session's best so far |
| `no_improvement` | Proven equivalent, not faster than the session's best |
| `unverified` | Timed, but the equivalence proof did not pass (counterexample, proof deadline or proof memory budget) |
| `evaluation_failed` | Did not compile, or could not be measured within the measurement's fixed memory budget |

## Measurement

- **Timing.** boson synthesizes `sources.sv` with the design's fixed constraints on the public ASAP7 TT
  Liberty libraries and searches for the shortest passing clock period at 1 ps resolution. The result is an
  unplaced setup-timing estimate, not sign-off timing or measured silicon. A period passes when setup WNS is
  at least 1 ps, or at least 0 for the four designs with latch-based timing. Area is recorded, not optimized.
- **Equivalence.** The evaluator proves the candidate `sources.sv` equivalent to the original with EQY
  (YosysHQ's equivalence-checking flow), within a fixed deadline and memory budget per design. A proof that
  finds a difference, reaches its deadline or exceeds its memory budget does not pass. "Not proven" is not
  proof that a candidate is wrong: EQY can also report differences that only occur from unreachable states.
- **GPU classes.** Sessions run on a slice of an NVIDIA H200 NVL or RTX 6000 Ada GPU; `sessions.csv`
  records which. boson's netlist for the same RTL can differ between the two classes, so each session runs
  entirely on one class, and a design runs on a class only after a control there reproduced the design's
  stored baseline exactly.

## Agent environment

- **Tools.** The sandbox exposes exactly three EDA tools: boson, Verilator and EQY. EQY runs Yosys and
  SAT/SMT solvers internally; they are not separately on the agent's path, and no other EDA tool is
  reachable. boson in the sandbox is the evaluator's binary with the same ASAP7 TT libraries and constraints,
  and runs with two threads, as in the evaluator.
- **The exact recipe.** Every workspace has `measure.tcl`, the evaluator's exact synthesis and Fmax
  period-search script with paths pointing into the sandbox. `boson -f measure.tcl` on the original
  `sources.sv` prints the same passing period as the evaluator; the controls check this for every design.
  Local measurements never record a result: only `./evaluate` does.
- **Shared allocation.** The agent's sandbox shares the session's CPUs, memory and GPU slice with the
  evaluator's measurements. One boson run happens at a time in a session: the agent's runs and
  `./evaluate`'s measurements take turns, and boson prints a notice while it waits.
- **Memory.** The agent's sandbox has a fixed memory size on top of the measurement's own: 8 GiB on the
  smaller designs (`cvfpu.*`, `serial_link`, `cv32e40p`, `ibex.*`, `spi_host`, `snitch_cluster.minimal`,
  `cva6`) and 12 GiB on the others. A session that reaches this ceiling stands; that is the protocol's limit
  for every agent.
- **Isolation.** The agent sees its workspace, a fresh home directory holding only the harness's model
  configuration, the harness runtime and the three tools. Temporary files use private disk-backed storage.
  The harness runs headless in its documented non-interactive mode with all permissions granted inside the
  sandbox, without user settings, plugins or MCP servers.

## Prompt

The CLI's own system prompt is unchanged. Every agent receives this user prompt once, with the design's top
module in place of `{top}`:

> Optimize the RTL in sources.sv for the highest verified Fmax of top {top}. Preserve all functionality, the top interface, parameter defaults, reset and clock behavior, latency, and handshakes. Only changes in sources.sv are submitted for evaluation; you may use other workspace files for ordinary analysis.
>
> Read TASK.md for the fixed measurement rules and the available tools. Use boson for synthesis and timing (`boson -f measure.tcl` measures sources.sv exactly as ./evaluate does), Verilator for simulation and EQY for equivalence checks, together with your normal file and shell tools. Run ./evaluate after preparing each candidate. You have up to ten candidate evaluations in this continuous session. Develop and evaluate improvements, retain the best formally verified result, and finish with a concise account of the changes and evaluation outcomes.

## TASK.md

Verbatim, with the per-design values in braces: `{top}`, `{measurement_minutes}`, `{baseline_period_ns}`
and `{budget_minutes}` come from [benchmarks.md](benchmarks.md); `{passing_rule}` is "passing setup WNS
threshold of 1 ps" or, for the latch-timed designs, "non-negative setup WNS"; `{proof_deadline}` is
" Formal equivalence of a changed candidate has a fixed N-minute deadline." where a deadline is stated, and
empty otherwise.

```markdown
# RTL Fmax optimization

Optimize sources.sv for Fmax while preserving behavior. The top is {top}. All models begin with the same original RTL and the same context files. No previous optimized candidates are supplied.

Use your normal coding-agent tools. There is no required response format or cap on ordinary inspection/edit/shell calls. Only sources.sv is scored; constraints, libraries, compiler and formal settings are fixed outside the workspace. Preserve the top interface, parameter defaults, functionality, reset/clock behavior, latency and handshakes. Do not alter the evaluation client or try to access the evaluator implementation.

## Measurement

- Run `./evaluate` to snapshot the current sources.sv and request compilation, timing measurement and formal equivalence to the original RTL. It waits for the measurement and returns the result. One measurement of the original RTL took about {measurement_minutes} minutes.{proof_deadline}
- You have at most ten candidate evaluations, including candidates that fail compilation or equivalence. Ordinary file/shell exploration, `./evaluate --status`, and `./evaluate --restore-best` do not consume that budget.
- Acceptance requires proven equivalence and a strictly shorter passing clock period than the current best. A formal failure or timeout does not pass. Non-improving and unverified candidates do not replace the best result.
- The baseline passing period is {baseline_period_ns} ns. Fmax ratio equals baseline period / candidate period; greater is better. Timing is an unplaced setup estimate using fixed public ASAP7 TT libraries, a 1 ps period-search resolution and a {passing_rule}. Area is recorded separately and is not the objective.
- Returned metrics and proof status are external measurement feedback. A candidate may compile and improve timing yet fail formal equivalence. Use feedback to decide subsequent edits.
- Baseline scalar metrics are in baseline-metrics.json. Baseline RTL source locations associated with critical-path delay are in baseline-hotspots.json; these are hints, not a substitute for understanding the source. Line numbers refer to the original source.
- When done, run `./evaluate --restore-best` to leave the best verified source in place. Report changes, evaluation outcomes, and any limitations. Stop if an infrastructure error pauses the session; that is not a model-quality failure.

## Session budget

One continuous stock-agent session, at most ten candidate evaluations, and a {budget_minutes}-minute elapsed-time limit including measurement waits. The service drains an evaluation already submitted at the limit. An unfinished or infrastructure-interrupted session is reported as incomplete.

## Available tools

Only these EDA tools are installed; they are on PATH:

- `boson`: synthesis and static timing, the same binary, ASAP7 TT libraries and constraints as ./evaluate, on this session's GPU slice. Your boson runs and ./evaluate's measurements take turns: whichever starts second waits for the first, and boson prints a notice while it waits. `boson -f measure.tcl` synthesizes the current sources.sv and runs the same 1 ps Fmax period search as ./evaluate; it prints `@@FMAX period_ps=<passing period>` and writes timing reports to /tmp/measure. A run takes about as long as one measurement of the original RTL. You may write your own boson Tcl scripts; measure.tcl shows the commands.
- `verilator`: linting and simulation.
- `eqy`: equivalence checking (EQY runs Yosys and SAT/SMT solvers internally; they are not separately on PATH).

Temporary files use private disk-backed storage. Local measurements do not replace ./evaluate: only ./evaluate records a candidate, and only its formal proof can accept it.
```

## Models and harnesses

| Model | Developer | Harness and version | Access | Model identifier |
|---|---|---|---|---|
| Claude Fable 5.2 | Anthropic | Claude Code 2.1.322 | Official CLI signed in to a subscription | `claude-fable-5-2` |
| GPT-6 Astra | OpenAI | Codex 0.154.0 | Official CLI signed in to a subscription | `gpt-6-astra` |
| Kimi K3.1 Pro | Moonshot AI | Kimi Code 2.5.2 | OpenRouter, pinned to Moonshot AI's own endpoint (MXFP4), fallbacks disabled | `moonshotai/kimi-k3.1-pro` |
| Qwen3.8 2.4T-A95B | Qwen (Alibaba) | Qwen Code 0.27.1 | OpenRouter, one pinned provider (SiliconFlow, FP8), fallbacks disabled | `qwen/qwen3.8-2.4t-a95b` |
| Ripple-65B Preview | Ricursive AI | OpenCode 1.19.5 | Self-hosted SGLang 0.5.19 with the BF16 weights for its first 15 designs; OpenRouter pinned to PrimeIntellect (BF16) for later sessions | `ricursiveai/ripple-65b-preview` |

Headless launch modes: Claude Code `--print --permission-mode bypassPermissions` with no setting sources
and no MCP configuration; Codex `exec --sandbox danger-full-access` with approvals off and user config
ignored; Kimi Code `--prompt`; Qwen Code `--approval-mode yolo`; OpenCode `run --auto`.

## Controls

Before any model session on a design:

1. Two fresh measurements of the original RTL reproduce the stored baseline exactly (metrics and netlist).
2. The equivalence check proves the unchanged design and rejects a deliberately broken copy (on Ara and
   CVA6 the broken copy is only left unproven at the deadline; see [benchmarks.md](benchmarks.md)).
3. For each GPU class the design runs on, a model-free control session evaluates the original RTL once
   through the complete session setup. It must return "no improvement, proven" at exactly the stored
   baseline period, and `boson -f measure.tcl` inside the sandbox must print the same period. Model sessions
   on that design and GPU class start only after this control passes.

The sandbox itself was verified on both GPU classes before the first session: only boson, Verilator and
EQY are reachable (Yosys, Icarus Verilog, OpenSTA, OpenROAD, standalone solvers and other EDA tools are
not); EQY proves a design
against itself and rejects `a - b` against `a + b`; boson in the sandbox reproduces the baseline period and
netlist of four small designs exactly; and the agent's boson runs and the evaluator's measurements take
turns as described.

## Reruns

A session spoiled by something other than the model is not a model result. It is rerun from scratch, with
a fresh workspace and home and the fault fixed. The tables report the latest valid completed attempt. Provider-refused or infrastructure-interrupted attempts,
and attempts with a replacement still pending, do not enter the tables or aggregates. Their design, model and
reason are listed in `summary.json` under `incomplete_attempts`; raw attempts remain in the campaign archive.
For completed replacements, `sessions.csv`
records the number of attempts, the earlier attempts' outcomes and the reason. The reasons are:

- an infrastructure fault, such as an under-sized allocation or a compute node lost mid-session;
- the model provider refusing service (credit or concurrency limits, peak-load refusals, subscription usage
  limits), up to three attempts in all;
- a sandbox gap: the agent could reach a tool outside the protocol's tool set;
- an agent sandbox smaller than the protocol's memory size;
- a benchmark artifact: every harness receives the prompt on its command line, and the prompt names
  `boson -f measure.tcl`, so an agent stopping its own background measurement with `pkill -f` on that
  text also stops its own harness. The agent could not have expected that, so such a session is rerun.

An agent that crashes, stops early or runs out of budget on its own keeps its result. Once, when the shared
disk was nearly full, two runaway equivalence-check logs (27 GB and 41 GB) that one running agent had written
were cut to their first 256 KB and last 4 MB; nothing else in a running agent's files is ever modified. If a rerun is
submitted twice by mistake, the first-submitted attempt counts and the duplicate is excluded.

## Evaluator version

All sessions so far ran evaluator version `next-09` (the `evaluator` column of `sessions.csv`). A session
runs start to finish on the version it started with; a later version will be listed here with what it
changes.

## Result files

- `results/sessions.csv`: one row per model and design, the latest attempt. Columns: `design`, `model`,
  `attempts`, `earlier_outcomes`, `rerun_reason`, `harness`, `evaluator`, `gpu`, `budget_minutes`,
  `outcome` (`agent_finished`, `budget_reached` when the session used at least 95% of its budget,
  `agent_error`, `infrastructure_error`), `agent_exit_code`, `elapsed_minutes`, `evaluations`, `accepted`,
  `unverified`, `compile_or_score_failed`, `baseline_period_ns`, `best_period_ns`, `fmax_ratio`.
- `results/evaluations.csv`: one row per evaluation. Columns: `design`, `model`, `evaluation` (1–10),
  `status`, `period_ns`, `fmax_ratio`, `proof_status` (`proven`, `unverified`, `memory_limit`, `not_run`),
  `proof_failure` (`partition_proof_failed` when EQY could not prove a partition, `timeout`, or empty).
- `results/summary.json`: per-model aggregates over the designs each model finished (geometric-mean Fmax
  gain, designs improved, mean evaluations, outcomes), each design's baseline period, and each model's
  planned designs. `ranked` is true when a model has finished every design that any model has finished.
- `results/models.json`: model, developer, harness, version and access route, as in the table above.

## Limitations

- **Preliminary.** Results are added as sessions finish. Until every model has finished the same designs,
  the models are measured on different design sets and their order is provisional.
- **One session per model and design.** There are no repeats, so there are no confidence intervals, and a
  single session's luck can move a model's aggregate.
- **The harness is part of the result.** An agent that stops early, or whose provider returns malformed
  tool calls, scores what it reached. Access routes differ (subscription CLI, OpenRouter, self-hosted), and
  Kimi Code has no setting for OpenRouter's provider-routing field, so its requests go through a local
  forwarding proxy that adds the pin and changes nothing else. Kimi's first sessions ran unpinned; they were
  rerun pinned and only the pinned runs are reported.
- **The evaluation cap limits scored candidates, not feedback.** Agents may run boson locally as often as
  their time allows; local runs share the session's GPU slice and budget with `./evaluate`.
- **Timing is an estimate.** Unplaced setup timing on ASAP7 TT libraries; no placement, routing, hold or
  sign-off corners.
- **Ripple serving differs by design.** Its first 15 designs used self-hosted SGLang; its five remaining
  designs use the pinned PrimeIntellect BF16 endpoint. Both use Ripple-65B Preview, but serving differences
  may affect behavior. All five models are scheduled on all 20 designs.
