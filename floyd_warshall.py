import numpy as np
import typing as tp
import process_map_data as pmd


def floyd_warshall(graph: np.ndarray, start: int, end: int) -> tp.Tuple[list, float]:
    graph[np.where(np.isclose(graph, 0.))] = np.inf
    np.fill_diagonal(graph, 0.0)
    n = graph.shape[0]
    s_graph = np.tile(np.array(
        [(0., 0)], dtype=[('weight', float), ('index', int)]), n * n).reshape((n, n))
    s_graph[:, :]['weight'] = graph
    queue = [s_graph.copy()]
    indices = np.arange(n)
    for k in range(n):
        current_graph = queue[-1]
        change_indices = np.where(indices != k)[0]
        row_weights = current_graph[k, change_indices]
        col_weights = current_graph[change_indices, k]
        prev_sub_matrix = queue[-1][change_indices, :][:, change_indices]
        sub_matrix = col_weights[:, np.newaxis]['weight'] + row_weights['weight']
        prev_weights = prev_sub_matrix['weight']
        prev_indices = prev_sub_matrix['index']
        decision_matrix = sub_matrix < prev_weights
        prev_weights[decision_matrix] = sub_matrix[decision_matrix]
        prev_indices[decision_matrix] = k + 1
        prev_sub_matrix['weight'] = prev_weights
        prev_sub_matrix['index'] = prev_indices
        new_s_graph = current_graph.copy()
        new_s_graph[np.ix_(change_indices, change_indices)] = prev_sub_matrix
        assert np.any(np.diag(new_s_graph['weight']) >= 0.), 'Negative Cycle'
        queue.append(new_s_graph)
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
    # graph = np.array([
    #     [0, 1, 0, 4],
    #     [2, 0, -2, 0],
    #     [3, 0, 0, 0],
    #     [0, -5, -1, 0]
    # ], dtype=float)
    # path, distance = floyd_warshall(graph, 0, 2)
    # assert path == [0, 3, 3, 1, 1, 2]
    # assert np.isclose(distance, -3.0)
    # print(path)
    # print(distance)
    reader = pmd.OSMReader.parse('data/turtle_lake_map_region.osm')
    graph = reader.adjacency_matrix
    print("Number of nodes: ", len(reader.index_to_node))
    print("Number of edges: ", len(reader.edges))
    distance, path = floyd_warshall(graph, start=10, end=40)
    print("Distance: ", distance)
    print("Path: ", path)
