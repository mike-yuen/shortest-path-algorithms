from functools import reduce
from typing import Dict, List, Tuple


def dijkstra(graph: Dict[str, List[Tuple[str, int]]], start: str, end: str):
    infinity = reduce(lambda x, y: x + y, (i[1] for u in graph for i in graph[u]))
    dist = dict.fromkeys(graph, infinity)
    prev = dict.fromkeys(graph)
    q = list(graph)

    dist[start] = 0
    while q:
        u = min(q, key=lambda x: dist[x])
        q.remove(u)
        for v, w in graph[u]:
            alt = dist[u] + w
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
    # "way"
    trav = []
    temp = end
    while temp != start:
        trav.append(prev[temp])
        temp = prev[temp]
    trav.reverse()
    trav.append(end)
    return trav, dist[end]


if __name__ == "__main__":
    graph = {
        'A': [('B', 20), ('G', 15)],
        'B': [('A', 20), ('C', 8), ('D', 9)],
        'C': [('B', 8), ('D', 6), ('E', 15), ('H', 10)],
        'D': [('B', 9), ('C', 6), ('E', 7)],
        'E': [('C', 15), ('D', 7), ('F', 22), ('G', 18)],
        'F': [('E', 22)],
        'G': [('A', 15), ('E', 18)],
        'H': [('C', 10)]
    }
    print(dijkstra(graph, "F", "H"))
