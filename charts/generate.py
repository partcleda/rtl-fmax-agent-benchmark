"""Render the preliminary-results charts from results/ into charts/ (PNG and SVG, light theme).

Usage: python3 charts/generate.py   (one CPU is enough)
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import textwrap

for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[variable] = '1'

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent/'results'
INPUTS = [RESULTS/'summary.json', RESULTS/'sessions.csv', RESULTS/'models.json']

# Partcl light tokens: ink navy, body and faint ink, steel-blue accent (the single product series), grid, chart ground.
INK, BODY, FAINT, ACCENT, GRID, GROUND = '#171738', '#5b607d', '#74788d', '#3f5680', '#ebedf0', '#ffffff'
HAIRLINE = (23/255, 23/255, 56/255, .22)
CHARACTERS_PER_INCH = 12  # 8.5 pt provenance text across 92% of the figure width
NOT_FINISHED = '–'
GAIN_COLORS = ['#f3f5f7', '#8ab6df', ACCENT, INK]


def main():
    before = {p.name: digest(p) for p in INPUTS}
    data = load()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'svg.fonttype': 'none',
                         'svg.hashsalt': 'rtl-fmax-agent-benchmark', 'axes.spines.top': False,
                         'axes.spines.right': False, 'text.color': INK, 'axes.labelcolor': BODY,
                         'xtick.color': FAINT, 'ytick.color': INK})
    outputs = save(gain_chart(data), 'model-fmax') + save(design_heatmap(data), 'design-fmax')
    if before != {p.name: digest(p) for p in INPUTS}:
        raise RuntimeError('Inputs changed during plotting')
    (HERE/'manifest.json').write_text(json.dumps(dict(
        inputs_sha256=before, generator_sha256=digest(Path(__file__)), models=data['order'],
        outputs={p.name: dict(sha256=digest(p), bytes=p.stat().st_size) for p in outputs}), indent=2)+'\n')
    print(json.dumps(dict(generated=[p.name for p in outputs], sessions=len(data['sessions']))))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    summary = json.loads(INPUTS[0].read_text())
    with INPUTS[1].open(newline='') as stream:
        sessions = {(r['model'], r['design']): r for r in csv.DictReader(stream)}
    models = json.loads(INPUTS[2].read_text())['models']
    aggregates = summary['models']
    best = {}
    for (_, design), row in sessions.items():
        best[design] = max(best.get(design, 1.0), float(row['fmax_ratio']))
    for model, info in aggregates.items():
        rows = [(design, float(r['fmax_ratio'])) for (m, design), r in sessions.items() if m == model]
        geomean = (math.exp(sum(math.log(ratio) for _, ratio in rows)/len(rows))-1)*100
        shares = [(ratio-1)/(best[design]-1)*100 for design, ratio in rows if best[design] > 1]
        normalized = sum(shares)/len(shares) if shares else None
        if (abs(geomean-info['geomean_fmax_gain_pct']) > 1e-3
                or (normalized is None) != (info['normalized_score'] is None)
                or (normalized is not None and abs(normalized-info['normalized_score']) > 1e-2)):
            raise RuntimeError('summary.json and sessions.csv disagree for '+model)
    finished = sorted((m['id'] for m in models if m['id'] in aggregates), key=lambda m: ranking_key(aggregates[m]))
    order = finished + [m['id'] for m in models if m['id'] not in aggregates]
    return dict(summary=summary, sessions=sessions, models={m['id']: m for m in models}, order=order,
                designs=[e['design'] for e in summary['benchmark']])


def ranking_key(info):
    """Highest normalized score first; Fmax gain breaks ties."""
    return -(info['normalized_score'] or 0), -info['geomean_fmax_gain_pct']


def label(data, model):
    info = data['models'][model]
    return f"{info['name']}\n{info['harness']}"


def provenance(fig, data):
    """Conditions and data date beneath the figure, wrapped to the figure's width."""
    planned = sum(len(d) for d in data['summary']['planned_designs'].values())
    text = (f"Preliminary results as of {data['summary']['generated']}: {len(data['sessions'])} of {planned} "
            'sessions finished.\n' + textwrap.fill(
                'Stock coding agents, one session per model and design, at most 10 evaluations each. boson synthesis '
                'and unplaced setup timing on public ASAP7 TT libraries, 1 ps period search; a candidate counts only '
                'with an EQY equivalence proof against the original RTL.', int(fig.get_figwidth()*CHARACTERS_PER_INCH)))
    fig.text(.04, .25/fig.get_figheight(), text, fontsize=8.5, color=BODY, linespacing=1.6)


def header(fig, title, subtitle):
    """Bold title, one-line subtitle and a hairline, placed in inches from the top edge."""
    height = fig.get_figheight()
    fig.text(.04, 1-.6/height, title, fontsize=18, fontweight='bold', color=INK)
    fig.text(.04, 1-.95/height, subtitle, fontsize=11.5, color=BODY)
    fig.add_artist(Line2D([.04, .96], [1-1.15/height]*2, color=HAIRLINE, linewidth=1))


def save(fig, stem):
    paths = []
    for extension in ('svg', 'png'):
        path = HERE/f'{stem}.{extension}'
        fig.savefig(path, dpi=150, facecolor=GROUND, metadata={'Date': None} if extension == 'svg' else None)
        paths.append(path)
    plt.close(fig)
    return paths


def gain_chart(data):
    """Two bar panels sharing the model axis: geometric-mean Fmax gain, and normalized score, each over the
    designs the model has finished."""
    order, aggregates, planned = data['order'], data['summary']['models'], data['summary']['planned_designs']
    height = 3.4+.62*len(order)
    fig, (gain_axis, score_axis) = plt.subplots(1, 2, figsize=(14, height), sharey=True,
                                                gridspec_kw=dict(width_ratios=[1.25, 1], wspace=.06))
    fig.subplots_adjust(left=.17, right=.97, top=1-1.5/height, bottom=1.85/height)
    gains = [aggregates[m]['geomean_fmax_gain_pct'] if m in aggregates else 0 for m in order]
    scores = [(aggregates[m]['normalized_score'] or 0) if m in aggregates else 0 for m in order]
    bar_panel(gain_axis, gains, 'Fmax gain, geometric mean over designs (%)', max(2.0, max(gains)*1.75))
    bar_panel(score_axis, scores, 'Normalized score (best result on each design = 100)', 128)
    score_axis.set_xticks([0, 25, 50, 75, 100])
    gain_axis.set_yticks(range(len(order)), [label(data, m) for m in order], fontsize=10.5)
    gain_axis.invert_yaxis()
    for row, model in enumerate(order):
        total = len(planned.get(model, []))
        if model not in aggregates:
            annotate(gain_axis, 0, row, f'no finished sessions yet · 0 of {total} designs', FAINT)
            continue
        info = aggregates[model]
        coverage = '' if info['designs'] == total else f" · {info['designs']} of {total} designs finished"
        annotate(gain_axis, gains[row], row, f"+{gains[row]:.2f}%   {info['designs_improved']}/{info['designs']} "
                                             f"improved{coverage}", INK)
        annotate(score_axis, scores[row], row, f'{scores[row]:.1f}', INK)
    header(fig, 'RTL Fmax gain by coding agent (preliminary)',
           'Ordered by normalized score: its gain on each design as a share of the best gain any model reached '
           'there, averaged over the designs it has finished')
    provenance(fig, data)
    return fig


def bar_panel(ax, values, xlabel, right):
    ax.barh(range(len(values)), values, color=ACCENT, alpha=.85, height=.58)
    ax.set_xlim(0, right)
    ax.set_xlabel(xlabel, labelpad=10)
    ax.set_axisbelow(True)
    ax.grid(axis='x', color=GRID)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    ax.tick_params(axis='y', length=0, pad=10)


def annotate(ax, value, row, text, color):
    ax.annotate(text, (value, row), xytext=(6, 0), textcoords='offset points', va='center', fontsize=10,
                color=color)


def design_heatmap(data):
    """Designs x models: each finished session's gain; a dash for a planned session not finished, 'n/a' if not planned."""
    order, designs, planned = data['order'], data['designs'], data['summary']['planned_designs']
    matrix = np.full((len(designs), len(order)), np.nan)
    for i, design in enumerate(designs):
        for j, model in enumerate(order):
            row = data['sessions'].get((model, design))
            if row:
                matrix[i, j] = (float(row['fmax_ratio'])-1)*100
    width = max(10.5, 1.6*len(order)+5)
    height = .42*len(designs)+4.2
    fig, ax = plt.subplots(figsize=(width, height))
    fig.subplots_adjust(left=3.3/width, right=1-1.3/width, top=1-2.1/height, bottom=1.1/height)
    cmap = LinearSegmentedColormap.from_list('gain', GAIN_COLORS)
    cmap.set_bad(GROUND)
    top = max(5.0, float(np.nanmax(matrix))) if np.isfinite(matrix).any() else 5.0
    image = ax.imshow(np.ma.masked_invalid(matrix), cmap=cmap, vmin=0, vmax=top, aspect='auto')
    ax.set_xticks(range(len(order)), [label(data, m) for m in order], fontsize=9.5)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(designs)), designs, fontsize=10)
    ax.tick_params(length=0, pad=8)
    ax.set_xticks(np.arange(len(order)+1)-.5, minor=True)
    ax.set_yticks(np.arange(len(designs)+1)-.5, minor=True)
    ax.grid(which='minor', color=GROUND, linewidth=2)
    ax.tick_params(which='minor', length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for i, design in enumerate(designs):
        for j, model in enumerate(order):
            value = matrix[i, j]
            if np.isfinite(value):
                ax.text(j, i, f'{value:.1f}', ha='center', va='center', fontsize=9,
                        color='white' if value >= top*.55 else INK)
            elif design in planned.get(model, []):
                ax.text(j, i, NOT_FINISHED, ha='center', va='center', fontsize=11, color=FAINT)
            else:
                ax.add_patch(plt.Rectangle((j-.5, i-.5), 1, 1, color=GRID, zorder=0))
                ax.text(j, i, 'n/a', ha='center', va='center', fontsize=8, color=FAINT)
    fig.colorbar(image, ax=ax, fraction=.03, pad=.02).set_label('Fmax gain (%)', fontsize=10, color=BODY)
    header(fig, 'Fmax gain by design (preliminary)',
           f"Best formally verified gain per session (%) · {NOT_FINISHED} not finished yet · n/a: design not in the "
           "model's set")
    provenance(fig, data)
    return fig


if __name__ == '__main__':
    main()
