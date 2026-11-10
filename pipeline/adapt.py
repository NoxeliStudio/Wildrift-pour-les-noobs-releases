SITUATIONS = [
    ("ad", "Contre une équipe AD", ["Death's Dance", "Randuin's Omen", "Frozen Heart", "Thornmail", "Dead Man's Plate", "Gargoyle Stoneplate", "Zhonya's Hourglass", "Iceborn Gauntlet", "Sunfire Aegis", "Amaranth's Twinguard"]),
    ("ap", "Contre une équipe AP", ["Maw of Malmortius", "Wit's End", "Kaenic Rookern", "Force of Nature", "Abyssal Mask", "Banshee's Veil", "Hollow Radiance", "Mercury's Treads"]),
    ("heal", "Contre beaucoup de soins", ["Mortal Reminder", "Chempunk Chainsword", "Morellonomicon", "Thornmail"]),
    ("tank", "Contre des tanks", ["Lord Dominik's Regards", "Serylda's Grudge", "Black Cleaver", "Void Staff", "Cryptbloom", "Liandry's Torment", "Blade of the Ruined King", "Kraken Slayer", "Divine Sunderer", "Terminus", "Bloodletter's Curse"]),
    ("shield", "Contre des boucliers", ["Serpent's Fang", "Oceanid's Trident"]),
    ("cc", "Contre beaucoup de contrôles", ["Mercurial Scimitar", "Edge of Night", "Banshee's Veil", "Mikael's Blessing"]),
    ("behind", "Si tu meurs souvent", ["Guardian Angel", "Zhonya's Hourglass", "Sterak's Gage", "Gargoyle Stoneplate", "Mantle of the Twelfth Hour", "Death's Dance", "Banshee's Veil", "Knight's Vow"]),
    ("ahead", "Si tu es en avance", ["Rabadon's Deathcap", "Infinity Edge", "The Collector", "Duskblade of Draktharr", "Lich Bane", "Infinity Orb", "Kraken Slayer", "Youmuu's Ghostblade", "Heartsteel"]),
]


def adapt(core, situational):
    out = []
    for key, label, items in SITUATIONS:
        pick = next((i for i in situational if i in items), None)
        in_core = False
        if pick is None:
            pick = next((i for i in core if i in items), None)
            in_core = pick is not None
        if pick:
            out.append({"key": key, "label": label, "item": pick, "in_core": in_core})
    return out
