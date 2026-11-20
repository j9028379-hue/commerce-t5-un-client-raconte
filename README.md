# T5 · Un client raconte

**Dépôt public officiel du gabarit Commerce T5.** Version commerciale 1.1.0. Le code et les versions publiées font référence ici ; les copies de visionnage sur Drive ne pilotent pas le moteur.

[Parcours 6 questions → 12 écrans](https://j9028379-hue.github.io/commerce-t5-un-client-raconte/) · [Catalogue](catalogue/catalogue.json) · [Partition et police](montage/partition.json) · [Moteur de rendu](render/marchand.py) · [Worker de référence](shared/cloudflare-control-plane/) · [Rotation](audio/rotation.py) · [Musiques et crédits](audio/CREDITS.md) · [Source vidéo et attribution](render/demo/plans.json).

Les quatre MP3 adaptés sont dans `audio/pistes/` et le ZIP ; les conserver sous CC BY 4.0 avec attribution. Les anciennes pistes Pixabay ne sont pas redistribuées. Le [film historique validé](https://github.com/j9028379-hue/commerce-t5-un-client-raconte/releases/tag/temoin-sonore-01) et le [master muet](https://github.com/j9028379-hue/commerce-t5-un-client-raconte/releases/tag/essai-silencieux-01) gardent leurs images et leurs sons d’origine. La démo utilise un témoignage fictif.

Déclencher `sonore.yml` pour les contrôles ; `livrer=true` pour confirmer une livraison sur main. Le rendu marchand local prend son job et ses quatre prises, sans narration de démonstration : `python render/marchand.py --job DOSSIER --out SORTIE --state journal.sqlite`. Le projet nécessite les outils décrits dans le workflow (FFmpeg, Python, Node).
