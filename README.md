# Wildrift pour les noobs — releases

Dépôt des mises à jour de l'app Android **Wildrift pour les noobs** (méta du serveur chinois de Wild Rift).

- L'app vérifie au lancement la dernière release de ce dépôt (tag `vX.Y`) et propose d'installer l'APK joint.
- `builds.json` (quand il est présent) contient les builds affichés dans les fiches champion.

Pour publier une version : exporter l'APK depuis Godot avec un numéro de version plus élevé, puis créer une release avec le tag `vX.Y` et l'APK en pièce jointe.
