"""Build and query the project dependency graph."""
from __future__ import annotations

from pathlib import Path

import networkx as nx

from cca.parser import FileInfo


def _module_to_path(module: str, root: Path) -> Path | None:
    parts = module.split(".")
    candidate = root.joinpath(*parts).with_suffix(".py")
    if candidate.exists():
        return candidate
    pkg = root.joinpath(*parts) / "__init__.py"
    if pkg.exists():
        return pkg
    return None


def build_graph(file_infos: list[FileInfo], root: Path) -> nx.DiGraph:
    graph: nx.DiGraph = nx.DiGraph()
    path_set = {info.path for info in file_infos}

    for info in file_infos:
        rel = str(info.path.relative_to(root))
        graph.add_node(rel)

    for info in file_infos:
        src = str(info.path.relative_to(root))
        for module in info.imports:
            target = _module_to_path(module, root)
            if target and target in path_set:
                tgt = str(target.relative_to(root))
                graph.add_edge(src, tgt)

    return graph


def get_in_degrees(graph: nx.DiGraph) -> dict[str, int]:
    return dict(graph.in_degree())


def get_most_imported(graph: nx.DiGraph, n: int = 10) -> list[tuple[str, int]]:
    degrees = get_in_degrees(graph)
    return sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:n]
