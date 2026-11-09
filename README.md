# Wildrift pour les noobs – mises à jour

Dépôt public lu par l'appli Android **Wildrift pour les noobs** (méta du serveur chinois de Wild Rift) pour se mettre à jour toute seule.

- `latest.json` : dernière version publiée (`version`, chemin de l'`apk`, `notes`).
- `apk/` : les APK de l'appli. Ils sont tous signés avec la même clé (gardée hors de ce dépôt), sinon Android refuse la mise à jour.
- `builds.json` (quand il est présent) : builds affichés dans les fiches champion.

Pour publier une mise à jour : déposer `apk/Wildrift_pour_les_noobs-<version>.apk`, puis mettre à jour `version`, `apk` et `notes` dans `latest.json`.
