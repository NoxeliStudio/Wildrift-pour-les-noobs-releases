"""Matchups (counters) : SeeMeta, serveur chinois Diamant+, par lane.

Usage : python3 -I counters.py AAAA-MM-JJ
Lit seemeta/*.json (extraits de https://seemeta.com/en/wild-rift/champions),
vérifie, écrit counters.json puis l'ajoute à ../builds.json.
Chaque entrée : [adversaire, winrate du champion, winrate attendu d'après la force des deux].
"""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
date = sys.argv[1] if len(sys.argv) > 1 else ''
LANES = {'Baron': '2', 'Jungle': '5', 'Mid': '1', 'Dragon': '3', 'Support': '4'}
BUILDS = os.path.join(HERE, '..', 'builds.json')
d = json.load(open(BUILDS))
known = set(d['slugs'])
ALIAS = {'nunu': 'nunuwillump', 'monkeyking': 'wukong'}


def key(name):
    k = re.sub(r'[^a-z0-9]', '', name.lower())
    return ALIAS.get(k, k)


raw = {}
for path in sorted(glob.glob(os.path.join(HERE, 'seemeta', '*.json'))):
    raw.update(json.load(open(path)))

out, errors, unknown = {}, [], set()
for champ, lanes in raw.items():
    ck = key(champ)
    if ck not in known:
        unknown.add(champ)  # pas de build, mais l'appli l'affiche quand même via son nom
    for lane, m in lanes.items():
        ln = LANES.get(lane)
        if ln is None:
            errors.append(f'{champ} : lane inconnue {lane}')
            continue
        entry = {}
        for side in ('h', 'e'):
            rows = []
            for opp, wr, exp in m.get(side, []):
                ok = key(opp)
                if ok not in known:
                    unknown.add(opp)
                if not (30 <= wr <= 70 and 30 <= exp <= 70):
                    errors.append(f'{champ} vs {opp} : valeurs hors limites {wr} {exp}')
                    continue
                # Difficile = moins bien que prévu ; facile = mieux que prévu
                if (side == 'h' and wr > exp + 0.05) or (side == 'e' and wr < exp - 0.05):
                    errors.append(f'{champ} vs {opp} ({side}) : {wr} / {exp} incohérent')
                    continue
                rows.append([ok, round(wr, 1), round(exp, 1)])
            if rows:
                entry[side] = rows
        if entry:
            out.setdefault(ck, {})[ln] = entry

# Contrôle croisé : A contre B et B contre A doivent faire environ 100 %.
# Quelques écarts viennent de la source (ex. Samira) ; beaucoup = extraction ratée.
pairs, bad = 0, []
for a, lanes in out.items():
    for ln, m in lanes.items():
        for side in ('h', 'e'):
            for b, wr, _ in m.get(side, []):
                for side2 in ('h', 'e'):
                    for c, wr2, _ in out.get(b, {}).get(ln, {}).get(side2, []):
                        if c == a:
                            pairs += 1
                            if abs(wr + wr2 - 100) > 0.6:
                                bad.append(f'{a}/{b} ({ln}) : {wr} + {wr2}')
print(f'contrôle croisé : {pairs - len(bad)}/{pairs} paires cohérentes')
if bad:
    print('écarts :', '; '.join(bad))
if pairs and len(bad) > max(8, pairs * 0.1):
    errors.append('trop de paires incohérentes : extraction à refaire')

if unknown:
    print('sans build dans l\'appli :', sorted(unknown))
if errors:
    print('\n'.join(errors))
    sys.exit(1)
json.dump(out, open(os.path.join(HERE, 'counters.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
d['counters'] = out
d['counters_source'] = 'SeeMeta (serveur chinois, Diamant+)'
if date:
    d['counters_updated'] = date
json.dump(d, open(BUILDS, 'w'), ensure_ascii=False, separators=(',', ':'))
print(f'{len(out)} champions, {sum(len(v) for v in out.values())} lanes')
