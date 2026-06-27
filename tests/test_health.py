"""Tests for cca.health — composite health scoring."""
from __future__ import annotations

from pathlib import Path

import pytest

from cca.health import HealthScore, calculate_health
from cca.parser import FileInfo


def _make_info(funcs: int = 5, typed: int = 5, complexity: int = 2) -> FileInfo:
    return FileInfo(
        path=Path("f.py"),
        lines=100,
        functions=[f"f{i}" for i in range(funcs)],
        typed_functions=typed,
        complexity=complexity,
    )


class TestHealthScore:
    def test_grade_a_high_score(self):
        s = HealthScore(100, 100, 100, 100, 100)
        assert s.total == pytest.approx(100.0)
        assert s.grade == "A"

    def test_grade_d_low_score(self):
        s = HealthScore(0, 0, 0, 0, 0)
        assert s.total == pytest.approx(0.0)
        assert s.grade == "D"

    def test_grade_b_boundary(self):
        # Force total = 75 exactly: 75/0.30 = 250 — weight trick via equal scores
        # 75 = 75*0.30 + 75*0.25 + 75*0.20 + 75*0.15 + 75*0.10 = 75
        s = HealthScore(75, 75, 75, 75, 75)
        assert s.grade == "B"

    def test_grade_c_boundary(self):
        s = HealthScore(60, 60, 60, 60, 60)
        assert s.grade == "C"

    def test_weights_sum_to_one(self):
        s = HealthScore(100, 100, 100, 100, 100)
        assert s._WEIGHTS is not None
        assert sum(s._WEIGHTS.values()) == pytest.approx(1.0)

    def test_to_dict_structure(self):
        s = HealthScore(80, 90, 70, 100, 100)
        d = s.to_dict()
        assert "total" in d
        assert "grade" in d
        assert "breakdown" in d
        assert "weights" in d
        assert set(d["breakdown"]) == {
            "token_savings", "type_coverage", "complexity_score",
            "dead_code_score", "cycle_score",
        }

    def test_to_dict_total_matches_property(self):
        s = HealthScore(80, 70, 60, 50, 40)
        assert s.to_dict()["total"] == pytest.approx(s.total, abs=0.1)


class TestCalculateHealth:
    def test_perfect_project(self):
        info = _make_info(funcs=4, typed=4, complexity=1)
        score = calculate_health([info], 90.0, {}, [])
        assert score.total > 70

    def test_no_token_savings_penalizes(self):
        info = _make_info()
        s_good = calculate_health([info], 80.0, {}, [])
        s_bad = calculate_health([info], 0.0, {}, [])
        assert s_good.total > s_bad.total

    def test_cycles_penalize(self):
        info = _make_info()
        s_no = calculate_health([info], 50.0, {}, [])
        s_cycle = calculate_health([info], 50.0, {}, [["a", "b"]])
        assert s_no.total > s_cycle.total

    def test_dead_code_penalizes(self):
        info = _make_info()
        s_clean = calculate_health([info], 50.0, {}, [])
        s_dead = calculate_health([info], 50.0, {"f.py": ["foo", "bar"]}, [])
        assert s_clean.total > s_dead.total

    def test_token_score_capped_at_100(self):
        info = _make_info()
        score = calculate_health([info], 150.0, {}, [])
        assert score.token_savings <= 100.0

    def test_no_functions_type_coverage_defaults_to_100(self):
        info = FileInfo(path=Path("empty.py"), lines=5)
        score = calculate_health([info], 50.0, {}, [])
        assert score.type_coverage == pytest.approx(100.0)

    def test_high_complexity_lowers_score(self):
        low_cx = _make_info(complexity=1)
        high_cx = _make_info(complexity=25)
        s_low = calculate_health([low_cx], 50.0, {}, [])
        s_high = calculate_health([high_cx], 50.0, {}, [])
        assert s_low.complexity_score > s_high.complexity_score
