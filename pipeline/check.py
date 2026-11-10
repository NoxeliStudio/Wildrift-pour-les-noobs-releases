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
G = [{'Bulwark of the Mountain', 'Black Mist Scythe'}, {"Lord Dominik's Regards", "Serylda's Grudge", 'Mortal Reminder', 'Black Cleaver'},
     {'Trinity Force', 'Divine Sunderer', 'Essence Reaver', 'Iceborn Gauntlet', 'Lich Bane'}, {'Maw of Malmortius', "Sterak's Gage"},
     {'Muramana', "Seraph's Embrace", 'Fimbulwinter', 'Manamune', "Archangel's Staff", "Winter's Approach", 'Diadem of Songs', 'Whispering Circlet'},
     {'Maw of Malmortius', "Sterak's Gage", "Seraph's Embrace"},
     {'Ravenous Hydra', 'Titanic Hydra', 'Profane Hydra'}]
for k, c in d['champions'].items():
    for ln, b in c.items():
        it = b.get('items', [])
        if len(it) < 5: bad.append((k, ln, 'moins de 5 objets'))
        if True:
            for g in G:
                if len(g & set(it)) > 1: bad.append((k, ln, 'même effet unique', sorted(g & set(it))))
        sp = b.get('spells', [])
        if (ln == 'jungle') != ('Smite' in sp): bad.append((k, ln, 'Châtiment', sp))
        if not b.get('boots') or not b.get('start'): bad.append((k, ln, 'bottes ou départ manquant'))
        sup = [i for i in it if i in G[0]]
        if (ln == 'support') != bool(sup) or len(sup) > 1: bad.append((k, ln, 'objet de soutien', sup))
print('OK' if not bad else bad)
sys.exit(1 if bad else 0)
