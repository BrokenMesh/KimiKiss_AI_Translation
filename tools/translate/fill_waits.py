#!/usr/bin/env python3
"""Put back {Wn} waits that a translation dropped (D-026).

The waits split inside Japanese words (見{W2}る{W2}か{W2}ら) are voice timing; translators often drop
some of them, which the checker reports as CC_MISSING. For every line whose only FAIL is CC_MISSING of
{Wn} codes, each missing wait is inserted after the English word at the same relative position of the
visible text as in the Japanese. Waits may change order (TRANSLATOR.md), so this keeps the timing close
without a model call.

  fill_waits.py <check.json from check_translation.py --json> <out_answers.jsonl>
  then: batch.py import text <out_answers.jsonl> --force
"""
import json, re, sys
from collections import Counter

CODE = re.compile(r'\{[^{}]*\}')
WAIT = re.compile(r'\{W\d+\}')


def visible(s):
    return CODE.sub('', s)


def positions(ja):
    """[(code, ratio)] for every wait in the Japanese, ratio = visible chars before it / total."""
    total = max(1, len(visible(ja).replace('／', '')))
    out, seen = [], 0
    for m in re.finditer(r'\{[^{}]*\}|.', ja, re.S):
        t = m.group(0)
        if WAIT.fullmatch(t):
            out.append((t, seen / total))
        elif not t.startswith('{') and t != '／':
            seen += 1
    return out


def missing(ja, en):
    need = Counter(WAIT.findall(ja))
    need.subtract(Counter(WAIT.findall(en)))
    return need


def insert(en, code, ratio):
    """Insert code after the word that ends nearest to ratio of the visible text."""
    vis_total = len(visible(en))
    target = ratio * vis_total
    best, best_d, seen = None, None, 0
    i, n = 0, len(en)
    while i < n:
        m = CODE.match(en, i)
        if m:
            i = m.end()
            continue
        seen += 1
        i += 1
        nxt = en[i] if i < n else ' '
        if (en[i - 1] != ' ' and (nxt == ' ' or i == n)) and not (i == n and en[i - 1] in '")'):
            d = abs(seen - target)
            if best_d is None or d < best_d:
                best, best_d = i, d
    if best is None:
        best = len(en.rstrip('")'))
    return en[:best] + code + en[best:]


def fix(ja, en):
    need = missing(ja, en)
    if any(v < 0 for v in need.values()):
        return None
    pos = positions(ja)
    # pick, for each missing code, the occurrences in the Japanese with the largest ratio gap to
    # existing English waits: simply the last k occurrences of that code
    for code, k in need.items():
        if k <= 0:
            continue
        occ = [r for c, r in pos if c == code][-k:]
        for r in occ:
            en = insert(en, code, r)
    return en


def main():
    res = json.load(open(sys.argv[1]))['results']
    out, n = open(sys.argv[2], 'w', encoding='utf-8'), 0
    for r in res:
        if r['status'] != 'FAIL':
            continue
        fails = [x for x in r['reasons'] if x['level'] == 'FAIL']
        if any(x['code'] != 'CC_MISSING' for x in fails):
            continue
        if any(not WAIT.fullmatch(c) for x in fails for c in CODE.findall(x['msg'])):
            continue
        new = fix(r['ja'], r['en'])
        if new and new != r['en']:
            out.write(json.dumps({'id': r['id'], 'translation': new}, ensure_ascii=False) + '\n')
            n += 1
    print(n, 'lines fixed ->', sys.argv[2])


if __name__ == '__main__':
    main()
