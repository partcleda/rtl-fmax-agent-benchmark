"""Check the publication boundary across every reachable commit: exact file allowlist, no local paths, internal
host or account names, cluster commands, source-code paths, email addresses or credentials.

Usage: python3 scripts/check_publication.py
"""
from pathlib import Path
import re
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    '.gitignore', 'LICENSE', 'LICENSE-CC-BY-4.0', 'README.md',
    'docs/methodology.md', 'docs/benchmarks.md',
    'results/sessions.csv', 'results/evaluations.csv', 'results/summary.json', 'results/models.json',
    'charts/generate.py', 'charts/manifest.json',
    'charts/model-fmax.png', 'charts/model-fmax.svg', 'charts/design-fmax.png', 'charts/design-fmax.svg',
    'scripts/check_publication.py', 'scripts/render_readme.py',
}
# Patterns are assembled from fragments so that this file does not match itself.
LOCAL_PATHS = [('/' + name + '/').encode() for name in ('home', 'media', 'mnt')]
FORBIDDEN = [
    (re.compile(rb'(?i)\b(?:' + b'|'.join(name.encode() for name in ('cas' + 'tle', 'gad' + 'get', 'aws' + '2', 'aws' + '3'))
                + rb')\b'), 'internal host name'),
    (re.compile(rb'(?i)\b(?:' + b'|'.join(name.encode() for name in ('will' + '-personal', 'will' + '-org', 'c' + 'cx'))
                + rb')\b'), 'internal account or tool name'),
    (re.compile(rb'(?i)\b(?:' + b'|'.join(name.encode() for name in ('s' + 'run', 's' + 'batch', 's' + 'lurm'))
                + rb')\b'), 'cluster scheduler detail'),
    (re.compile(rb'\b[\w/-]+\.r' + rb's\b|\bcra' + rb'tes/'), 'source-code path'),
    (re.compile(rb'[A-Za-z0-9._%+-]+' + rb'@' + rb'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'), 'email address'),
    (re.compile(rb'(?:s' + rb'k-|gh' + rb'p_|github' + rb'_pat_|xox[abprs]-)[A-Za-z0-9_\-]{20,}'), 'credential'),
    (re.compile(rb'AK' + rb'IA[0-9A-Z]{16}|AI' + rb'za[0-9A-Za-z_\-]{35}'), 'credential'),
    (re.compile(rb'-----BEGIN [A-Z ]*PRIVATE ' + rb'KEY-----'), 'private key'),
]
COMMIT_EMAIL_ALLOWED = [b'noreply' + b'@' + b'anthropic.com']
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def main():
    tracked = set(git('ls-files', '-z').decode().rstrip('\0').split('\0')) - {''}
    if tracked != ALLOWED:
        raise RuntimeError(f'File allowlist differs: extra={sorted(tracked-ALLOWED)}, missing={sorted(ALLOWED-tracked)}')
    for path in sorted(tracked):
        full = ROOT/path
        if full.is_symlink():
            raise RuntimeError('Symlinks are not permitted: '+path)
        check_file(path, full.read_bytes())
    commits = git('rev-list', '--all').decode().split()
    blobs = check_history(commits)
    for commit in commits:
        check_text('commit message '+commit[:12], git('log', '-1', '--format=%B', commit), COMMIT_EMAIL_ALLOWED)
    print(f'Publication boundary passed: {len(tracked)} files; {len(commits)} reachable commits; '
          f'{blobs} historical blobs.')


def check_history(commits):
    checked = set()
    for commit in commits:
        for record in git('ls-tree', '-r', '-z', commit).split(b'\0'):
            if not record:
                continue
            metadata, raw_path = record.split(b'\t', 1)
            mode, kind, blob = metadata.decode().split()
            path = raw_path.decode()
            if path not in ALLOWED or kind != 'blob' or mode not in ('100644', '100755'):
                raise RuntimeError(f'Disallowed history entry in {commit[:12]}: {path}')
            if blob not in checked:
                check_file(path, git('cat-file', 'blob', blob))
                checked.add(blob)
    return len(checked)


def check_file(path, data):
    if path.endswith('.png'):
        check_text(path, png_text(path, data))
        return
    data.decode('utf-8')
    check_text(path, data)


def check_text(where, data, allowed=()):
    for allowed_text in allowed:
        data = data.replace(allowed_text, b'')
    if any(prefix in data for prefix in LOCAL_PATHS):
        raise RuntimeError('Local filesystem path in '+where)
    for pattern, what in FORBIDDEN:
        match = pattern.search(data)
        if match:
            raise RuntimeError(f'{what} in {where}: {match.group(0)[:40]!r}')


def png_text(path, data):
    """The text chunks of a PNG (metadata), which is where readable strings live in an image file."""
    if not data.startswith(PNG_SIGNATURE):
        raise RuntimeError('Unexpected image format: '+path)
    position, texts = len(PNG_SIGNATURE), []
    while position < len(data):
        length = int.from_bytes(data[position:position+4], 'big')
        kind, body = data[position+4:position+8], data[position+8:position+8+length]
        if kind == b'tEXt':
            texts.append(body)
        elif kind == b'zTXt':
            keyword, _, rest = body.partition(b'\0')
            texts.append(keyword+b' '+zlib.decompress(rest[1:]))
        elif kind == b'iTXt':
            keyword, _, rest = body.partition(b'\0')
            compressed, rest = rest[0], rest[2:]
            text = rest.split(b'\0', 2)[-1]
            texts.append(keyword+b' '+(zlib.decompress(text) if compressed else text))
        position += 12+length
    return b'\n'.join(texts)


if __name__ == '__main__':
    main()
