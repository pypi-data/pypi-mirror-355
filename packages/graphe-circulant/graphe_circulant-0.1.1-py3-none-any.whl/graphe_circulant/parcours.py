def parcours_largeur(graphe, sommet_depart):
    """
    Implémente le parcours en largeur  pour un graphe donné.
    :param graphe: Dictionnaire représentant le graphe (liste d'adjacence).
    :param sommet_depart: Sommet à partir duquel commencer le parcours.
    :return: Liste des sommets visités dans l'ordre du parcours.
    """
    visites = set()  # Ensemble{} des sommets visités 
    file = [sommet_depart]  # File pour gérer les sommets à visiter
    ordre_parcours = []  # Liste pour stocker l'ordre des sommets visités

    while file:
        sommet_actuel = file.pop(0)  # Récupérer le premier sommet de la file
        if sommet_actuel not in visites:
            visites.add(sommet_actuel)  # Marquer le sommet comme visité
            ordre_parcours.append(sommet_actuel)  # Ajouter à l'ordre de parcours

            # On parcourt tous les voisins du sommet_actuel dans le graphe
            for voisin in graphe[sommet_actuel]: # sommet 0, graphe[0] nous donnera la liste [1, 2]
                if voisin not in visites:
                    file.append(voisin) #1 et 2 seront ajoutés à la file

    return ordre_parcours