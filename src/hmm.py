import numpy as np
import pandas as pd
from graphviz import Digraph



#################################
# Initialisation des paramètres #
#################################

"""Chaines de Markov Cachées"""


# Création de l'espace de probabilité 
observable_states= ['O1', 'O2', 'O3', 'O4']
hidden_states = ['R', 'DR', 'D', 'DG', 'G']


# On définit t la matrice de transition (probabilité de changer d'état en fonction de chaque état)
# t est de taille 5x5 car il y a 5 états cachés 
t_df = pd.DataFrame(columns=hidden_states, index=hidden_states)
t_df.loc[hidden_states[0]] = [0.250, 0.500, 0.025, 0.200, 0.025]
t_df.loc[hidden_states[1]] = [0.250, 0.150, 0.075, 0.500, 0.025]
t_df.loc[hidden_states[2]] = [0.050, 0.025, 0.050, 0.850, 0.025]
t_df.loc[hidden_states[3]] = [0.025, 0.075, 0.150, 0.125, 0.625]
t_df.loc[hidden_states[4]] = [0.050, 0.075, 0.475, 0.025, 0.375]

t = t_df.to_numpy(dtype='float64') # On crée un tableau numpy


# On définit la matrice d'émission (probabilité de réalisation d'un état en fonction de l'observation)
# e est de taille 5x4 car il y a 5 états cachés et 4 états observables
e_df = pd.DataFrame(columns=observable_states, index=hidden_states)
e_df.loc[hidden_states[0]] = [0.600, 0.175, 0.175, 0.050]
e_df.loc[hidden_states[1]] = [0.050, 0.600, 0.175, 0.175]
e_df.loc[hidden_states[2]] = [0.050, 0.175, 0.600, 0.175]
e_df.loc[hidden_states[3]] = [0.050, 0.175, 0.175, 0.600]
e_df.loc[hidden_states[4]] = [0.600, 0.050, 0.175, 0.175]

e = e_df.to_numpy(dtype='float64')



#Encodage numérique des états latents et cachés 
obs_map = {'O1':0, 'O2':1, 'O3':2, 'O4':3}
state_map = {0:'R', 1:'DR', 2:'D', 3:'DG', 4:'G'}
inv_obs_map = dict((v,k) for k, v in obs_map.items())


# fonction permettant d'avoir les porbabilités initiales du pays concerné
def get_pi(nom_pays) :
    if nom_pays == 'Iraq': 
        pi = [0.2, 0.2, 0.2, 0.2, 0.2] 
    elif nom_pays == 'Nigeria' :
        pi = [0.025, 0.025, 0.025, 0.025, 0.9]
    else: 
        pi = [0.2, 0.2, 0.2, 0.2, 0.2] 
    return pi



#########################
# Algorithme de Viterbi #
#########################


# Défifinition de l'algorithme de Viterbi 
def viterbi(pi, t, e, obs):
   
    N = np.shape(e)[0] #nombre d'états 
    T = np.shape(obs)[0] #nombre d'observations 
   
    # Initialisation du chemin d'un nombre de colonnes égal à T
    path = np.zeros(T,dtype=int)
    # Initialisation de la matrice du treillis de taille NxT
    treillis = np.zeros((N, T))
    # Initialisation de la matrice de backtracing de taille NxT 
    backtracing = np.zeros((N, T))
   
   
   # Initialisation de la construction du treillis 
    for s in range(N):
        treillis[s, 0] = pi[s] * e[s, obs[0]] 

   

    # Construction du treillis et de la matrice de backtracing 
    for k in range(1, T):
        for s in range(N):
            treillis[s, k] = np.max(treillis[:, k-1] * t[:, s]) * e[s, obs[k]] 
            backtracing[s, k] = np.argmax(treillis[:, k-1] * t[:, s])
        
    
    # Initialisation de la construction du chemin 
    path[T-1] = np.argmax(treillis[:, T-1])
    
    
    #Backtracking 
    for k in range(T-2, -1, -1):
        path[k] = backtracing[path[k+1], [k+1]]


    return path, treillis, backtracing



# Défifinition de la version lognl'algorithme de Viterbi 
def viterbi_log(pi, t, e, obs):
   
    N = np.shape(e)[0] #nombre d'états 
    T = np.shape(obs)[0] #nombre d'observations

    # On prend le log de pi, t, et e
    tiny = np.finfo(0.).tiny # tiny est le plus petit nombre possible dans Python

    # On rajoute tiny aux matrices pour s'assurer qu'on ne fait pas log(O)
    t_log = np.log(t + tiny)
    pi_log = np.log(pi + tiny)
    e_log = np.log(e + tiny)
    
  
    # On initialise la version log du treillis
    treillis_log = np.zeros((N, T))
    backtracing = np.zeros((N, T))
    path = np.zeros(T, dtype=int)
   
    # Initialisation de la construction du treillis 
    for s in range(N):
        treillis_log[s, 0] = pi_log[s] + e_log[s, obs[0]]
     

    # Construction du treillis et de la matrice de backtracing
    for k in range(1, T):
        for s in range(N):
            treillis_log[s, k] = np.max(treillis_log[:, k-1] + t_log[:, s]) + e_log[s, obs[k]] 
            backtracing[s, k] = np.argmax(treillis_log[:, k-1] + t_log[:, s])

 
    # Initialisation de la construction du chemin
    path[T-1] = np.argmax(treillis_log[:, T-1])
    
    
    #Backtracking
    for k in range(T-2, -1, -1):
        path[k] = backtracing[path[k+1], [k+1]]
        
    return path, treillis_log, backtracing



################################
# Application avec nos données #
################################


def get_states(observations_df, pi):
    observations_df = observations_df.T

    states_df = pd.DataFrame(index=observations_df.index)

    for cell in observations_df.columns:
        obs = observations_df[cell].to_numpy(dtype='int8')
        
        path, _, _ = viterbi(pi, t, e, obs)
        
        state_path = [state_map[v] for v in path]
        states_df[cell] = state_path

    return states_df


def get_states_viterbilog(observations_df, pi):
    observations_df = observations_df.T

    states_df = pd.DataFrame(index=observations_df.index)

    for cell in observations_df.columns:
        obs = observations_df[cell].to_numpy(dtype='int8')
        
        path, _, _ = viterbi_log(pi, t, e, obs)
        
        state_path = [state_map[v] for v in path]
        states_df[cell] = state_path

    return states_df


def test_viterbit():
    path = "../observations/" + input("Enter exposure filename for observation")
    observations_df = pd.read_csv(path, index_col=0)
    
    pi = [0.2, 0.2, 0.2, 0.2, 0.2] 

    states_df = get_states(observations_df, pi)

    params = path.split('_') # On récupère les infos dans le nom du fichier
    country = params[1]
    date_start, date_end = params[2], params[3]
    freq = params[4]

    filename = "controls/controls_" + country + '_' + date_start + '_' + date_end + '_' + freq

    # On enregistre le résultat
    states_df.to_csv(filename)


def graph_mcc():

    print(t_df)
    print('\n', t, t.shape, '\n')
    print(t_df.sum(axis=1))

    print(e_df)
    print('\n', e, e.shape, '\n')
    print(e_df.sum(axis=1))


    #Graphe probabiliste des transitions d'un état caché à l'autre

    g = Digraph('G', filename='../figures/Graphes probabilistes/probas.gv',
            node_attr={ 'style': 'filled'}, format='png')


    g.attr('node', shape='doublecircle')
    g.node('R', fillcolor='indigo')
    g.node('DR', fillcolor='darkcyan')
    g.node('D', fillcolor='mediumturquoise')
    g.node('DG', fillcolor='mediumseagreen')
    g.node('G', fillcolor='gold')


    g.attr('node', shape='circle')
    g.edge('R', 'R', label='0.250')
    g.edge('R', 'DR', label='0.500')
    g.edge('R', 'D', label='0.025')
    g.edge('R', 'DG', label='0.200')
    g.edge('R', 'G', label='0.025')

    g.edge('DR', 'R', label='0.250')
    g.edge('DR', 'DR', label='0.150')
    g.edge('DR', 'D', label='0.075')
    g.edge('DR', 'DG', label='0.500')
    g.edge('DR', 'G', label='0.025')

    g.edge('D', 'R', label='0.050')
    g.edge('D', 'DR', label='0.025')
    g.edge('D', 'D', label='0.050')
    g.edge('D', 'DG', label='0.850')
    g.edge('D', 'G', label='0.025')

    g.edge('DG', 'R', label='0.025')
    g.edge('DG', 'DR', label='0.075')
    g.edge('DG', 'D', label='0.150')
    g.edge('DG', 'DG', label='0.125')
    g.edge('DG', 'G', label='0.625')

    g.edge('G', 'R', label='0.050')
    g.edge('G', 'DR', label='0.075')
    g.edge('G', 'D', label='0.475')
    g.edge('G', 'DG', label='0.025')
    g.edge('G', 'G', label='0.375')

    g.view()

if __name__ == "__main__":
    graph_mcc()
