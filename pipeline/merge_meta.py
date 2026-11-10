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


# Objets qui ne se combinent pas : même effet unique (ou un seul objet de soutien).
GROUPS = {
    'support': {'Bulwark of the Mountain', 'Black Mist Scythe'},
    'lastwhisper': {"Lord Dominik's Regards", "Serylda's Grudge", 'Mortal Reminder'},
    'spellblade': {'Trinity Force', 'Divine Sunderer', 'Essence Reaver', 'Iceborn Gauntlet', 'Lich Bane'},
    'lifeline': {'Maw of Malmortius', "Sterak's Gage"},
}
SUPPORT_START = {'Bulwark of the Mountain': 'Relic Shield', 'Black Mist Scythe': 'Spectral Sickle'}
STARTER = {'ad': 'Long Sword', 'ap': 'Amplifying Tome', 'tank': 'Ruby Crystal'}
START_CLASS = {'Long Sword': 'ad', 'Dagger': 'ad', 'Amplifying Tome': 'ap', 'Ruby Crystal': 'tank'}


def group_of(i):
    return next((g for g, items in GROUPS.items() if i in items), None)


def conflict(i, items):
    """Objet de `items` incompatible avec `i` (même actif, même effet unique), sinon None."""
    if i in ACTIVES:
        a = next((x for x in items if x != i and x in ACTIVES), None)
        if a:
            return a
    g = group_of(i)
    if g:
        return next((x for x in items if x != i and group_of(x) == g), None)
    return None


def item_class(i):
    st = str(d['vals'].get(i, {}).get('stats', ''))
    ad = "dégâts d'attaque" in st or re.search(r'\bDA\b', st)
    ap = 'puissance' in st or re.search(r'\bPA\b', st)
    if ad and not ap:
        return 'ad'
    if ap and not ad:
        return 'ap'
    if not ad and not ap:
        return 'tank'
    return 'hybrid'


def coherence(b, best_core):
    """Build cohérent : 5 objets sans doublon d'effet, objet de départ assorti, notes sur les options."""
    items = []
    keep = 3 if b.get('meta') else 0  # le cœur de la source chinoise est gardé tel quel
    for i in b.get('items', []):
        if i not in items and i not in REMOVED and (len(items) < keep or not conflict(i, items)):
            items.append(i)
    for i in list(b.pop('_base_items', [])) + list(best_core) + list(b.get('situational', [])):
        if len(items) >= 5:
            break
        if i in items or i in REMOVED or i in BOOTS or not known(i) or conflict(i, items):
            continue
        items.append(i)
    b['items'] = items
    sup = next((i for i in items if i in SUPPORT_START), None)
    situ = [i for i in b.get('situational', []) if i not in items and i not in REMOVED and group_of(i) != 'support']
    b['situational'] = situ
    if sup:
        b['start'] = [SUPPORT_START[sup]]
    elif items:
        # Départ assorti au build : on ne corrige que les contresens nets (objet AD pour un build AP, etc.)
        classes = [item_class(i) for i in items[:3]]
        ad, ap = classes.count('ad'), classes.count('ap')
        want = 'ad' if ad >= 2 and ap == 0 else 'ap' if ap >= 2 and ad == 0 else 'tank'
        start = b.get('start', [])
        if not start:
            b['start'] = [STARTER[want]]
        elif START_CLASS.get(start[0]) in ('ad', 'ap') and want in ('ad', 'ap') and START_CLASS[start[0]] != want:
            b['start'] = [STARTER[want]]
    active_logic(b)


def active_logic(b):
    """Un seul objet actif, pas deux effets uniques identiques : notes sur les options concernées."""
    active = next((i for i in b['items'] if i in ACTIVES), None)
    b['active'] = active
    notes = {}
    for i in b.get('situational', []):
        c = conflict(i, b['items'])
        if c and i in ACTIVES and c in ACTIVES:
            notes[i] = 'Objet actif : un seul possible, remplace %s.' % fr(c)
        elif c:
            notes[i] = 'Même effet unique que %s : remplace-le plutôt que de cumuler.' % fr(c)
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
    b['_base_items'] = list(b.get('items', []))
    b['items'] = list(core)
    b['situational'] = [i for i in b.get('situational', []) if i not in b['items']]
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

# Règles de cohérence sur toutes les builds (objets, départ, sorts, bottes, notes)
for champ in d['champions'].values():
    for ln, b in champ.items():
        coherence(b, b.get('meta', {}).get('best', {}).get('core', []))
        sp = list(b.get('spells', []))
        if ln == 'jungle' and sp and 'Smite' not in sp:
            sp[-1 if sp[-1] != 'Flash' else 0] = 'Smite'
        if ln != 'jungle' and 'Smite' in sp:
            sp[sp.index('Smite')] = 'Ignite'
        b['spells'] = sp
        if not b.get('boots'):
            other = next((x.get('boots') for x in champ.values() if x.get('boots')), '')
            if not other:
                cls = [item_class(i) for i in b['items'][:3]]
                other = 'Ionian Boots of Lucidity' if cls.count('ap') >= 2 else "Berserker's Greaves" if ln == 'dragon' else 'Plated Steelcaps'
            b['boots'] = other

d['abilities'] = abilities
# Identifiants Data Dragon (Riot) : icônes, noms et descriptions officiels en français.
DD_FIX = {'aurelionsol': 'AurelionSol', 'chogath': 'Chogath', 'drmundo': 'DrMundo', 'jarvaniv': 'JarvanIV',
          'kaisa': 'Kaisa', 'khazix': 'Khazix', 'kogmaw': 'KogMaw', 'ksante': 'KSante', 'leblanc': 'Leblanc',
          'leesin': 'LeeSin', 'masteryi': 'MasterYi', 'missfortune': 'MissFortune', 'nunuwillump': 'Nunu',
          'tahmkench': 'TahmKench', 'twistedfate': 'TwistedFate', 'velkoz': 'Velkoz', 'wukong': 'MonkeyKing',
          'xinzhao': 'XinZhao', 'reksai': 'RekSai', 'belveth': 'Belveth', 'norra': ''}
d['dd_ids'] = {k: DD_FIX.get(k, k[:1].upper() + k[1:]) for k in d['slugs']}
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
