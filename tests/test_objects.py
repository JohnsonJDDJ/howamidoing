from howamidoing import *
from math import isclose

# ================
# Helper Functions
# ================

def _check_detail_struct(detail: dict, curved: bool):
    """
    Check that the structure of `detail` returned by
    get_detail() are the same accross different 
    components.
    """
    if not curved:
        assert "score" in detail
        assert "stats" in detail
        assert detail["stats"] == {}
    else:
        assert "score" in detail
        assert "stats" in detail
        assert detail["stats"] is not None
        stats = detail["stats"]
        assert "zscore" in stats
        assert "mu" in stats
        assert "sigma" in stats

# =================
# Test Assignment
# =================
def test_id():
    """Id should be unique"""
    a1 = Assignment(50, curved=False)
    a2 = Assignment(50, curved=False)
    a3 = Assignment(50, curved=False)
    assert a1.get_id() != a2.get_id()
    assert a2.get_id() != a3.get_id()

def test_score():
    """Test calculation for scores"""
    # 50/100
    a1 = Assignment(50, curved=False)
    assert isclose(a1.get_score(), 0.5)
    # 100/50
    a2 = Assignment(100, upper=50, mu=50, sigma=10, curved=True)
    assert isclose(a2.get_score(), 2)
    # -100/10
    a3 = Assignment(-100, upper=10, curved=False)
    assert isclose(a3.get_score(), -10)


def test_zscore():
    """Test calculation for zscores"""
    # (50 - 50) / 10 = 0
    a1 = Assignment(50, mu=50, sigma=10, curved=True)
    assert isclose(a1.get_zscore(), 0)
    # (-20 - 50) / 10 = 0
    a2 = Assignment(-20, mu=50, sigma=10, curved=True)
    assert isclose(a2.get_zscore(), -7)
    # Uncurved assignment = 0
    a3 = Assignment(-100, upper=10, curved=False)
    assert isclose(a3.get_zscore(), 0)


def test_primary_score():
    """Test correct primary scores"""
    # 60/100, (60 - 50) / 10 = 1
    a1 = Assignment(60, mu=50, sigma=10, curved=False)
    a2 = Assignment(60, mu=50, sigma=10, curved=True)
    assert isclose(a1.get_primary_score(), 0.6) 
    assert isclose(a2.get_primary_score(), 1)


def test_detail():
    """Test getting detail"""
    # Uncurved assignment
    a1 = Assignment(50, curved=False)
    detail = a1.get_detail()
    _check_detail_struct(detail, a1.curved)
    assert isclose(detail["score"], 0.5)

    # Curved Assignment
    a2 = Assignment(-20, mu=50, sigma=10, curved=True)
    detail = a2.get_detail()
    _check_detail_struct(detail, a2.curved)
    # Everything in stats  except zscore should 
    # be normalized by `upper`, which is 100.
    assert isclose(detail["score"], -0.2)
    assert isclose(detail["stats"]["zscore"], -7)
    assert isclose(detail["stats"]["mu"], 0.5)
    assert isclose(detail["stats"]["sigma"], 0.1)


def test_simple_clobber():
    """Test clobbering an assignment once"""
    a1 = Assignment(50, mu=50, sigma=10, curved=True)
    a1.apply_clobber(1)
    assert isclose(a1.get_zscore(), 1)
    assert isclose(a1.get_score(), 0.6)

    a2 = Assignment(50, mu=50, sigma=10, curved=True)
    a2.apply_clobber(-1)
    assert isclose(a2.get_zscore(), -1)
    assert isclose(a2.get_score(), 0.4)


def test_clobber_and_reverts():
    a = Assignment(50, mu=50, sigma=10, curved=True)
    # Apply clobber twice
    a.apply_clobber(2)
    a.apply_clobber(1)
    # Only the last clobber should be effective
    assert isclose(a.get_zscore(), 1)
    assert isclose(a.get_score(), 0.6)
    # Revert the clobbse
    a.revert_clobber()
    assert isclose(a.get_zscore(), 0)
    assert isclose(a.get_score(), 0.5)
    # Revert again should not throw error
    a.revert_clobber()