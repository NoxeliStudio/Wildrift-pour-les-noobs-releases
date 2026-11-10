"""Vérifie builds.json : un seul objet actif, aucun objet retiré, runes valides."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from runes import KEYSTONES
d = json.load(open(os.path.join(HERE, '..', 'builds.json')))
A, R = set(d['actives']), set(d['removed'])
bad = []
for k, c in d['champions'].items():
    for ln, b in c.items():
        it = b.get('items', [])
        if sum(i in A for i in it) > 1: bad.append((k, ln, '2 objets actifs'))
        if any(i in R for i in it): bad.append((k, ln, 'objet retiré'))
        if len(set(it)) != len(it): bad.append((k, ln, 'doublon'))
        ru = b.get('runes', [])
        if b.get('meta') and (len(ru) != 5 or ru[0] not in KEYSTONES): bad.append((k, ln, 'runes', ru))
print('OK' if not bad else bad)
sys.exit(1 if bad else 0)
