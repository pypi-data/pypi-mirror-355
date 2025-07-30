from .parcours import parcours_largeur
def calculer_distance_PL(graphe, sommet_depart, sommet_arrivee):
    """
    Calcule "la distance minimale" entre deux sommets dans un graphe 
    :param graphe: Dictionnaire représentant le graphe (liste d'adjacence)
    :return: Distance entre les deux sommets, ou float('inf') si aucun chemin n'existe
    """
    # Utiliser parcours_largeur pour obtenir l'ordre des sommets visités à partir du sommet_depart.
    ordre_parcours = parcours_largeur(graphe, sommet_depart)

    # Si le sommet d'arrivée n'est pas dans l'ordre des sommets visités, il n'y a pas de chemin
    if sommet_arrivee not in ordre_parcours:
        return float('inf')  

    # Calculer la distance en comptant le nombre de niveaux entre les sommets
    distances = {sommet_depart: 0}  # un dictionnaire qui garde une trace des distances depuis le sommet_depart.
                                    # Initialiser la distance du sommet de départ à 0

    for sommet in ordre_parcours:  # On parcourt tous les sommets visités
        for voisin in graphe[sommet]:#pour chaque sommet, on regarde ses voisins
            if voisin not in distances:  # Si le voisin n'a pas encore de distance calculée
                distances[voisin] = distances[sommet] + 1# on lui assigne la distance du sommet actuel + 1

    # Retourner la distance vers le sommet d'arrivée
    return distances.get(sommet_arrivee, float('inf')) # distances.get -> renvoie la valeur associée à sommet_arrivee
                                                       # si il ne la trouves pas, retourne float('inf') (une valeur spéciale en Python qui représente l’infini)
"""
    # Exemple d'utilisation
    graphe = {
        0: [1, 2],
        1: [0, 3, 4],
        2: [0, 4],
        3: [1, 4],
        4: [1, 2, 3]
    }

    sommet_depart = 0   
   
    distances = {0: 0}
    ordre_parcours = [0, 1, 2, 3, 4]

        🔸 sommet = 0
                voisins : [1, 2]
                1 n’est pas encore dans distances -> distances[1] = distances[0] + 1 = 1
                2 pareil -> distances[2] = distances[0] + 1 = 1

                ---> distances = {0: 0, 1: 1, 2: 1}
        
        🔸 sommet = 1
                voisins : [0, 3, 4]
                0 déjà vu -> rien
                3 pas encore vu -> distances[3] = distances[1] + 1 = 2
                4 pas encore vu -> distances[4] = distances[1] + 1 = 2

                ---> distances = {0: 0, 1: 1, 2: 1, 3: 2, 4: 2}

        
        🔸 sommet = 2
                voisins : [0, 4]
                0 et 4 déjà vus -> rien à faire

        🔸 sommet = 3
                voisins : [1, 4] 
                déjà vus -> rien

        🔸 sommet = 4
                voisins : [1, 2, 3]
                déjà vus -> rien

    Donc : distances = {0: 0, 1: 1, 2: 1, 3: 2, 4: 2}

            Distance minimale de 0 à 1 = 1
            Distance minimale de 0 à 4 = 2 
            Distance minimale de 0 à 3 = 2 

"""

def calculer_plus_court_chemin(graphe, sommet_depart, sommet_arrivee):
        """
        Calcule le plus court chemin entre deux sommets dans un graphe.
        :param graphe: Dictionnaire représentant le graphe (liste d'adjacence).
        :param sommet_depart: Sommet de départ.
        :param sommet_arrivee: Sommet d'arrivée.
        :return: Liste des sommets du chemin et dictionnaire des distances.
        """
         # Vérifier la distance entre les deux sommets
        distance = calculer_distance_PL(graphe, sommet_depart, sommet_arrivee)

         # Si aucun chemin n'existe
        if distance == float('inf'):
            return None 

        # Utiliser parcours_largeur pour obtenir les distances et les parents
        ordre_parcours = parcours_largeur(graphe, sommet_depart)

        # Reconstruire le chemin en utilisant les parents
        parents = {sommet_depart: None} #Au départ, seul sommet_depart a un parent défini (qui est None)
        for sommet in ordre_parcours:
            for voisin in graphe[sommet]:
                if voisin not in parents:
                    parents[voisin] = sommet

        #Reconstruire le chemin depuis sommet_arrivee jusqu'à sommet_depart :
        chemin = []
        sommet = sommet_arrivee
        while sommet is not None:
            chemin.append(sommet)
            sommet = parents[sommet]

        chemin.reverse()  # Inverser pour obtenir le chemin dans le bon ordre
        return chemin

"""
    # Exemple d'utilisation
    graphe = {
        0: [1, 2],
        1: [0, 3, 4],
        2: [0, 4],
        3: [1, 4],
        4: [1, 2, 3]
    }

    sommet_depart = 0
    sommet_arrivee = 4    

    ordre_parcours = [0, 1, 2, 3, 4]

    parents = {0: None}  # Le sommet 0 est le point de départ et n'a pas de parent

        🔸 sommet = 0
                voisins : [1, 2]
                1 n’est pas encore dans parent, donc -> parents[1] = 0
                2 n'est pas encore dans parent, donc -> parents[2] = 0
                ---> parents = {0: None, 1: 0, 2: 0}
        
        🔸 sommet = 1
                voisins : [0, 3, 4]
                0 déjà visité -> rien
                3 n’est pas encore dans parent, donc -> parents[3] = 1
                4 n’est pas encore dans parent, donc -> parents[4] = 1

                ---> parents = {0: None, 1: 0, 2: 0, 3: 1, 4: 1}
        
        🔸 sommet = 2
                voisins : [0, 4]
                0 et 4 ont déjà des parents -> rien à faire

        🔸 sommet = 3
                voisins : [1, 4] 
                1 et  4 ont déjà des parents -> rien à faire

        🔸 sommet = 4
                voisins : [1, 2, 3]
                1, 2 et 3 ont déjà des parents -> rien à faire

    Donc : parents = {0: None, 1: 0, 2: 0, 3: 1, 4: 1}

    chemin = []
    sommet = sommet_arrivee = 4

        🔸Sommet = 4
              On ajoute 4 à chemin, donc --> chemin = [4]
              Le parent de 4 est 1, donc on met sommet = 1

        🔸Sommet = 1
              On ajoute 1 à chemin, donc --> chemin = [4, 1]
              Le parent de 1 est 0, donc on met sommet = 0

        🔸Sommet = 0
              On ajoute 0 à chemin, donc --> chemin = [4, 1, 0].
              Le parent de 0 est None, donc on termine la reconstruction du chemin

        Donc : chemin = [4, 1, 0] (dans l'ordre inverse)

        Inverser pour obtenir le chemin dans le bon ordre ---> chemin = [0, 1, 4]
"""
        