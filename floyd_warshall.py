import numpy as np
import typing as tp


def floyd_warshall(graph: np.ndarray, start: int, end: int) -> tp.Tuple[list, float]:
    graph[np.where(np.isclose(graph, 0.))] = np.inf
    np.fill_diagonal(graph, 0.0)
    n = graph.shape[0]
    s_graph = np.tile(np.array(
        [(0., 0)], dtype=[('weight', float), ('index', int)]), n * n).reshape((n, n))
    s_graph[:, :]['weight'] = graph
    queue = [s_graph.copy()]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                weights = [s_graph[i, j]['weight'],
                           s_graph[i, k]['weight'] + s_graph[k, j]['weight']]
                min_index = np.argmin(weights)
                keep_index = s_graph[i, j]['index'] if min_index == 0 else k + 1
                s_graph[i, j] = (weights[min_index], keep_index)
        assert np.any(np.diag(s_graph['weight']) >= 0.), 'Negative Cycle'
        queue.append(s_graph.copy())
    assert start in range(n) and end in range(n) and start != end
    entry = queue[-1][start, end]
    shortest_distance = entry['weight']
    queue_index = entry['index']
    shortest_path = trace_back_shortest_path(queue, queue_index, start, end)
    return shortest_path, shortest_distance


def trace_back_shortest_path(matrix_queue: list, queue_index: int, start: int, end: int) -> list:
    if queue_index == 0:
        return [start, end]
    matrix = matrix_queue[queue_index]
    start_queue_index = matrix[start, queue_index - 1]['index']
    end_queue_index = matrix[queue_index - 1, end]['index']
    start_trace = trace_back_shortest_path(matrix_queue, start_queue_index, start, queue_index - 1)
    end_trace = trace_back_shortest_path(matrix_queue, end_queue_index, queue_index - 1, end)
    return start_trace + end_trace


if __name__ == '__main__':
    graph = np.array([
        [0, 1, 0, 4],
        [2, 0, -2, 0],
        [3, 0, 0, 0],
        [0, -5, -1, 0]
    ], dtype=float)
    path, distance = floyd_warshall(graph, 0, 2)
    print(path)
    print(distance)
