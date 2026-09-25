from app.services.oven_engine import (
    Interval,
    Occupancy,
    RecipeDurations,
    build_occupancies,
    find_conflicts,
    next_free_window,
)


def test_half_open_no_touch_conflict():
    a = Occupancy(1, Interval(0, 30), "bake", 1)
    b = Occupancy(1, Interval(30, 60), "bake", 2)
    assert find_conflicts([a], [b]) == []


def test_overlap_detected():
    recipe = RecipeDurations(20, 30)
    cand = build_occupancies(1, 9, 10, recipe)
    existing = [Occupancy(1, Interval(25, 40), "bake", 1)]
    assert find_conflicts(existing, cand)


def test_next_free_window_after_busy():
    existing = [
        Occupancy(1, Interval(0, 40), "ferment", 1),
        Occupancy(1, Interval(40, 70), "bake", 1),
    ]
    w = next_free_window(existing, 1, duration=30, search_from=0)
    assert w == Interval(70, 100)


def test_next_free_in_gap():
    existing = [
        Occupancy(1, Interval(0, 20), "bake", 1),
        Occupancy(1, Interval(80, 100), "bake", 2),
    ]
    w = next_free_window(existing, 1, duration=30, search_from=0)
    assert w == Interval(20, 50)


def test_off_oven_only_bake_occupies():
    # 离炉醒发：发酵不占炉，只有烘烤段；烘烤起点仍为开工+发酵
    occ = build_occupancies(1, 9, 100, RecipeDurations(40, 30), proof_off_oven=True)
    assert occ == [Occupancy(1, Interval(140, 170), "bake", 9)]


def test_off_oven_ferment_slot_free_for_others():
    # 离炉批次的发酵时段可被其他批次占用，不判冲突
    off = build_occupancies(1, 9, 100, RecipeDurations(40, 30), proof_off_oven=True)
    other = build_occupancies(1, 10, 110, RecipeDurations(10, 10))
    assert find_conflicts(off, other) == []


def test_off_oven_bake_still_conflicts():
    # 离炉只免发酵段，烘烤段重叠仍冲突
    off = build_occupancies(1, 9, 100, RecipeDurations(40, 30), proof_off_oven=True)
    other = build_occupancies(1, 10, 150, RecipeDurations(5, 20))
    assert find_conflicts(off, other)


def test_zero_ferment_only_bake_segment():
    # 布朗尼：发酵 0 分钟，未标离炉也只有烘烤段
    occ = build_occupancies(1, 9, 600, RecipeDurations(0, 30))
    assert occ == [Occupancy(1, Interval(600, 630), "bake", 9)]


def test_toggle_off_restores_two_segments():
    # 关掉离炉标记后，同一配方恢复发酵+烘烤两段占炉
    recipe = RecipeDurations(40, 30)
    occ = build_occupancies(1, 9, 100, recipe, proof_off_oven=False)
    assert occ == [
        Occupancy(1, Interval(100, 140), "ferment", 9),
        Occupancy(1, Interval(140, 170), "bake", 9),
    ]


def test_window_fits_bake_only_gap_for_off_oven():
    # 空档只够烘烤分钟：离炉批次（只占烘烤段）能排入，未离炉的排不进
    existing = [
        Occupancy(1, Interval(0, 100), "bake", 1),
        Occupancy(1, Interval(130, 200), "bake", 2),
    ]
    assert next_free_window(existing, 1, duration=30, search_from=0) == Interval(100, 130)
    assert next_free_window(existing, 1, duration=70, search_from=0) == Interval(200, 270)
