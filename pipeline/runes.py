"""Transforme la liste de runes populaires en une page valide Wild Rift :
1 rune-clé + 3 runes de la voie principale (une par emplacement) + 1 rune d'une autre voie."""

KEYSTONES = ["Electrocute", "Dark Harvest", "Empowerment", "Lethal Tempo", "Fleet Footwork", "Conqueror",
             "Grasp of Undying", "Guardian", "Aery", "Arcane Comet", "Phase Rush", "First Strike", "Ice Overlord"]
PATHS = {
    "Domination": [["Cheap Shot", "Sudden Impact", "Empowered Attack"],
                   ["Chain Assault", "Tyrant", "Hubris"],
                   ["Eyeball Collection", "Relentless Hunter", "Zombie Ward"]],
    "Precision": [["Brutal", "Triumph", "Battle Zeal"],
                  ["Last Stand", "Cut Down", "Coup de Grace"],
                  ["Legend: Alacrity", "Legend: Haste", "Legend: Bloodline", "Legend: Tenacity"]],
    "Resolve": [["Demolish", "Font of Life", "Courage of the Colossus", "Unshakeable"],
                ["Second Wind", "Nullifying Orb", "Bone Plating"],
                ["Overgrowth", "Revitalize", "Perseverance"]],
    "Sorcery": [["Axiom Arcanist", "Manaflow Band", "Botanist", "Hextech Flash"],
                ["Transcendence", "Celerity", "Absolute Focus"],
                ["Scorch", "Nimbus Cloak", "Gathering Storm", "Ixtali Seedjar"]],
}
SLOT = {}
for p, slots in PATHS.items():
    for i, s in enumerate(slots):
        for r in s:
            SLOT[r] = (p, i)
PATH_FR = {"Domination": "Domination", "Precision": "Précision", "Resolve": "Volonté", "Sorcery": "Sorcellerie"}


def page(popular):
    """Retourne (page, alternatives, voie principale)."""
    keystone = next((r for r in popular if r in KEYSTONES), None)
    minors = [r for r in popular if r in SLOT]
    count = {}
    for r in minors:
        count[SLOT[r][0]] = count.get(SLOT[r][0], 0) + 1
    if not minors:
        return ([keystone] if keystone else []), [], ""
    first_index = {p: next(i for i, r in enumerate(minors) if SLOT[r][0] == p) for p in count}
    primary = max(count, key=lambda p: (count[p], -first_index[p]))
    chosen = {}
    for r in minors:
        p, i = SLOT[r]
        if p == primary and i not in chosen:
            chosen[i] = r
    secondary = next((r for r in minors if SLOT[r][0] != primary), None)
    result = ([keystone] if keystone else []) + [chosen[i] for i in sorted(chosen)]
    if secondary:
        result.append(secondary)
    alts = [r for r in popular if r not in result]
    return result, alts, primary
