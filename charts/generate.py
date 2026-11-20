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
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import FancyBboxPatch
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
MONO = 'DejaVu Sans Mono'
TRACK = '#eceef1'
# Leaderboard geometry in inches: rows of BOARD_ROW under a BOARD_TOP header.
BOARD_WIDTH, BOARD_TOP, BOARD_ROW, BOARD_MARGIN = 10.5, 2.0, 1.0, .45
BOARD_RANK_X, BOARD_LOGO_X, BOARD_NAME_X = BOARD_MARGIN, 1.05, 1.5
# Each developer's name on the board, bar color and logo (charts/logos; a monogram when there is none).
MAKERS = {
    'Anthropic': ('Anthropic', '#d97757', 'anthropic.png'),
    'OpenAI': ('OpenAI', '#10a37f', 'openai.png'),
    'Google': ('Google', '#e3a600', 'google.png'),
    'xAI': ('xAI', INK, 'xai.png'),
    'Meta': ('Meta', '#0866ff', 'meta.png'),
    'Moonshot AI': ('Moonshot AI', '#1783ff', 'moonshot-ai.png'),
    'Qwen (Alibaba)': ('Alibaba', '#615ced', 'qwen.png'),
    'NVIDIA': ('NVIDIA', '#76b900', 'nvidia.png'),
    'Ricursive AI': ('Ricursive AI', '#c39a4a', 'ricursive-ai.png'),
}


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
    """A leaderboard: one row per model with its maker's logo and color, its normalized score and Fmax gain, and a
    bar for the normalized score, each over the designs the model has finished."""
    order, aggregates, planned = data['order'], data['summary']['models'], data['summary']['planned_designs']
    height = BOARD_TOP+BOARD_ROW*len(order)+1.3
    fig = plt.figure(figsize=(BOARD_WIDTH, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, BOARD_WIDTH)
    ax.set_ylim(height, 0)
    ax.axis('off')
    board_heading(ax, BOARD_TOP-.3)
    for rank, model in enumerate(order, 1):
        board_row(ax, data, model, rank, BOARD_TOP+BOARD_ROW*(rank-1), aggregates.get(model),
                  len(planned.get(model, [])))
    header(fig, 'RTL Fmax gain by coding agent (preliminary)',
           'Normalized score: share of the best gain any model reached on each design, averaged over its designs')
    provenance(fig, data)
    return fig


def board_heading(ax, y):
    for x, text, align in ((BOARD_RANK_X, '#', 'left'), (BOARD_NAME_X, 'MODEL', 'left'),
                           (BOARD_WIDTH-BOARD_MARGIN, 'NORMALIZED SCORE', 'right')):
        ax.text(x, y, text, ha=align, va='center', fontsize=8.5, color=FAINT, family=MONO)
    hairline(ax, y+.22)


def board_row(ax, data, model, rank, top, info, planned_designs):
    """Rank, logo, name, maker and harness, score and gain, then the score bar on a rounded track."""
    maker = MAKERS.get(data['models'][model]['developer'], (data['models'][model]['developer'], FAINT, None))
    middle = top+.34
    ax.text(BOARD_RANK_X, middle, str(rank), va='center', fontsize=12, color=FAINT, family=MONO)
    place_logo(ax, maker, middle)
    ax.text(BOARD_NAME_X, middle-.12, data['models'][model]['name'], va='center', fontsize=14, color=INK)
    ax.text(BOARD_NAME_X, middle+.16, f"{maker[0]} · {data['models'][model]['harness']}".upper(), va='center',
            fontsize=8.5, color=FAINT, family=MONO)
    right = BOARD_WIDTH-BOARD_MARGIN
    if info is None:
        score, detail = NOT_FINISHED, f'0 of {planned_designs} designs finished'
    else:
        score = f"{info['normalized_score'] or 0:.0f}"
        coverage = '' if info['designs'] == planned_designs else f" · {info['designs']}/{planned_designs} designs"
        detail = f"+{info['geomean_fmax_gain_pct']:.1f}% Fmax{coverage}"
    ax.text(right, middle-.12, score, ha='right', va='center', fontsize=16, color=INK, family=MONO)
    ax.text(right, middle+.16, detail, ha='right', va='center', fontsize=9, color=FAINT, family=MONO)
    track_y, track_height = top+.66, .11
    rounded_bar(ax, BOARD_LOGO_X-.17, track_y, right-(BOARD_LOGO_X-.17), track_height, TRACK)
    if info is not None and (info['normalized_score'] or 0) > 0:
        rounded_bar(ax, BOARD_LOGO_X-.17, track_y, (right-(BOARD_LOGO_X-.17))*info['normalized_score']/100,
                    track_height, maker[1])
    hairline(ax, top+BOARD_ROW-.02)


def place_logo(ax, maker, y):
    if maker[2] is None:
        ax.text(BOARD_LOGO_X, y, maker[0][0], ha='center', va='center', fontsize=11, color=maker[1], fontweight='bold')
        return
    image = plt.imread(HERE/'logos'/maker[2])
    ax.add_artist(AnnotationBbox(OffsetImage(image, zoom=.2), (BOARD_LOGO_X, y), frameon=False))


def rounded_bar(ax, x, y, width, height, color):
    width = max(width, height)  # a sliver still shows as a dot
    ax.add_patch(FancyBboxPatch((x, y), width, height, boxstyle=f'round,pad=0,rounding_size={height/2}',
                                linewidth=0, facecolor=color))


def hairline(ax, y):
    ax.plot([BOARD_MARGIN-.15, BOARD_WIDTH-BOARD_MARGIN+.15], [y, y], color=HAIRLINE, linewidth=1)


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
