from functools import reduce
import heapq
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


def dijkstra1(graph, start, end):
    queue = [(0, start, [])]  # (cost, current_node, path)
    seen = set()
    mins = {start: 0}

    while queue:
        (cost, node, path) = heapq.heappop(queue)
        if node in seen:
            continue

        seen.add(node)
        path = path + [node]

        if node == end:
            return (cost, path)

        for next_node, weight in graph.get(node, ()):
            if next_node in seen:
                continue
            prev = mins.get(next_node, None)
            next_cost = cost + weight
            if prev is None or next_cost < prev:
                mins[next_node] = next_cost
                heapq.heappush(queue, (next_cost, next_node, path))

    return float("inf"), []


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

    graph1 = {
        "C": [('D', 3), ('E', 2)],
        "E": [("D", 1), ("F", 2), ("G", 3)],
        "F": [("H", 1), ("G", 2)],
        "D": [("F", 4)],
        "G": [("H", 2)]
    }
    print(dijkstra1(graph1, start="C", end="H"))
    print(dijkstra1(graph, start="F", end="H"))

    print(dijkstra(graph1, "C", "H"))  # TODO: this case failed
