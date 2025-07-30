from .connexe import est_connexe
from .distance import calculer_distance_PL

# def calculer_diametre(graphe):
#     """
#     Calcule le diamètre du graphe (la plus grande distance entre deux sommets).
#     :param graphe: Liste d'adjacence représentant le graphe.
#     :return: Le diamètre du graphe.
#     """
#     #n = len(graphe)  # Nombre de sommets dans le graphe

#     diametre = 0  # Initialiser le diamètre à 0
#     sommets = list(graphe.keys()) 
#     # Parcourir tous les sommets pour calculer les distances
#     for sommet_depart in sommets:
#         for sommet_arrivee in sommets:
#             if sommet_depart != sommet_arrivee:  # Éviter de calculer la distance d'un sommet à lui-même
#                 # Utiliser calculer_distance_PL pour calculer la distance entre deux sommets
#                 distance = calculer_distance_PL(graphe, sommet_depart, sommet_arrivee)
#                 #print(f"Distance entre {sommet_depart} et {sommet_arrivee}: {distance}")
#                 if est_connexe(graphe) == False:
#                     return float('inf')
#                 # Mettre à jour le diamètre si une distance plus grande est trouvée
#                 diametre = max(diametre, distance)

#     return diametre


def calculer_diametre(graphe):
    """
    Calcule le diamètre du graphe (la plus grande distance entre deux sommets)
    et retourne aussi les couples de sommets qui réalisent ce diamètre.

    :param graphe: Liste d'adjacence représentant le graphe.
    :return: Tuple (diametre, liste_de_chemins_max)
    """
    if not est_connexe(graphe):
        return float('inf'), []

    diametre = 0
    chemins_max = []

    sommets = list(graphe.keys())

    for sommet_depart in sommets:
        for sommet_arrivee in sommets:
            if sommet_depart != sommet_arrivee:
                distance = calculer_distance_PL(graphe, sommet_depart, sommet_arrivee)
                if distance > diametre:
                    diametre = distance
                    chemins_max = [(sommet_depart, sommet_arrivee)]
                elif distance == diametre:
                    chemins_max.append((sommet_depart, sommet_arrivee))

    # Éliminer les doublons de type (a,b) / (b,a)
    couples_uniques = set()
    couples_final = []
    for a, b in chemins_max:
        couple = tuple(sorted((a, b)))
        if couple not in couples_uniques:
            couples_uniques.add(couple)
            couples_final.append(couple)

    return diametre, couples_final

###############################################################################################
###############################################################################################
###############################################################################################

import math

class Noeud:
    def __init__(self, valeur, filsG=None, filsD=None):
        self.valeur = valeur
        self.filsG = filsG
        self.filsD = filsD

def fusion_min(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a.valeur <= b.valeur:
        tmp = a.filsD
        a.filsD = a.filsG
        a.filsG = fusion_min(tmp, b)
        return a
    else:
        tmp = b.filsD
        b.filsD = b.filsG
        b.filsG = fusion_min(tmp, a)
        return b

def fusion_max(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a.valeur >= b.valeur:
        tmp = a.filsD
        a.filsD = a.filsG
        a.filsG = fusion_max(tmp, b)
        return a
    else:
        tmp = b.filsD
        b.filsD = b.filsG
        b.filsG = fusion_max(tmp, a)
        return b

def ajout_min(v, a):
    b = Noeud(v)
    return fusion_min(a, b)

def ajout_max(v, a):
    b = Noeud(v)
    return fusion_max(a, b)


def l1(i, n, s):
    return i % s + i // s

def l2(i, n, s):
    return 1 + s - i % s + i // s

def l1t(i, n, s, t):
    return (t * n + i) % s + (t * n + i) // s

def l2t(i, n, s, t):
    return 1 + s - (t * n + i) % s + (t * n + i) // s

def l3t(i, n, s, t):
    return (t * n - i) % s + (t * n - i) // s

def l4t(i, n, s, t):
    return 1 + s - (t * n - i) % s + (t * n - i) // s

def d(i, n, s):
    a = None
    a = ajout_min(l1(i, n, s), a)
    a = ajout_min(l2(i, n, s), a)
    for t in range(1, s // math.gcd(n, s) + 1):
        a = ajout_min(l1t(i, n, s, t), a)
        a = ajout_min(l2t(i, n, s, t), a)
        a = ajout_min(l3t(i, n, s, t), a)
        a = ajout_min(l4t(i, n, s, t), a)
    return a.valeur if a else -1

def diam(n, s):
    a = None
    for i in range(2, n // 2 + 1):
        a = ajout_max(d(i, n, s), a)
    return a.valeur if a else -1

###############################################################################################
###############################################################################################
###############################################################################################
from .Dijkstra import calculer_dijkstra  # version optimisée avec heapq

def calculer_diametre_pondere(graphe):
    """
    Calcule le diamètre pondéré du graphe : la plus grande distance minimale entre deux sommets.
    Version optimisée : O(V × (V + E) log V)
    Évite les doublons de couples (u, v) ≡ (v, u)
    """
    # Vérification de poids valides
    for voisins in graphe.values():
        for _, poids in voisins:
            if poids < 0:
                raise ValueError("Le graphe contient des poids négatifs. Dijkstra ne supporte pas cela.")

    max_distance = 0
    couples_max = []

    for sommet in graphe:
        distances, _ = calculer_dijkstra(graphe, sommet)
        for autre_sommet, distance in distances.items():
            # Éviter les doublons symétriques
            if autre_sommet <= sommet:
                continue
            if distance == float('inf'):
                continue
            if distance > max_distance:
                max_distance = distance
                couples_max = [(sommet, autre_sommet)]
            elif distance == max_distance:
                couples_max.append((sommet, autre_sommet))

    return max_distance, couples_max

###############################################################################################
###############################################################################################
###############################################################################################

def PE_SUP(a, b):
    """Retourne a/b si a est divisible par b, 
       sinon retourne (x/p) + 1.
    """
    return a // b if a % b == 0 else (a // b) + 1


def FormulDiam(n, s):
    # n = q.s + r
    q = n // s
    r = n % s

    """ I """
    if r == 0:
        return (q + s - 1) // 2 , False
    

    """ II """
    if q > r:
        # cas 1 : n pair et s impair
        if n % 2 == 0 and s % 2 == 1:
            return PE_SUP(q, 2) + (s + 1) // 2 - (min(PE_SUP(r, 2), PE_SUP(s - r + 1, 2))) , False
        
        # cas 2 : n pair et s pair
        if n % 2 == 0 and s % 2 == 0:
            if r <= 2 * PE_SUP(s - 2, 4):
                return PE_SUP(q, 2) + (s - r) // 2 , False
            return q // 2 + r // 2 , False
        
        # cas 3 : n impair et s impair
        if n % 2 == 1 and s % 2 == 1:
            return PE_SUP(q, 2) + (s + 1) // 2 - (min(PE_SUP(r + 1, 2), PE_SUP(s - r + 2, 2))) , False
        
        # cas 4 : n impair et s pair
        if n % 2 == 1 and s % 2 == 0:
            if  r == 1 or r == s - 1:
                return PE_SUP(q, 2) + (s - 2) // 2 , False
            if 3 <= r <= 2 * PE_SUP(s, 4) - 1:
                return (q // 2) + (s - r + 1) // 2 , False
            return PE_SUP(q, 2) + (r - 1) // 2 , False
    
    """ III le cas de r >= q """
    # n = q.s + r    si r >= q  ===> s = a.r + b
    a = s // r
    b = s % r

    p0 = (q + r) // 2
    p1 = (r - b + (a + 1) * q + 1) // 2
    p2 = (r + b + (a - 1) * q + 1) // 2
    p3 = (b + a * q + 1) // 2
    p4 = ((r + b) * (a * q - q + 1))
    e = min(max(p1, p3), max(p0, p2))

    if q <= r and b <= a * q + 1:
        if p1 == p2 and p4 % 2 == 1:
            return p1 - 1 , False
        return e , False
    
    """All n and s"""
    borne1 = max((n // s) + 1, n - (n // s) * s - 2, (n // s) + 1 * s - n - 1)
    borne2 = (n + 2) // 4
    borne3 = ((n // 2)) // s + PE_SUP(s , 2)

    return  min(borne1, borne2, borne3) , True

