# Mise à jour des builds (builds.json)

Deux sources, toutes deux du serveur chinois de Wild Rift :
- **wrchina.gg** (source principale) : pour chaque lane, les 3 cœurs d'objets et 2 pages de runes
  les plus joués en Diamant+ (winrate + part des parties), et les objets / runes des vraies builds
  du top ~25 du classement chinois de chaque champion.
- **RiftPatchNotes** : bottes et sorts d'invocateur (et secours si wrchina n'a pas le champion).

Choix de la build (merge_meta.py) : les ordres d'achat d'un même cœur sont fusionnés ; winrate corrigé
de l'échantillon (un set joué dans 15 % des parties garde la moitié de son écart) ; le set le plus joué
n'est remplacé que pour +0,3 point corrigé, et jamais par un set que le top joueurs utilise moins.
Objets 4-5 et bottes améliorées : ceux du top joueurs (≥ 30 %, bottes ≥ 50 %), si leur build
correspond à la lane. Puis les règles de cohérence (un actif, pas d'effets uniques en double…).

Données : RiftPatchNotes, pages `https://riftpatchnotes.com/champion/<slug>`
(builds les plus joués en Diamant+ sur le serveur chinois de Wild Rift).
Les slugs sont dans `builds.json` → `slugs` (clé champion → slug).

## Fichiers
- `base_builds.json` : builds JunglerGG d'origine (objets 4-5, options, touches). Ne pas modifier.
- `rpn.jsonl` : une ligne par champion `{"k", "abilities", "builds", "best"}`.
  Une nouvelle ligne pour un champion remplace l'ancienne ; si elle n'a pas
  d'`abilities`, les anciennes sont gardées.
- `ddnames.txt` : noms officiels français des compétences (Riot Data Dragon).
- `extra_items.json` : noms français et valeurs des objets absents de la base.
- `merge_meta.py` : fusionne tout et écrit `../builds.json`.

## Mise à jour quotidienne
1. Lire la date des stats sur une page (phrase « updated AAAA-MM-JJ »).
   Si elle est identique à `meta_updated` dans `../builds.json` : rien à faire.
2. Sinon, pour chaque slug, extraire les builds avec ce prompt WebFetch :
   `Extract as compact JSON one line, no notes: {"builds": [{"lane", "core": [3 items of the most popular core], "wr", "pr", "boots", "runes": [5 runes], "spells": [2]}], "best": {"core", "wr", "pr"} (highest win-rate core)}. Item/rune names in English. Only lanes explicitly labeled; only the most popular build per lane.`
   Ajouter une ligne `{"k": <clé>, "builds": [...], "best": {...}}` à `rpn.jsonl`.
3. `python3 -I merge_meta.py ../builds.json AAAA-MM-JJ`
4. Si « objets inconnus ignorés » n'est pas vide : ajouter nom français + valeurs
   dans `extra_items.json` (page `https://riftpatchnotes.com/item/<slug>`), relancer l'étape 3.
5. Vérifier (aucun build à 2 objets actifs, aucun objet retiré, runes à 5 éléments), puis commit + push.

## wrchina.gg — chaque jour
Pages : `https://wrchina.gg/c/<slug>/` (même slug que RiftPatchNotes : `builds.json` → `slugs`).
1. Lire la date « stats updated AAAA-MM-JJ » sur `https://wrchina.gg/c/lee-sin/`. Si elle est égale à
   `wrchina_updated` dans `../builds.json` : rien à faire.
2. Sinon, pour chaque slug, WebFetch avec ce prompt (lots de 8 en parallèle) :
   `Extract as compact JSON one line, no notes: {"date": "<stats updated date>", "lanes": {"<lane label exactly as written>": {"cores": [[[3 items], wr, use], ...every core item set listed for this lane, in page order], "runes": [[[runes], wr, use], ...every rune set for this lane]}}, "top": {"n": <number of real builds counted>, "date": "<builds captured date>", "items": [[item, pct], ...], "runes": [[rune, pct], ...]}}. Names exactly as written. Numbers as numbers. Do not invent anything.`
   Ajouter `{"k": <clé champion>, ...réponse}` comme nouvelle ligne de `wrchina.jsonl`
   (la dernière ligne d'un champion gagne). Page en erreur : garder l'ancienne ligne.
3. `python3 -I merge_meta.py ../builds.json <meta_updated actuel ou nouvelle date RPN>` puis
   `python3 -I check.py`, et mettre `wrchina_updated` (date de l'étape 1) dans `../builds.json` :
   `python3 -I -c "import json;p='../builds.json';d=json.load(open(p));d['wrchina_updated']='AAAA-MM-JJ';json.dump(d,open(p,'w'),ensure_ascii=False,separators=(',',':'))"`
4. Si « objets inconnus ignorés » n'est pas vide : nom anglais différent d'un objet connu → l'ajouter
   à `ITEM_ALIAS` dans merge_meta.py ; objet nouveau → `extra_items.json`. Relancer l'étape 3.

## Matchups (counters) — chaque jour aussi
Source : `https://seemeta.com/en/wild-rift/champions` (serveur chinois, Diamant+,
winrate du champion contre chaque adversaire de sa lane + winrate « attendu »
d'après la force des deux champions ; 5 plus durs et 5 plus faciles par lane).
1. Lire la date des stats (« Stats for <date> »). Si elle est égale à
   `counters_updated` dans `../builds.json` : rien à faire.
2. La page fait ~340 000 caractères : 4 appels WebFetch, offsets 0, 100000, 200000, 300000,
   avec ce prompt, et écrire chaque réponse telle quelle dans `seemeta/1.json` … `seemeta/4.json` :
   `Output ONLY compact JSON, one line, no notes, covering EVERY champion whose matchups appear in this content: {"<Champion>": {"<Lane>": {"h": [["<opponent>", <wr>, <expected>], ...hardest in order], "e": [[...easiest in order]]}}}. Lane names exactly as written (Baron, Jungle, Mid, Dragon, Support). Skip lanes without matchups. Copy numbers exactly; do not invent anything.`
3. `python3 -I counters.py AAAA-MM-JJ` : vérifie les valeurs et le contrôle croisé
   (A contre B + B contre A ≈ 100 %). S'il échoue : refaire l'extraction du morceau en cause.
4. Commit + push de `builds.json`, `pipeline/counters.json` et `pipeline/seemeta/`.
