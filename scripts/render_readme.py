"""Render the README's results section from results/ between the results markers.

Usage: python3 scripts/render_readme.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT/'results'
README = ROOT/'README.md'
START, END = '<!-- results:start -->', '<!-- results:end -->'
MAX_EVALUATIONS = 10
OUTCOME_PHRASES = {'agent_finished': 'ended with the agent finishing on its own', 'budget_reached': 'ran to the time budget',
                   'agent_error': 'ended with an agent error', 'infrastructure_error': 'ended with an infrastructure error'}


def main():
    results = load_results()
    section = '\n\n'.join([status_line(results), coverage_table(results), model_table(results),
                           design_table(results), observations(results)])
    print('README updated' if replace_section(section) else 'README unchanged')


def load_results():
    summary = json.loads((RESULTS/'summary.json').read_text())
    models = json.loads((RESULTS/'models.json').read_text())['models']
    return dict(summary=summary, models=models,
                names={m['id']: m['name'] for m in models},
                sessions=read_csv(RESULTS/'sessions.csv'), evaluations=read_csv(RESULTS/'evaluations.csv'))


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def replace_section(section):
    """Swap the text between the markers; return whether the README changed."""
    text = README.read_text()
    if text.count(START) != 1 or text.count(END) != 1:
        raise RuntimeError('README needs exactly one results start and end marker')
    before, rest = text.split(START)
    after = rest.split(END)[1]
    updated = f'{before}{START}\n{section}\n{END}{after}'
    if updated == text:
        return False
    README.write_text(updated)
    return True


def status_line(results):
    return (f"**Status:** {len(results['sessions'])} of {planned_sessions(results)} sessions finished "
            f"({len(results['models'])} models, {len(results['summary']['benchmark'])} designs), "
            f"as of {results['summary']['generated']}."
            + (f" {len(results['summary'].get('incomplete_attempts', []))} interrupted attempts are excluded "
               "from these results while awaiting a valid replacement."
               if results['summary'].get('incomplete_attempts') else ""))


def planned_sessions(results):
    return sum(len(designs) for designs in results['summary']['planned_designs'].values())


def coverage_table(results):
    rows = ['### Coverage', '', '| Model | Developer | Harness | Access | Sessions finished |', '|---|---|---|---|---:|']
    finished = sessions_by_model(results)
    for model in results['models']:
        planned = len(results['summary']['planned_designs'].get(model['id'], []))
        rows.append(f"| {model['name']} | {model['developer']} | {model['harness']} {model['harness_version']} | "
                    f"{model['access']} | {len(finished.get(model['id'], []))} / {planned} |")
    return '\n'.join(rows)


def sessions_by_model(results):
    grouped = {}
    for session in results['sessions']:
        grouped.setdefault(session['model'], []).append(session)
    return grouped


def model_table(results):
    rows = ['### Results by model', '']
    aggregates = results['summary']['models']
    if not aggregates:
        return '\n'.join(rows+['No session has finished yet.'])
    rows += ['| Model | Harness | Designs finished | Fmax gain (geomean) | Normalized score | Designs improved | '
             'Mean evaluations | Candidates not proven |', '|---|---|---:|---:|---:|---:|---:|---:|']
    harness = {m['id']: m['harness'] for m in results['models']}
    planned = results['summary']['planned_designs']
    sessions = sessions_by_model(results)
    for model in sorted(aggregates, key=lambda m: -aggregates[m]['geomean_fmax_gain_pct']):
        info = aggregates[model]
        evaluated = sum(int(s['evaluations']) for s in sessions[model])
        unproven = sum(int(s['unverified']) for s in sessions[model])
        share = f'{100*unproven/evaluated:.0f}% ({unproven} / {evaluated})' if evaluated else '—'
        rows.append(f"| {results['names'].get(model, model)} | {harness.get(model, info['harness'])} | "
                    f"{info['designs']} / {len(planned.get(model, []))} | {gain(info['geomean_fmax_gain_pct'])} | "
                    f"{score(info['normalized_score'])} | {info['designs_improved']} / {info['designs']} | {info['mean_evaluations']:.1f} | {share} |")
    rows += ['', "Fmax gain is the geometric mean of each finished session's Fmax ratio (baseline period / best "
                 f'accepted period) over the designs that model has finished. Normalized score is the mean of its '
                 'gain on each design as a percentage of the best gain any model here reached on that design (100: '
                 'the best result on every design), so every design counts equally however much headroom it had. '
                 f'{ranking_caveat(results)} '
                 '"Candidates not proven" is the share of evaluations whose equivalence proof did not pass.']
    return '\n'.join(rows)


def ranking_caveat(results):
    if all(info['ranked'] for info in results['summary']['models'].values()):
        return ('Every model has finished the same designs, so this order is a like-for-like ranking over them; '
                'with one session per model and design it has no confidence intervals.')
    return ('Models have finished different designs, so this order is provisional, not a like-for-like ranking, '
            'until every model covers the same designs.')


def score(normalized):
    return '—' if normalized is None else f'{normalized:.1f}'


def gain(percent):
    return f'+{percent:.2f}%' if percent >= 0 else f'{percent:.2f}%'


def design_table(results):
    rows = ['### Best result by design', '',
            '| Design | Baseline period (ns) | Sessions finished | Best period (ns) | Fmax gain | Best by |',
            '|---|---:|---:|---:|---:|---|']
    by_design = {}
    for session in results['sessions']:
        by_design.setdefault(session['design'], []).append(session)
    for entry in results['summary']['benchmark']:
        design, sessions = entry['design'], by_design.get(entry['design'], [])
        if not sessions:
            rows.append(f"| `{design}` | {entry['baseline_period_ns']:.3f} | 0 | — | — | — |")
            continue
        best = max(float(s['fmax_ratio']) for s in sessions)
        leaders = sorted(results['names'].get(s['model'], s['model']) for s in sessions if float(s['fmax_ratio']) == best)
        best_period = min(float(s['best_period_ns']) for s in sessions)
        rows.append(f"| `{design}` | {entry['baseline_period_ns']:.3f} | {len(sessions)} | {best_period:.3f} | "
                    f"{gain((best-1)*100)} | {', '.join(leaders) if best > 1 else 'no improvement yet'} |")
    return '\n'.join(rows)


def observations(results):
    sessions, evaluations = results['sessions'], results['evaluations']
    if not sessions:
        return ''
    lines = ['### Early observations', '',
             'Counts over every finished session of the models above. They describe what happened; with one '
             'session per model and design they do not establish causes or rankings.', '',
             '- '+candidate_counts(evaluations),
             '- '+session_endings(sessions),
             '- '+evaluation_use(sessions),
             '- '+largest_gain(results)]
    unimproved = [e['design'] for e in results['summary']['benchmark']
                  if any(s['design'] == e['design'] for s in sessions)
                  and all(float(s['fmax_ratio']) <= 1 for s in sessions if s['design'] == e['design'])]
    if unimproved:
        lines.append('- No finished session has improved '+', '.join(f'`{d}`' for d in unimproved)+' yet.')
    return '\n'.join(lines)


def candidate_counts(evaluations):
    count = lambda status: sum(e['status'] == status for e in evaluations)
    unproven = [e for e in evaluations if e['status'] == 'unverified']
    reasons = {'with a partition EQY could not prove': 0, 'at the proof deadline': 0,
               'over the proof memory budget': 0, 'for another reason': 0}
    for e in unproven:
        if e['proof_status'] == 'memory_limit':
            reasons['over the proof memory budget'] += 1
        elif e['proof_failure'] == 'timeout':
            reasons['at the proof deadline'] += 1
        elif e['proof_failure'] == 'partition_proof_failed':
            reasons['with a partition EQY could not prove'] += 1
        else:
            reasons['for another reason'] += 1
    why = ', '.join(f'{n} {reason}' for reason, n in reasons.items() if n)
    return (f"{len(evaluations)} candidates evaluated: {count('accepted')} accepted, {count('no_improvement')} "
            f"proven equivalent but not faster than the session's best, {len(unproven)} not proven"
            + (f' ({why})' if why else '') + f", {count('evaluation_failed')} failed to compile or measure.")


def session_endings(sessions):
    counts = {o: sum(s['outcome'] == o for s in sessions) for o in OUTCOME_PHRASES}
    parts = [f'{n} {OUTCOME_PHRASES[o]}' for o, n in counts.items() if n]
    listed = parts[0] if len(parts) == 1 else ', '.join(parts[:-1])+' and '+parts[-1]
    return f'Of {len(sessions)} finished sessions, {listed}.'


def evaluation_use(sessions):
    used = [int(s['evaluations']) for s in sessions]
    full = sum(n == MAX_EVALUATIONS for n in used)
    return (f'Sessions used {sum(used)/len(used):.1f} of the {MAX_EVALUATIONS} allowed evaluations on average; '
            f'{full} used all {MAX_EVALUATIONS}.')


def largest_gain(results):
    best = max(results['sessions'], key=lambda s: float(s['fmax_ratio']))
    ratio = float(best['fmax_ratio'])
    if ratio <= 1:
        return 'No finished session has an accepted improvement yet.'
    so_far = '' if len(results['sessions']) == planned_sessions(results) else ' so far'
    return (f"Largest single gain{so_far}: `{best['design']}` by {results['names'].get(best['model'], best['model'])}, "
            f"{float(best['baseline_period_ns']):.3f} ns to {float(best['best_period_ns']):.3f} ns "
            f"({gain((ratio-1)*100)} Fmax).")


if __name__ == '__main__':
    main()
