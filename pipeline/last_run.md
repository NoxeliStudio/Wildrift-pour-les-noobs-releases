# Journal de la mise à jour automatique

Début : 2026-11-15 16:16 UTC

## Partie A — RiftPatchNotes
- WebFetch https://riftpatchnotes.com/champion/ahri : 2 essais, 0 réussi / 2 en échec.
- Erreur exacte (refus d'outil / demande de permission non répondue) :
  `{"error_type":"PROVENANCE_REQUIRED","source":"target","message":"The permission request for this URL was not answered in time and was withdrawn. Ask the user to include the URL in a message, or retry once they reply: a retry sends them a new permission request and waits for them again."}`
- Date des stats non lue → rpn.jsonl inchangé (meta_updated reste 2026-11-08).

## Partie B — wrchina.gg
- WebFetch https://wrchina.gg/c/lee-sin/ : 0 réussi / 1 en échec, même erreur PROVENANCE_REQUIRED que ci-dessus.
- wrchina.jsonl inchangé, merge_meta.py non relancé (aucune donnée nouvelle) ; wrchina_updated reste 2026-11-15.

## Partie C — Matchups (seemeta)
- WebFetch https://seemeta.com/en/wild-rift/champions : 0 réussi / 1 en échec, même erreur PROVENANCE_REQUIRED.
- counters.json inchangé ; counters_updated reste 2026-11-13.

## Fin
- Tous les WebFetch sont refusés dans cette exécution planifiée (aucun utilisateur pour approuver les URL). Aucun contournement (curl, Actions…) tenté, conformément aux règles.
- builds.json non modifié. Fin : 2026-11-15 16:27 UTC
