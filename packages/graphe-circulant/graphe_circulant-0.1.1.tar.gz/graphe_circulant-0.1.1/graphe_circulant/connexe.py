import math
from .parcours import parcours_largeur
from collections import deque
from itertools import combinations
from copy import deepcopy
from typing import Any
def est_connexe1(n, S):
    for s in S:
        if math.gcd(n, s) != 1:
            return False
   
    return True

"""
    n=10 et S=[1,2,3]
    PGCD(10, 1) = 1
    PGCD(10, 2) = 2
    PGCD(10, 3) = 1
"""

def est_connexe(graphe):
    #est connexe s’il existe un chemin entre n’importe quelle paire de sommets.
    # On parcourt le graphe en utilisant un parcours en largeur (BFS) depuis un sommet arbitraire.
    # Si tous les sommets sont visités, alors le graphe est connexe.
    if not graphe:
        return False
    sommet_depart = next(iter(graphe)) # Prendre un sommet au hasard comme point de départ
    visites = set(parcours_largeur(graphe, sommet_depart))
    return len(visites) == len(graphe)

def construire_sous_graphe(graphe, sommets_supprimes):
    return {
        sommet: [v for v in voisins if v not in sommets_supprimes]
        for sommet, voisins in graphe.items()
        if sommet not in sommets_supprimes
    }

def est_connexe_apres_suppression(graphe, sommets_supprimes):
    """
    Vérifie si le graphe reste connexe après suppression des sommets_supprimes.
    """
    sous_graphe = construire_sous_graphe(graphe, sommets_supprimes)
    sommets_restants = list(sous_graphe.keys())

    if not sommets_restants:
        return False

    visite = parcours_largeur(sous_graphe, sommets_restants[0])
    return len(visite) == len(sous_graphe)

def calculer_tolerance_sommets(graphe):
    """
    cherche la taille maximale d'un ensemble de sommets dont la suppression rendrait le graphe non connexe.
    """
    n = len(graphe)
    sommets = list(graphe.keys())
    tolérance = 0

    for sommet in sommets:
        if est_connexe_apres_suppression(graphe, [sommet]):
            tolérance += 1
        else:
            break  # Dès que ce n'est plus connexe, on s'arrête

    return tolérance
"""
C5(1)
combinations([0, 1, 2, 3, 4], 1) 
➜ [(0,), (1,), (2,), (3,), (4,)]

combinations([0, 1, 2, 3, 4], 2)
➜ [(0,1), (0,2), (0,3), (0,4), (1,2), (1,3), (1,4), (2,3), (2,4), (3,4)]

pour 3
[
    (0, 1, 2),
    (0, 1, 3),
    (0, 1, 4),
    (0, 2, 3),
    (0, 2, 4),
    (0, 3, 4),
    (1, 2, 3),
    (1, 2, 4),
    (1, 3, 4),
    (2, 3, 4)
]
...
"""

# def build_flow_network_for_pair(graphe, s, t):
#     """
#     Construit le réseau de flux à partir du graphe non orienté par vertex splitting.
#     Pour chaque vertex v du graphe, on crée deux nœuds : (v, "in") et (v, "out").
#     Pour v == s ou v == t, on met une capacité infinie sur l'arc interne,
#     sinon une capacité de 1.
#     Pour chaque arête (u, v) dans le graphe, on ajoute deux arcs :
#        - de (u, "out") vers (v, "in")
#        - de (v, "out") vers (u, "in")
#     Ces arcs reçoivent une capacité infinie.
#     """
#     INF = float('inf')
#     network = {}
#     # Créer les nœuds de "in" et "out" pour chaque vertex
#     for v in graphe:
#         network[(v, "in")] = {}
#         network[(v, "out")] = {}
#         # Pour s et t, on autorise un flot infini pour éviter de couper s ou t
#         if v == s or v == t:
#             network[(v, "in")][(v, "out")] = INF
#         else:
#             network[(v, "in")][(v, "out")] = 1
#     # Pour chaque arête dans le graphe non orienté, ajouter les arcs de capacité infinie
#     for u in graphe:
#         for v in graphe[u]:
#             # Arc de u_out vers v_in
#             network.setdefault((u, "out"), {})
#             network[(u, "out")][(v, "in")] = INF
#             # Arc de v_out vers u_in
#             network.setdefault((v, "out"), {})
#             network[(v, "out")][(u, "in")] = INF
#     return network

# def edmonds_karp(network, source, sink):
#     """
#     Implémente l'algorithme d'Edmonds-Karp pour calculer le flot maximum dans le réseau.
#     Le réseau est représenté comme un dictionnaire de dictionnaires.
#     """
#     flow = 0
#     INF = float('inf')
#     while True:
#         # Recherche d'un chemin d'augmentation par BFS
#         parent = {source: None}
#         queue = deque([source])
#         while queue and sink not in parent:
#             u = queue.popleft()
#             for v in network[u]:
#                 if v not in parent and network[u][v] > 0:
#                     parent[v] = u
#                     queue.append(v)
#                     if v == sink:
#                         break
#         # S'il n'y a pas de chemin vers le sink, on arrête
#         if sink not in parent:
#             break
#         # Déterminer le flot possible sur ce chemin (bottleneck)
#         v = sink
#         bottleneck = INF
#         while v != source:
#             u = parent[v]
#             bottleneck = min(bottleneck, network[u][v])
#             v = u
#         # Augmenter le flot et mettre à jour le réseau résiduel
#         v = sink
#         while v != source:
#             u = parent[v]
#             network[u][v] -= bottleneck
#             network.setdefault(v, {})
#             network[v].setdefault(u, 0)
#             network[v][u] += bottleneck
#             v = u
#         flow += bottleneck
#     return flow

# def calculer_tolerance_sommets(graphe):
#     """
#     Calcule la tolérance aux pannes (vertex connectivity) du graphe de manière
#     efficace via une approche par flot maximum.
    
#     Pour un graphe non orienté, on fixe un sommet s arbitraire, puis,
#     pour chaque t ≠ s, on construit le réseau de flux par vertex splitting et
#     on calcule le flot maximum (min-cut) entre s et t. La valeur minimale ainsi
#     trouvée correspond à la connectivité par sommets.
#     """
#     vertices = list(graphe.keys())
#     n = len(vertices)
#     if n < 2:
#         return 0
#     s = vertices[0]
#     min_flow = float('inf')
#     for t in vertices[1:]:
#         # Construire le réseau pour la paire (s, t)
#         network = build_flow_network_for_pair(graphe, s, t)
#         # Créer une copie profonde du réseau car l'algorithme modifie les capacités
#         network_copy = deepcopy(network)
#         current_flow = edmonds_karp(network_copy, (s, "out"), (t, "in"))
#         min_flow = min(min_flow, current_flow)
#         # Si un cut de capacité 0 est trouvé, on peut arrêter tôt.
#         if min_flow == 0:
#             return 0
#     return min_flow


def trouver_composants_connexes(graphe):
    visites = set()
    composants = []

    def dfs(sommet, composant):
        visites.add(sommet)
        composant.append(sommet)
        for voisin in graphe.get(sommet, []):
            if voisin not in visites:
                dfs(voisin, composant)

    for sommet in graphe:
        if sommet not in visites:
            composant = []
            dfs(sommet, composant)
            composants.append(composant)

    return composants


    