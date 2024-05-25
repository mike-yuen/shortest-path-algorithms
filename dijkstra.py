import heapq


def dijkstra(graph, start, end):
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
    print(dijkstra(graph1, start="C", end="H"))
