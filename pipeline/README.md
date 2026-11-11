# Mise à jour des builds (builds.json)

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
