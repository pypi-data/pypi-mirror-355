from .circulant_graph import construire_liste_adjacence

import heapq

def calculer_dijkstra(graphe, sommet_depart):
    """
    Dijkstra optimisé avec file de priorité (heapq).
    Complexité : O((V + E) log V)
    """
    distances = {v: float('inf') for v in graphe}
    distances[sommet_depart] = 0
    chemins = {v: [] for v in graphe}
    chemins[sommet_depart] = [sommet_depart]

    visited = set()
    queue = [(0, sommet_depart)]  # (distance, sommet)

    while queue:
        dist_u, u = heapq.heappop(queue)
        if u in visited:
            continue
        visited.add(u)

        for voisin, poids in graphe[u]:
            nouvelle_distance = dist_u + poids
            if nouvelle_distance < distances[voisin]:
                distances[voisin] = nouvelle_distance
                chemins[voisin] = chemins[u] + [voisin]
                heapq.heappush(queue, (nouvelle_distance, voisin))

    return distances, chemins

def chemin_dijkstra(graphe, depart, arrivee):
    distances = {v: float('inf') for v in graphe}
    precedents = {}
    distances[depart] = 0
    queue = [(0, depart)]

    while queue:
        dist_u, u = heapq.heappop(queue)
        for v, poids in graphe[u]:
            alt = dist_u + poids
            if alt < distances[v]:
                distances[v] = alt
                precedents[v] = u
                heapq.heappush(queue, (alt, v))

    # Reconstruction du chemin
    chemin = []
    current = arrivee
    while current != depart:
        chemin.append(current)
        if current not in precedents:
            return []  # Aucun chemin trouvé
        current = precedents[current]
    chemin.append(depart)
    chemin.reverse()
    return chemin
