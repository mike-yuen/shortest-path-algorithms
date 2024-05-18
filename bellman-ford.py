class Graph:
    def __init__(self, vertices):
        self.vertices = vertices
        self.edges = []

    def add_edge(self, u, v, weight):
        self.edges.append((u, v, weight))


class BellmanFord:
    def __init__(self, graph, source):
        self.graph = graph
        self.source = source
        self.distances = {vertex: float('inf') for vertex in graph.vertices}
        self.distances[source] = 0
        self.predecessors = {vertex: None for vertex in graph.vertices}

    def run(self):
        for i in range(len(self.graph.vertices) - 1):
            for u, v, weight in self.graph.edges:
                if self.distances[u] + weight < self.distances[v]:
                    self.distances[v] = self.distances[u] + weight
                    self.predecessors[v] = u

        for u, v, weight in self.graph.edges:
            if self.distances[u] + weight < self.distances[v]:
                print("Negative cycle detected")
                return

        print("Shortest distances:", self.distances)

    def get_shortest_path(self, destination):
        path = []
        while destination != self.source:
            path.append(destination)
            destination = self.predecessors[destination]
        path.append(self.source)
        return path[::-1]


if __name__ == '__main__':
    vertices = ['A', 'B', 'C', 'D', 'E']
    graph = Graph(vertices)
    graph.add_edge('A', 'B', 4)
    graph.add_edge('A', 'C', 2)
    graph.add_edge('B', 'C', 3)
    graph.add_edge('B', 'D', 2)
    graph.add_edge('B', 'E', 3)
    graph.add_edge('C', 'B', 1)
    graph.add_edge('C', 'D', 4)
    graph.add_edge('C', 'E', 5)
    graph.add_edge('E', 'D', 1)

    bf = BellmanFord(graph, 'A')
    bf.run()
    print("Shortest path from A to D:", bf.get_shortest_path('D'))
