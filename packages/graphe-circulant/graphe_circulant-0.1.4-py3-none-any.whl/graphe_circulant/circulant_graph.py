import math

# Valeurs par défaut, seront écrasées par l'interface
CENTRE_X, CENTRE_Y, RAYON = 470, 318, 230

def generer_graphe_circulant(n, S):
    """
    Génère un graphe circulant avec n nbr de sommets et S ensemble de connexions (cordes) pour chaque sommet.
    Retourne les positions des sommets et les arêtes sous forme de liste.
    """

    points = []
    aretes = [] #list vide 
    # Vérifier que S est une liste
    if isinstance(S, int):
        S = list(range(1, S + 1))  # Convertir en liste si S est un entier

    for i in range(n):
        for j in S:  # Chaque sommet est relié à S voisins
            voisin = (i + j) % n  # Connexions en cercle 
            """
              % n assure que lorsqu'on dépasse n, on revient au début du cycle

              exemple avec n = 8, S = 3 (1,2,3)
                (6 + 1) % 8 = 7  
                (6 + 2) % 8 = 0  (on revient à 0, boucle fermée )
                (6 + 3) % 8 = 1 

            """
           
            aretes.append((i, voisin))
            """
              (i, voisin) est un tuple qui représente une connexion entre :
                    i -> le sommet actuel.
                    voisin -> le sommet auquel i doit être connecté.
            """ 
            """
            Exemple avec n = 8, S = 2
                [(0, 1), (0, 2), 
                (1, 2), (1, 3), 
                (2, 3), (2, 4), 
                (3, 4), (3, 5), 
                (4, 5), (4, 6), 
                (5, 6), (5, 7), 
                (6, 7), (6, 0), 
                (7, 0), (7, 1)]
            """
     


    # Calcul des positions des sommets (disposition circulaire)
    angle = 2 * math.pi / n
    points = [(CENTRE_X + RAYON * math.cos(i * angle),
               CENTRE_Y + RAYON * math.sin(i * angle)) for i in range(n)]


    return points, aretes


def set_dimensions(centre_x, centre_y, rayon):
    global CENTRE_X, CENTRE_Y, RAYON
    CENTRE_X = centre_x
    CENTRE_Y = centre_y
    RAYON = rayon




# def construire_liste_adjacence(n, aretes):
#     """
#     Construit une liste d'adjacence à partir des arêtes du graphe.
#     :param n: Nombre de sommets dans le graphe.
#     :param aretes: Liste des arêtes du graphe [(u, v), ...].
#     :return: Dictionnaire représentant la liste d'adjacence.
#     """
#     graphe = {i: [] for i in range(n)}  # Initialiser un dictionnaire vide (pour n = 5 : {0: [], 1: [], 2: [], 3: [], 4: []})
#     for u, v in aretes:
#         graphe[u].append(v) #pour chaque itération, on modifie le dictionnaire graphe
#         graphe[v].append(u)  
#     return graphe

def construire_liste_adjacence(n, aretes):
    """
    Construit une liste d'adjacence à partir des arêtes du graphe.
    :param n: Nombre de sommets dans le graphe.
    :param aretes: Liste des arêtes du graphe [(u, v), ...].
    :return: Dictionnaire représentant la liste d'adjacence.
    """
    graphe = {i: [] for i in range(n)}  # Initialise les sommets

    for u, v in aretes:
        # On vérifie que les sommets u et v sont bien dans le range [0, n-1]
        if 0 <= u < n and 0 <= v < n:
            graphe[u].append(v)
            graphe[v].append(u)
        # Sinon, on ignore l'arête (et on peut aussi logguer si besoin)
        # print("aretes :",aretes)
        # print(graphe)

    return graphe
"""
    Exemple avec n = 5 et aretes = [(0,1),(0,2),(1,3),(1,4),(2,4),(3,4)]

        Première arête (0, 1) :
            u = 0, v = 1
            graphe[0].append(1) -> ajoute 1 à la liste des voisins de 0
            graphe[1].append(0) -> ajoute 0 à la liste des voisins de 1
            --> graphe = { 0: [1], 1: [0], 2: [], 3: [], 4: [] }
        
        Deuxième arête (0, 2) :
            u = 0, v = 2
            graphe[0].append(2) ->  0 a maintenant aussi 2 comme voisin
            graphe[2].append(0) ->  2 est voisin de 0
            --> graphe = { 0: [1, 2], 1: [0], 2: [0], 3: [], 4: [] }

         .
         .
         . 
            
        graphe = {  0: [1, 2],   
                    1: [0, 3, 4],  
                    2: [0, 4],   
                    3: [1, 4],   
                    4: [1, 2, 3]  }      
""" 




 




