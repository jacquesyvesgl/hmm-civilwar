# -*- coding: utf-8 -*-
"""
Created on Sat May 22 15:38:28 2021

@author: Ca1000
"""

import pandas as pd
from graphviz import Digraph


################################
# Chaînes de Marvov classiques #
################################


#état de la chaîne de Markov
states = ['attentats', 'guérillas'] 

#probabilités initiales 
pi = [0.6, 0.4]

#construction d'un tableau de valeurs
state_space = pd.Series(pi, index=states, name='states')
print(state_space)
print(state_space.sum())

#matrice stochastique de transition d'un état à l'autre 
a_df = pd.DataFrame(columns=states, index=states)
a_df.loc[states[0]] = [0.7, 0.3]
a_df.loc[states[1]] = [0.4, 0.6]
print(a_df)

#construction d'un tableau de valeurs
a = a_df.values
print('\n', a, a.shape, '\n')
print(a_df.sum(axis=1))


#graphe probabiliste 

g = Digraph('G', filename='../figures/Graphes probabilistes/ex1.gv',
            node_attr={ 'style': 'filled'}, format='png')


g.node('attentats', fillcolor='darkolivegreen4')
g.node('guérillas', fillcolor='darkorange1')

g.edge('attentats', 'attentats', label='0.7')
g.edge('attentats', 'guérillas', label='0.3')
g.edge('guérillas', 'attentats', label='0.4')
g.edge('guérillas', 'guérillas', label='0.6')


g.view()



#############################
# Chaînes de Markov cachées #
#############################


# création de l'espace de probabilité 
observable_states= ['attentats', 'guérillas']
hidden_states = ['état', 'neutre', 'rebelle']
pi = [0.5, 0.1, 0.4] 

state_space = pd.Series(pi, index=hidden_states, name='states')
print(state_space)
print('\n', state_space.sum())



# on définit t la matrice de transition (probabilité de changer d'état en fonction de chaque état)
# t est de taille 3x3 car il y a 3 états cachés 

t_df = pd.DataFrame(columns=hidden_states, index=hidden_states)
t_df.loc[hidden_states[0]] = [0.6, 0.250, 0.150]
t_df.loc[hidden_states[1]] = [0.350, 0.2, 0.450]
t_df.loc[hidden_states[2]] = [0.3, 0.2, 0.5]

print(t_df)
t = t_df.values
print('\n', t, t.shape, '\n')
print(t_df.sum(axis=1))


# on définit la matrice d'émission (probabilité de réalisation d'un état en fonction de l'observation)
# e est de taille 3x2 car il y a trois états cachés et deux états observables 

e_df = pd.DataFrame(columns=observable_states, index=hidden_states)
e_df.loc[hidden_states[0]] = [0.8, 0.2]
e_df.loc[hidden_states[1]] = [0.6, 0.4]
e_df.loc[hidden_states[2]] = [0.3, 0.7]

print(e_df)
e = e_df.values
print('\n', e, e.shape, '\n')
print(e_df.sum(axis=1))



#Graphe probabiliste

g1 = Digraph('G1', filename='../figures/Graphes probabilistes/ex2.gv',
            node_attr={ 'style': 'filled'}, format='png')


g1.attr('node', shape='doublecircle')
g1.node('état', fillcolor='dodgerblue')
g1.node('neutre', fillcolor='lightgoldenrod1')
g1.node('rebelle', fillcolor='orangered2')
g1.node('attentats', fillcolor='darkolivegreen4')
g1.node('guérillas', fillcolor='darkorange1')


g.attr('node', shape='circle')
g1.edge('état', 'état', label='0.6')
g1.edge('neutre', 'neutre', label='0.2')
g1.edge('rebelle', 'rebelle', label='0.5')
g1.edge('état', 'neutre', label='0.250')
g1.edge('état', 'rebelle', label='0.150')
g1.edge('neutre', 'état', label='0.350')
g1.edge('neutre', 'rebelle', label='0.450')
g1.edge('rebelle', 'état', label='0.3')
g1.edge('rebelle', 'neutre', label='0.5')
g1.edge('état', 'attentats', label='0.8')
g1.edge('état', 'guérillas', label='0.2')
g1.edge('neutre', 'attentats', label='0.6')
g1.edge('neutre', 'guérillas', label='0.4')
g1.edge('rebelle', 'attentats', label='0.3')
g1.edge('rebelle', 'guérillas', label='0.7')


g1.view()












