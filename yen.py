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


def yen(graph, source, target, K):
    """
    Finds k shortest loopless paths from source to target in a graph,
    including their costs.

    Args:
        graph: A dictionary representing the graph. Keys are nodes, values are dictionaries
               mapping neighbors to their edge costs.
        source: The starting node.
        target: The destination node.
        k: The number of shortest paths to find.

    Returns:
        A list of tuples containing (cost, path) for k shortest paths.
    """
    paths = [dijkstra(graph.copy(), source, target)]  # Initialize with shortest path

    for _ in range(1, K):
        candidate_paths = []
        for cost, path in paths:
            for i in range(1, len(path) - 1):
                spur_node = path[i]
                root_path = path[:i]
                modified_graph = graph.copy()
                for c, p in paths:
                    if p[:i] == root_path:
                        new_edge = modified_graph[p[i - 1]]
                        new_edge = [(e, c) for e, c in new_edge if e != p[i]]
                        modified_graph[p[i - 1]] = new_edge
                for node in root_path:
                    modified_graph.pop(node, None)
                spur_cost, spur_path = dijkstra(modified_graph, spur_node, target)
                if spur_path:
                    total_path = root_path + spur_path[1:]
                    if total_path not in [p[1] for p in paths + candidate_paths]:
                        candidate_paths.append(([spur_path[0]] + path[i:], total_path))
        if not candidate_paths:
            break
        candidate_paths.sort(key=lambda x: x[0])
        paths.append(candidate_paths.pop(0))

    return paths[:K]


if __name__ == '__main__':
    # Example usage
    graph = {
        "A": [('B', 2), ('C', 4)],
        "B": [("D", 3), ("E", 1), ("A", 2)],
        "C": [("D", 2), ("E", 5)],
        "D": [("F", 4)],
        "E": [("F", 2)]
    }

    source = "A"
    target = "F"
    k = 3
    paths = yen(graph.copy(), source=source, target=target, K=k)
    print(paths)
