"""Fusionne les builds méta (RiftPatchNotes, serveur chinois Diamant+) et les compétences
dans builds.json. Part toujours de base_builds.json (données JunglerGG d'origine).

Usage : python3 -I merge_meta.py SORTIE.json [AAAA-MM-JJ]
Le 2e argument (optionnel) est la date des stats RiftPatchNotes ; rpn.jsonl est
réécrit avec une seule ligne par champion (la plus récente).
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from runes import page, PATH_FR
from adapt import adapt

out_path = sys.argv[1]
meta_date = sys.argv[2] if len(sys.argv) > 2 else ''
d = json.load(open(os.path.join(HERE, 'base_builds.json')))
extra = json.load(open(os.path.join(HERE, 'extra_items.json'))) if os.path.exists(os.path.join(HERE, 'extra_items.json')) else {}
for k in ('fr', 'vals', 'icon_fix', 'when'):
    d.setdefault(k, {}).update(extra.get(k, {}))

ACTIVES = set(d['actives'])
REMOVED = set(d['removed'])
LANES = {'mid': 'mid', 'top': 'baron', 'baron': 'baron', 'solo': 'baron', 'jungle': 'jungle',
         'adc': 'dragon', 'dragon': 'dragon', 'bot': 'dragon', 'duo': 'dragon', 'support': 'support'}
RUNE_FIX = {'Hexflash': 'Hextech Flash', 'Grasp of the Undying': 'Grasp of Undying', 'Legend: BloodLine': 'Legend: Bloodline'}
BOOTS = {"Gluttonous Greaves", "Plated Steelcaps", "Mercury's Treads", "Berserker's Greaves", "Ionian Boots of Lucidity",
         "Boots of Mana", "Boots of Dynamism", "Boots of Swiftness", "Immortal Treads"}


def num(v):
    try:
        return round(float(str(v).replace('%', '').replace(',', '.').strip()), 2)
    except ValueError:
        return None


def clean(t):
    """Mêmes abréviations partout : PA (puissance), DA (dégâts d'attaque)."""
    t = re.sub(r'\b(PM|AP)\b', 'PA', t)
    t = re.sub(r'\bAD\b', 'DA', t)
    return t.strip()


def fr(n):
    return d['fr'].get(n, n)


def active_logic(b):
    """Un seul objet actif par joueur : notes sur les options qui en remplaceraient un autre."""
    active = next((i for i in b['items'] if i in ACTIVES), None)
    b['active'] = active
    notes = {}
    if active:
        for i in b.get('situational', []):
            if i in ACTIVES and i != active:
                notes[i] = 'Objet actif : un seul possible, remplace %s.' % fr(active)
    b['notes'] = notes
    ad = adapt(b['items'], b.get('situational', []))
    for a in ad:
        if a['item'] in notes:
            a['note'] = notes[a['item']]
    b['adapt'] = ad


KNOWN = set(d['fr']) | set(d['vals']) | set(d.get('desc', {})) | BOOTS
UNKNOWN = set()


def known(i):
    if i in KNOWN:
        return True
    UNKNOWN.add(i)
    return False


def merge(b, cn):
    core = [i for i in cn.get('core', []) if i and known(i)]
    if len(core) < 2:
        return False
    has_active = any(i in ACTIVES for i in core)
    items = list(core)
    for i in b.get('items', []):
        if len(items) >= 5:
            break
        if i in items or i in REMOVED or i in BOOTS:
            continue
        if i in ACTIVES and (has_active or any(x in ACTIVES for x in items)):
            continue
        items.append(i)
    b['items'] = items
    b['situational'] = [i for i in b.get('situational', []) if i not in items]
    boots = (cn.get('boots') or '').strip()
    if boots and known(boots):
        if boots != b.get('boots'):
            b.pop('enchant', None)
        b['boots'] = boots
    runes = [RUNE_FIX.get(r, r) for r in cn.get('runes', [])]
    pg, _alts, primary = page(runes)
    if len(pg) == 5:
        old_key = b.get('keystone', '')
        b['runes'] = pg
        b['keystone'] = pg[0]
        b['rune_path'] = PATH_FR.get(primary, primary)
        b['runes_alt'] = [old_key] if old_key and old_key != pg[0] else []
    spells = [s for s in cn.get('spells', []) if s]
    if len(spells) == 2:
        b['spells'] = spells
    b['meta'] = {'src': 'Diamant+ (serveur chinois)', 'wr': num(cn.get('wr')), 'pr': num(cn.get('pr'))}
    active_logic(b)
    return True


seen = {}
for line in open(os.path.join(HERE, 'rpn.jsonl')):
    line = line.strip()
    if line:
        r = json.loads(line)
        old = seen.get(r['k'], {})
        if not r.get('abilities') and old.get('abilities'):
            r['abilities'] = old['abilities']
        if not r.get('builds') and old.get('builds'):
            r['builds'], r['best'] = old['builds'], old.get('best')
        seen[r['k']] = r  # la dernière ligne d'un champion gagne

# Noms officiels français (Data Dragon de Riot) : remplacent ceux de la source.
NAMES = {}
for line in open(os.path.join(HERE, 'ddnames.txt'), encoding='utf-8'):
    parts = line.rstrip('\n').split('|')
    if len(parts) == 6:
        NAMES[parts[0]] = dict(zip(['passive', '1', '2', '3', '4'], parts[1:]))

abilities = {}
merged = created = 0
for k, r in seen.items():
    if r.get('abilities'):
        ab = {}
        for slot, v in r['abilities'].items():
            if isinstance(v, str):
                v = ['', v]
            if isinstance(v, list) and len(v) >= 2:
                name = NAMES.get(k, {}).get(slot) or v[0].split(' (')[0]
                ab[slot] = [name, clean(v[1])]
        abilities[k] = ab
    champ = d['champions'].setdefault(k, {})
    best = r.get('best') or {}
    lanes_done = set()
    cn_lanes = {LANES.get(str(x.get('lane', '')).lower().strip()) for x in r.get('builds') or []} - {None}
    for cn in r.get('builds') or []:
        lane = LANES.get(str(cn.get('lane', '')).lower().strip())
        if not lane or lane in lanes_done:
            continue  # une seule build par lane : la plus jouée (la 1re)
        lanes_done.add(lane)
        b = champ.get(lane)
        if b is None:
            other = next(iter(champ.values()), {})
            b = {'start': [], 'items': [], 'situational': list(other.get('situational', [])),
                 'keys': list(other.get('keys', []))}
            champ[lane] = b
            created += 1
        if merge(b, cn):
            merged += 1
            bc = [i for i in best.get('core', []) if i and known(i)]
            if bc and set(bc) != set(cn.get('core', [])) and len(cn_lanes) == 1:
                b['meta']['best'] = {'core': bc, 'wr': num(best.get('wr')), 'pr': num(best.get('pr'))}
    if not champ:
        del d['champions'][k]

d['abilities'] = abilities
if meta_date:
    d['meta_updated'] = meta_date
    d['updated'] = meta_date
else:
    prev = os.path.join(HERE, '..', 'builds.json')
    if os.path.exists(prev):
        old = json.load(open(prev))
        d['meta_updated'] = old.get('meta_updated', '')
# Une ligne par champion dans rpn.jsonl
with open(os.path.join(HERE, 'rpn.jsonl'), 'w') as f:
    for r in seen.values():
        f.write(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n')
d['meta_source'] = 'RiftPatchNotes'
d['source'] = 'JunglerGG + WR-META'
json.dump(d, open(out_path, 'w'), ensure_ascii=False, separators=(',', ':'))

# Noms sans traduction ou valeurs : à compléter dans extra_items.json
names = set()
for ch in d['champions'].values():
    for b in ch.values():
        names.update(b.get('items', []))
        names.update(b.get('meta', {}).get('best', {}).get('core', []))
        if b.get('boots'):
            names.add(b['boots'])
        names.update(b.get('runes', []))
missing_fr = sorted(n for n in names if n not in d['fr'])
missing_vals = sorted(n for n in names if n not in d['vals'] and n not in d.get('desc', {}) and n not in d.get('keystone_why', {}))
print('champions', len(seen), 'builds fusionnés', merged, 'créés', created, 'compétences', len(abilities))
print('sans fr :', missing_fr)
print('objets inconnus ignorés :', sorted(UNKNOWN))
print('sans valeurs :', missing_vals[:60])
