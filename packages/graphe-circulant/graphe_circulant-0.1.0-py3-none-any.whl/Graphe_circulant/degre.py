def calculer_degre_sommet(sommet, aretes):
    """
    Retourne une liste des connexions et un entier représentant le degré.
    """
    # cherche tous les sommets "dest" qui sont connectés depuis le sommet "sommet"= src).
    connexions = [dest for src, dest in aretes if src == sommet] + [src for src, dest in aretes if dest == sommet]
  
    connexions = sorted(set(connexions))  # Supprimer les doublons
    degre = len(connexions)
    return connexions, degre 

"""
      si aretes = [(0, 1), (1, 2), (2, 3)] et 
           sommet = 1, 
                  alors "dest" serait 2 (car (1, 2) est une arête partant de 1)
                  connexion[2]
                  et "src" serait 0 (car (0, 1) est une arête partant de 0)
                  connexion[2,0]
                  
                  connexions serait [0, 2]
"""