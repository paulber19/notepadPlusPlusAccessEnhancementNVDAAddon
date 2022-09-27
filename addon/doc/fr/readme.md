# Éditeur de texte Notepad ++: complément d'accessibilité #
* Auteur: PaulBer19
* URL: paulber19@laposte.net
* Téléchargement:
	* [version stable][1]
	* [version de développement][2]
* Compatibilité:
	* Version minimum de NVDA requise: 2020.4
	* Dernière version de NVDA testée: 2022.3


# Fonctionnalités #

Cette extension a pour objectif d'améliorer l'accessibilité de l'éditeur de texte Notepad++ et ajouter des fonctionnalités pour faciliter l'édition de fichiers utilisés en langage Python et des fichiers écrit en langage markdown.

Elle reprend la plupart des compléments apportées par l'extension NVDA_notepadPlusPlus créé par Derek Riemer et Tuukka Ojala, puis modifiée par Robert Hänggi et Andre9642 <https://github.com/derekriemer/nvda-notepadPlusPlus>.

À savoir:

* vocalisation du résultat de la commande "control+b" qui permet de se déplacer au délimiteur symétrique,
* vocalisation du déplacement au prochain ou précédent signet par "F2" ou "majuscule+f2",
* signalement des lignes trop longues,
* accessibilité à la saisie semi-automatique,
* accessibilité à la recherche incrémentielle,
* Prise en charge de la fonction de recherche précédente / suivant.


Pour les fichiers Python, elle apporte:

* déplacement à la prochaine class ou méthode,
* importation du code de la fenêtre d'édition.


Pour les fichiers Markdown ou txt2tags:

* prévisualisation du résultat de la conversion en HTML dans le tampon virtuel de NVDA ou dans le navigateur par défaut,
* ajout du mode navigation pour les titres, liens, citations.



Et les autres compléments:

* annonce du numéro et du retrait de chaque ligne,
* scripts pour fixer le retrait de ligne,
* Vocalisation du déplacement du focus par touche "Début",
* Comparaison du texte sélectionné avec celui du presse-papier,
* aller à la prochaine ligne se terminant par au moins une tabulation ou un espace,
* arrangement de l'annonce du nom des documents:
	* annonce réduite du chemin des fichiers,
	* annonce du nom du fichier avant son chemin,
	* non diction des barres obliques inversées du chemin.


# Compatibilité #
Cette extension a été testé avec Notepad ++ version 7.71.


# Contraintes #
Cette extension utilise et intercepte les raccourcis de Notepad ++ configuré par défaut. Il est donc vivement conseillé, pour son bon fonctionnement, de ne pas modifier ces raccourcis.


[1]: https://github.com/paulber007/AllMyNVDAAddons/raw/notepadPlusPlusAccessEnhancement/notepadPlusPlusAccessEnhancement/notepadPlusPlusAccessEnhancement-2.3.nvda-addon
[2]: https://github.com/paulber007/AllMyNVDAAddons/tree/master/notepadPlusPlusAccessEnhancement/dev
