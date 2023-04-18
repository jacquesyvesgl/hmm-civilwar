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

## Préparation des données (`precleaning.py`)

Penser à s'assurer que les chemins des bases de données dans `precleaning.py` sont corrects. Par défault, ils sont de la forme `datasets/*.csv`.

Les bases de données sont à renommer en `ged.csv` et `gtd.csv`.

Pour l'instant, il n'y a pas de vérifications de doublons.

## Calcul de l'exposition aux conflits (`exposure.py`)

Penser à s'assurer que les chemins des GeoJSON dans `exposure.py` sont corrects. Par défault, ils sont de la forme `GeoJSONs/Country.geo.json`.

Ce fichier se charge du calcul d'exposition aux conflits. Les paramètres sont récupérés depuis `precleaning.py`. Les matrices obtenues après calcul sont enregistrées dans le dossier `exposures/`.

Le calcul est long : environ 6 minutes pour l'exposition sur un an à intervalles d'un mois. De plus, il ne prend pas encore en compte la précision temporelle des données (problème des évènements enregistrés comme ayant eu lieu le premier du mois.)

## A faire

- Vérifier la qualité des données filtrées avec `precleaning.py` : doublons, doutes, etc.
- Prendre en compte les possibles absurdités dans le calcul de l'exposition (`exposure.py`) : évènements mal datés, mal localisés, etc.