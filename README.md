# Modèles de Markov cachés et conflits civils

Une petite carte *animée*, pour le plaisir.

![Syria](img/syria_2017.gif)

## Description des jeux de données

Ci-dessous une courte description des datasets utilisés.

### UCDP Georeferenced Event Dataset (GED) Global version 20.1

- *Description :* This dataset is UCDP's most disaggregated dataset, covering individual  events of organized violence (phenomena of lethal violence occurring at a given time and place). These events are sufficiently fine-grained to be geo-coded down to the level of individual villages, with temporal  durations disaggregated to single, individual days.
- *Lien :* https://ucdp.uu.se/downloads/index.html#ged_global

### Global Terrorism Database

- *Description :* Data on terrorist attacks between 1970 – 2019 updated as of 25 Feb 2021
- *Lien :* https://www.start.umd.edu/gtd/


## Présentation des composantes

### Préparation des données (`precleaning.py`)

Le programme charge les deux bases de données et en extrait les variables nécessaires, en plus d’appliquer quelques opérations de bases (filtrage, calculs de dates).

Penser à s’assurer que les chemins des bases de données dans precleaning.py sont corrects. Par défault, ils sont de la forme `../datasets/*.csv`. Les bases de données sont à renommer en `ged.csv` et `gtd.csv`.

### Calcul de l'exposition aux conflits (`exposure.py`)

Penser à s’assurer que les chemins des GeoJSON dans exposure.py sont corrects. Par défault, ils sont
de la forme `../GeoJSONs/Country.geo.json`.

Ce fichier se charge du calcul d’exposition aux conflits. Les deux matrices obtenues après calcul (une pour l’exposition aux actes terroristes, une autre aux combats conventionnels) sont enregistrées dans le dossier `../exposures/`.

Le calcul est long : environ 6 minutes pour l’exposition sur un an à intervalles d’un mois.

### Calcul de l’exposition aux conflits, version accélérée (`exposure_numba.py`)

Ce programme s’appuie sur Numba pour calculer rapidement les matrices d’exposition.

Le gain de temps est significatif : compter une petite dizaine de secondes pour l’exposition sur un an à intervalles d’un mois.

### Détermination d’une séquence d’observation (`observation.py`)

A partir des matrices d’exposition générées par exposure.py, ce programme génère une séquence d’observation pour chaque cellule géographique, sur la période donnée.

Les résultats sont enregistrés sous la forme d’un tableau .csv dans le dossier ../observations/.

### Détermination d’une séquence de contrôle territorial (`hmm.py`)

Ce programme détermine une séquence sous-jacente de contrôle territorial, à partir d’une séquence d’observations et à l’aide d’un modèle de Markov (algorithme de Viterbi). Les résultats sont enregistrés sous la forme d’un tableau .csv dans le dossier ../controls/.

### Production de graphiques (`figures.py`)

Ce programme produit un ensemble de cartes à partir des séquences de contrôle calculées par hmm.py.

Les résultats sont enregistrés sous la forme de cartes .png dans le dossier ../figures/.

Des ajustements du code sont à prévoir au cas par cas selon les pays si l’on souhaite obtenir des cartes propres
