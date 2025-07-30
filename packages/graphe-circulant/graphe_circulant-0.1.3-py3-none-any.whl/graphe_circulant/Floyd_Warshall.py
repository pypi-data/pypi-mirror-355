import math

def calculer_diametre_floyd(graphe):
    """
    graphe : dict {u: [(v, poids), ...], ...}
    Renvoie (diametre, liste_de_couples).
    """
    # 1. Extraire la liste des sommets et leur indice
    sommets = sorted(graphe.keys())
    n = len(sommets)
    idx = {v:i for i,v in enumerate(sommets)}

    # 2. Initialiser la matrice des distances
    INF = math.inf
    dist = [[INF]*n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0

    for u, voisins in graphe.items():
        for v, w in voisins:
            dist[idx[u]][idx[v]] = min(dist[idx[u]][idx[v]], w)

    # 3. Boucles Floyd–Warshall
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]

    # 4. Rechercher le diamètre et les paires
    diam = 0
    couples = []
    for i in range(n):
        for j in range(n):
            d = dist[i][j]
            if d != INF and d > diam:
                diam = d
                couples = [(sommets[i], sommets[j])]
            elif d == diam:
                couples.append((sommets[i], sommets[j]))

    return diam, couples
