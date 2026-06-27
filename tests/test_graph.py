"""Tests for cca.graph — dependency graph building and querying."""
from __future__ import annotations

from pathlib import Path

import pytest

from cca.graph import build_graph, get_in_degrees, get_most_imported
from cca.parser import analyze_project


@pytest.fixture
def graph_data(sample_project: Path):
    infos = analyze_project(sample_project)
    graph = build_graph(infos, sample_project)
    return infos, graph, sample_project


class TestBuildGraph:
    def test_returns_digraph(self, graph_data):
        _, graph, _ = graph_data
        import networkx as nx
        assert isinstance(graph, nx.DiGraph)

    def test_all_files_are_nodes(self, graph_data):
        infos, graph, root = graph_data
        expected = {str(i.path.relative_to(root)) for i in infos}
        assert expected == set(graph.nodes)

    def test_edge_main_imports_config(self, graph_data):
        _, graph, root = graph_data
        # main.py imports from app.config -> edge main.py -> app/config.py
        main = str(Path("main.py"))
        config = str(Path("app") / "config.py")
        assert graph.has_edge(main, config)

    def test_edge_main_imports_utils(self, graph_data):
        _, graph, root = graph_data
        main = str(Path("main.py"))
        utils = str(Path("app") / "utils.py")
        assert graph.has_edge(main, utils)

    def test_edge_models_imports_config(self, graph_data):
        _, graph, root = graph_data
        models = str(Path("app") / "models.py")
        config = str(Path("app") / "config.py")
        assert graph.has_edge(models, config)

    def test_no_self_loops(self, graph_data):
        _, graph, _ = graph_data
        for node in graph.nodes:
            assert not graph.has_edge(node, node)

    def test_stdlib_imports_not_in_graph(self, graph_data):
        # "os" is a stdlib import — should not appear as a node
        _, graph, _ = graph_data
        nodes = set(graph.nodes)
        assert "os" not in nodes
        assert "os.py" not in nodes

    def test_empty_project_gives_empty_graph(self, tmp_path: Path):
        graph = build_graph([], tmp_path)
        assert len(graph.nodes) == 0

    def test_isolated_file_no_edges(self, sample_project: Path):
        from cca.parser import FileInfo
        isolated = FileInfo(path=sample_project / "standalone.py", lines=5)
        graph = build_graph([isolated], sample_project)
        assert graph.in_degree("standalone.py") == 0
        assert graph.out_degree("standalone.py") == 0


class TestGetInDegrees:
    def test_config_has_highest_in_degree(self, graph_data):
        _, graph, _ = graph_data
        degrees = get_in_degrees(graph)
        config = str(Path("app") / "config.py")
        # config.py is imported by main.py and models.py
        assert degrees[config] >= 2

    def test_main_has_zero_in_degree(self, graph_data):
        _, graph, _ = graph_data
        degrees = get_in_degrees(graph)
        assert degrees[str(Path("main.py"))] == 0

    def test_returns_all_nodes(self, graph_data):
        infos, graph, root = graph_data
        degrees = get_in_degrees(graph)
        for info in infos:
            rel = str(info.path.relative_to(root))
            assert rel in degrees


class TestGetMostImported:
    def test_returns_sorted_descending(self, graph_data):
        _, graph, _ = graph_data
        result = get_most_imported(graph)
        counts = [c for _, c in result]
        assert counts == sorted(counts, reverse=True)

    def test_config_is_first(self, graph_data):
        _, graph, _ = graph_data
        result = get_most_imported(graph, n=3)
        top_paths = [p for p, _ in result]
        config = str(Path("app") / "config.py")
        assert top_paths[0] == config

    def test_n_limits_results(self, graph_data):
        _, graph, _ = graph_data
        assert len(get_most_imported(graph, n=2)) == 2
        assert len(get_most_imported(graph, n=1)) == 1

    def test_n_larger_than_nodes_returns_all(self, graph_data):
        infos, graph, root = graph_data
        result = get_most_imported(graph, n=1000)
        assert len(result) == len(infos)
