import numpy as np
from scipy.special import factorial as fact
import pandas as pd

def poisson(n, mean):
    return np.exp(-mean)*(mean**n)/fact(n)


def get_probabilities(E):
    """
    Calcule les probabilités d'exposition en fonction d'une matrice de mesure d'exposition
    E : exposure matrix
    """
    F = E.copy()

    for c in E.columns:
        # Calcule l'exposition moyenne par mois
        l = E[c].mean()
        
        # Remarque : on n'est pas obligé de prendre la partie entière de x,
        # car le fact de SciPy calcule la factorielle à partir de la fonction gamma.
        F[c] = E[c].apply(lambda x: poisson(x, l))

    return F


def get_observation(Et, Ec, C, T, m, xs):
    """
    Calcule l'ensemble des séquences d'observations, à partir des matrices d'exposition.
    Et, Ec : matrices d'exposition
    C, T : matrices de probabilité d'exposition
    m : chevauchement des probabilités d'exposition
    xs : les expositions observées inférieures à xs sont tronquées à 0
    """

    def preprocess_exposures(x):
        if x < xs:
            return 0
        else:
            return x

    def cell_observation(row):
        if row['Et'] == 0 and row['Ec'] == 0:
            return 0
        elif abs(row['T'] - row['C']) <= m:
            return 2
        elif row['C'] > row['T']:
            return 1
        else:
            return 3
    
    # Initialiser un DF d'observations vide
    O = pd.DataFrame(index=Et.index)

    for date in Et.columns:
        # Construire un nouveau dataframe pour la date
        df = pd.concat([Et[date],Ec[date],C[date],T[date]], axis=1).copy()
        df.columns = ['Et', 'Ec','C', 'T']

        # Troncature des expositions
        df['Et'] = df['Et'].apply(preprocess_exposures)
        df['Ec'] = df['Ec'].apply(preprocess_exposures)

        # Déterminer l'observation
        df["observation"] = df.apply(cell_observation, axis=1)

        # Ajouter la colonne d'observation pour la date donnée
        O[date] = df["observation"]

    return O


def main():
    path_t = "../exposures/" + input("Enter exposure filename for terrorism > ")
    Et = pd.read_csv(path_t, index_col=0).sort_index()

    path_c = "../exposures/" + input("Enter exposure filename for conventional > ")
    Ec = pd.read_csv(path_c, index_col=0).sort_index()

    T = get_probabilities(Et)
    C = get_probabilities(Ec)

    m = float(input("Enter a value for m (default is 0.15) > ") or 0.15)
    xs = float(input("Enter a value for xs (default is 0.01) > ") or 0.01)
    O = get_observation(Et,Ec,C,T,m,xs)
    
    print(O)

    params = path_t.split('_') # On récupère les infos dans le nom du fichier
    country = params[1]
    date_start, date_end = params[3], params[4]
    freq = params[5]

    filename = "../observations/observation_" + country + '_' + date_start + '_' + date_end + '_' + freq

    # On enregistre le résultat
    save = (input("Save ? y/N > ") == "y") or False
    if save:
        O.to_csv(filename)

if __name__ == "__main__":
    main()
