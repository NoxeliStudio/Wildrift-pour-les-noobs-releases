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
RUNE_FIX = {'Hexflash': 'Hextech Flash', 'Grasp of the Undying': 'Grasp of Undying', 'Legend: BloodLine': 'Legend: Bloodline',
            'Unflinching': 'Perseverance', 'Summon Aery': 'Aery'}  # noms wrchina.gg
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
    'antiarmor': {"Lord Dominik's Regards", "Serylda's Grudge", 'Mortal Reminder', 'Black Cleaver'},
    'spellblade': {'Trinity Force', 'Divine Sunderer', 'Essence Reaver', 'Iceborn Gauntlet', 'Lich Bane'},
    'lifeline': {'Maw of Malmortius', "Sterak's Gage", "Seraph's Embrace"},
    'mana': {'Muramana', "Seraph's Embrace", 'Fimbulwinter', 'Manamune', "Archangel's Staff", "Winter's Approach",
             'Diadem of Songs', 'Whispering Circlet'},
    'hydra': {'Ravenous Hydra', 'Titanic Hydra', 'Profane Hydra'},
}
SUPPORT_START = {'Bulwark of the Mountain': 'Relic Shield', 'Black Mist Scythe': 'Spectral Sickle'}
STARTER = {'ad': 'Long Sword', 'ap': 'Amplifying Tome', 'tank': 'Ruby Crystal'}
START_CLASS = {'Long Sword': 'ad', 'Dagger': 'ad', 'Amplifying Tome': 'ap', 'Ruby Crystal': 'tank'}


def group_of(i):
    return next((g for g, items in GROUPS.items() if i in items), None)


def groups_of(i):
    return {g for g, items in GROUPS.items() if i in items}


def conflict(i, items):
    """Objet de `items` incompatible avec `i` (même actif, même effet unique), sinon None."""
    if i in ACTIVES:
        a = next((x for x in items if x != i and x in ACTIVES), None)
        if a:
            return a
    gs = groups_of(i)
    if gs:
        return next((x for x in items if x != i and gs & groups_of(x)), None)
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
    top = list(b.pop('_top', []))  # objets des meilleurs joueurs du champion (classement chinois)
    best_core = list(best_core) + top
    for i in b.get('items', []):
        if i in items or i in REMOVED or (len(items) >= keep and conflict(i, items)):
            continue
        # Au-delà du cœur, un objet actif est un choix de situation : il va dans les options
        if len(items) >= 3 and i in ACTIVES and i not in best_core:
            continue
        items.append(i)
    for i in top + list(b.pop('_base_items', [])) + list(best_core) + list(b.get('situational', [])):
        if len(items) >= 5:
            break
        if i in items or i in REMOVED or i in BOOTS or not known(i) or conflict(i, items):
            continue
        # Un objet actif est un choix de situation : on ne l'ajoute pas en complément
        # d'un cœur chinois, sauf s'il vient de la variante chinoise ; il reste dans les options.
        if i in ACTIVES and i not in best_core:
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
    merged = []
    for a in ad:
        if a['item'] in notes:
            a['note'] = notes[a['item']]
        same = next((m for m in merged if m['item'] == a['item']), None)
        if same:  # même objet pour deux situations : une seule ligne
            same['label'] = same['label'] + ' · ' + a['label'][:1].lower() + a['label'][1:]
        else:
            merged.append(a)
    b['adapt'] = merged


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

# wrchina.gg : cœurs et runes par lane (Diamant+ CN) + vraies builds du top ~25 du classement
# chinois de chaque champion. Une ligne par champion dans wrchina.jsonl (la dernière gagne).
WRC = {}
if os.path.exists(os.path.join(HERE, 'wrchina.jsonl')):
    for line in open(os.path.join(HERE, 'wrchina.jsonl'), encoding='utf-8'):
        line = line.strip()
        if line:
            r = json.loads(line)
            if isinstance(r.get('lanes'), dict) and r['lanes']:
                WRC[r['k']] = r

# Choix d'un set (cœur ou runes) : winrate corrigé de la taille d'échantillon, comme la tier list.
MIN_SHARE = 5.0     # % des parties du champion dans la lane : en dessous, jamais build principale
SWITCH = 0.3        # points de winrate corrigé qu'il faut gagner pour remplacer le set le plus joué
PRIOR_SHARE = 15.0  # un set joué dans 15 % des parties garde la moitié de son écart à la moyenne
TIER3 = {'Gunmetal Greaves': "Berserker's Greaves", 'Armored Advance': 'Plated Steelcaps',
         'Immortal Treads': 'Gluttonous Greaves', "Spellslinger's Shoes": 'Boots of Mana',
         'Crimson Lucidity': 'Ionian Boots of Lucidity', 'Chainlaced Crushers': "Mercury's Treads",
         'Armorcrusher Boots': 'Boots of Dynamism'}
STARTERS = {'Relic Shield', 'Spectral Sickle', 'Long Sword', 'Amplifying Tome', 'Ruby Crystal', 'Dagger',
            "Doran's Blade", "Doran's Ring", "Doran's Shield"}


def norm(n):
    return re.sub(r'[^a-z0-9]', '', str(n).lower())


KNOWN_NORM = {norm(x): x for x in KNOWN}


ITEM_ALIAS = {'amaranthtwinguard': "Amaranth's Twinguard"}


def item_name(n):
    return ITEM_ALIAS.get(norm(n)) or KNOWN_NORM.get(norm(n), n)


def lane_of(label):
    l = str(label).lower()
    for key, ln in (('adc', 'dragon'), ('duo', 'dragon'), ('dragon', 'dragon'), ('bot', 'dragon'),
                    ('support', 'support'), ('jungle', 'jungle'), ('mid', 'mid'),
                    ('baron', 'baron'), ('top', 'baron'), ('solo', 'baron')):
        if key in l:
            return ln
    return None


def pick_sets(sets, prefer=()):
    """[[noms, wr, part]] -> sets fusionnés (même contenu, ordre différent), le meilleur en premier."""
    merged = {}
    for names, wr, use in sets:
        if not names or wr is None or not use:
            continue
        m = merged.setdefault(frozenset(names), {'items': list(names), 'w': 0.0, 'use': 0.0, 'top': -1.0})
        m['w'] += wr * use
        m['use'] += use
        if use > m['top']:
            m['items'], m['top'] = list(names), use  # ordre d'achat le plus joué
    out = [{'items': m['items'], 'wr': round(m['w'] / m['use'], 2), 'use': round(m['use'], 2)} for m in merged.values()]
    if not out:
        return []
    total = sum(x['use'] for x in out)
    base = sum(x['wr'] * x['use'] for x in out) / total
    for x in out:
        x['adj'] = base + (x['wr'] - base) * x['use'] / (x['use'] + PRIOR_SHARE)
    elig = [x for x in out if x['use'] >= MIN_SHARE] or [max(out, key=lambda x: x['use'])]
    # Le set le plus joué est le plus fiable : on ne le remplace que pour un vrai gain,
    # ou à égalité quand les meilleurs joueurs du champion construisent davantage le challenger.
    ref = max(elig, key=lambda x: x['use'])
    fav = lambda x: len(set(x['items']) & set(prefer))
    best = ref
    for x in elig:
        if x is ref:
            continue
        # jamais vers un set que les meilleurs joueurs utilisent moins
        if (x['adj'] >= best['adj'] + SWITCH and fav(x) >= fav(best)) or (x['adj'] >= best['adj'] and fav(x) > fav(best)):
            best = x
    rest = sorted([x for x in out if x is not best], key=lambda x: -x['adj'])
    return [best] + rest


MAX_AGE = 10  # jours : une page wrchina plus vieille que les stats RiftPatchNotes - 10 j est ignorée


def fresh(date):
    import datetime
    ref = meta_date or d.get('meta_updated', '')
    try:
        a = datetime.date.fromisoformat(str(date)[:10])
        b = datetime.date.fromisoformat(str(ref)[:10])
    except ValueError:
        return bool(date)  # pas de date de référence : on fait confiance
    return (b - a).days <= MAX_AGE


def apply_top(b, k):
    """Lane sans données wrchina (ex. Gragas mid) : objets et bottes des meilleurs joueurs du
    champion quand même, si leur build correspond à celle de la lane (2 objets du cœur en commun)."""
    w = WRC.get(k)
    if not w or not fresh(w.get('date')) or not b.get('meta'):
        return
    top = w.get('top') or {}
    top_items = [(item_name(i), num(p) or 0) for i, p in top.get('items', []) if isinstance(i, str)]
    if len(set(b.get('items', [])[:3]) & {i for i, _ in top_items}) < 2:
        return
    b['_top'] = [i for i, p in top_items if p >= 30 and i not in STARTERS and i not in TIER3 and known(i)]
    b['meta']['top'] = {'n': top.get('n'), 'date': top.get('date')}
    t3 = next((i for i, p in top_items if i in TIER3 and p >= 50), None)
    if t3 and known(t3):
        b['boots'], b['enchant'] = TIER3[t3], t3


def wrc_lanes(k, rpn_lanes):
    """Builds par lane depuis wrchina.gg ; bottes et sorts repris de RiftPatchNotes."""
    w = WRC.get(k)
    if not w or not fresh(w.get('date')):
        return []  # page wrchina pas mise à jour depuis longtemps : RiftPatchNotes est plus récent
    top = w.get('top') or {}
    top_items = [(item_name(i), num(p) or 0) for i, p in top.get('items', []) if isinstance(i, str)]
    top_runes = [RUNE_FIX.get(i, i) for i, p in top.get('runes', []) if isinstance(i, str) and (num(p) or 0) >= 50]
    top_set = [i for i, p in top_items if p >= 50]
    out = []
    for label, L in w['lanes'].items():
        lane = lane_of(label)
        if not lane or not isinstance(L, dict):
            continue
        cores = pick_sets([([item_name(i) for i in c[0]], num(c[1]), num(c[2]))
                           for c in L.get('cores', []) if isinstance(c, list) and len(c) >= 3 and len(c[0]) >= 2
                           and all(known(item_name(i)) for i in c[0])], top_set)  # set complet seulement
        if not cores:
            continue
        # pages complètes et en anglais seulement (la source laisse parfois un nom chinois)
        runes = pick_sets([([RUNE_FIX.get(x, x) for x in c[0]], num(c[1]), num(c[2]))
                           for c in L.get('runes', []) if isinstance(c, list) and len(c) >= 3
                           and len(page([RUNE_FIX.get(x, x) for x in c[0]])[0]) == 5], top_runes)
        rp = rpn_lanes.get(lane, {})
        cn = {'lane': lane, 'core': cores[0]['items'], 'wr': cores[0]['wr'], 'pr': cores[0]['use'],
              'boots': rp.get('boots', ''), 'spells': rp.get('spells', []),
              'runes': runes[0]['items'] if runes else rp.get('runes', [])}
        alt = [c for c in cores[1:] if c['use'] >= 3 and c['wr'] > cores[0]['wr']]
        if alt:
            a = max(alt, key=lambda c: c['wr'])
            cn['best'] = {'core': a['items'], 'wr': a['wr'], 'pr': a['use']}
        # Objets du top joueurs : seulement si leur build correspond à cette lane
        tops = {i for i, _ in top_items}
        common = len(set(cn['core']) & tops)
        if top_items and common >= 2:
            cn['top'] = [i for i, p in top_items if p >= 30 and i not in STARTERS and i not in TIER3]
            cn['top_info'] = {'n': top.get('n'), 'date': top.get('date')}
            t3 = next((i for i, p in top_items if i in TIER3 and p >= 50), None)
            if t3:
                cn['tier3'] = t3
        out.append(cn)
    return out


# Noms officiels français (Data Dragon de Riot) : remplacent ceux de la source.
NAMES = {}
for line in open(os.path.join(HERE, 'ddnames.txt'), encoding='utf-8'):
    parts = line.rstrip('\n').split('|')
    if len(parts) == 6:
        NAMES[parts[0]] = dict(zip(['passive', '1', '2', '3', '4'], parts[1:]))

abilities = {}
merged = created = 0
wrc_used = set()
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
    rpn_lanes = {}
    for x in r.get('builds') or []:
        rpn_lanes.setdefault(LANES.get(str(x.get('lane', '')).lower().strip()), x)
    for cn in wrc_lanes(k, rpn_lanes):
        lane = cn['lane']
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
            wrc_used.add(k)
            b['meta']['src'] = 'Diamant+ (serveur chinois)'
            bc = [i for i in (cn.get('best') or {}).get('core', []) if known(i)]
            if bc:
                b['meta']['best'] = dict(cn['best'], core=bc)
            if cn.get('top'):
                b['_top'] = [i for i in cn['top'] if known(i)]
                b['meta']['top'] = cn['top_info']
            if cn.get('tier3') and known(cn['tier3']):
                b['boots'], b['enchant'] = TIER3[cn['tier3']], cn['tier3']
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
            apply_top(b, k)
    if not champ:
        del d['champions'][k]

# Règles de cohérence sur toutes les builds (objets, départ, sorts, bottes, notes)
for champ in d['champions'].values():
    for ln, b in champ.items():
        coherence(b, b.get('meta', {}).get('best', {}).get('core', []))
        sp = list(b.get('spells', []))
        if len(sp) < 2:  # lane créée sans sorts connus : ceux d'une autre lane du champion, sinon Flash + Embrasement
            sp = list(next((x.get('spells') for x in champ.values() if len(x.get('spells', [])) == 2), ['Flash', 'Ignite']))
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

# Type de dégâts par champion et par lane (pour la draft) : ap, ad, tank ou mixte
dmg = {}
for k, champ in d['champions'].items():
    for ln, b in champ.items():
        cls = [item_class(i) for i in b.get('items', [])[:3]]
        t = 'ap' if cls.count('ap') >= 2 else 'ad' if cls.count('ad') >= 2 else 'tank' if cls.count('tank') >= 2 else 'mixed'
        dmg.setdefault(k, {})[ln] = t
d['dmg'] = dmg

# Compositions types (théorie de draft) : remplaçants dans l'ordre si un champion est banni
comps = json.load(open(os.path.join(HERE, 'comps.json')))
for c in comps:
    for ln, keys in c['slots'].items():
        bad = [k for k in keys if k not in d['slugs']]
        assert not bad, ('champion inconnu dans', c['name'], bad)
    bad = [k for k in c.get('bans', []) if k not in d['slugs']]
    assert not bad, ('ban inconnu dans', c['name'], bad)
d['comps'] = comps

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
# Matchups (counters.py) : conservés d'une fusion à l'autre
cpath = os.path.join(HERE, 'counters.json')
if os.path.exists(cpath):
    d['counters'] = json.load(open(cpath))
    prev = os.path.join(HERE, '..', 'builds.json')
    if os.path.exists(prev):
        old = json.load(open(prev))
        for k in ('counters_source', 'counters_updated'):
            if k in old:
                d[k] = old[k]
prev = os.path.join(HERE, '..', 'builds.json')
if os.path.exists(prev):
    old = json.load(open(prev))
    if 'wrchina_updated' in old:
        d['wrchina_updated'] = old['wrchina_updated']
d['meta_source'] = 'wrchina.gg + RiftPatchNotes' if wrc_used else 'RiftPatchNotes'
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
print('champions', len(seen), 'builds fusionnés', merged, 'créés', created, 'compétences', len(abilities), 'wrchina', len(wrc_used))
print('sans fr :', missing_fr)
print('objets inconnus ignorés :', sorted(UNKNOWN))
print('sans valeurs :', missing_vals[:60])
