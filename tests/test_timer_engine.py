from utils.timers import TimerEngine


import pytest


@pytest.mark.parametrize("mode,work,break_", [("25/5", 25*60, 5*60), ("50/10", 50*60, 10*60)])
def test_timer_transitions(mode, work, break_):
    engine = TimerEngine(mode)
    engine.start()
    assert engine.phase == "work"
    assert engine.remaining == work
    for _ in range(work):
        engine.tick_manual()
    assert engine.phase == "break"
    assert engine.remaining == break_
    for _ in range(break_):
        engine.tick_manual()
    assert engine.phase == "work"
    assert engine.remaining == work
