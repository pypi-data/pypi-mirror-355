import pytest

import vip_ivp as vip


def test_algebraic_loop():
    x = vip.loop_node()
    ix = vip.integrate(x, 0)
    x.loop_into(x + ix)

    with pytest.raises(RecursionError):
        vip.solve(10)


def test_loop_node_not_set():
    x = vip.loop_node()
    with pytest.raises(Exception):
        vip.solve(10)

    vip.new_system()
    y = vip.loop_node(shape=(2, 3))
    with pytest.raises(Exception):
        vip.solve(10)

    vip.new_system()
    z=vip.loop_node(shape=(2,3), strict=False)
    vip.solve(10)


def test_set_loop_node_two_times():
    x = vip.loop_node()
    x.loop_into(6)
    with pytest.raises(Exception):
        x.loop_into(5)


def test_crossing_integration_bounds():
    a = vip.temporal(1)
    signal = vip.temporal(lambda t: 6 - t)
    ia = vip.integrate(a, 0, maximum=signal, minimum=-1)

    ia.to_plot("Integral")

    with pytest.raises(ValueError):
        try:
            vip.solve(10, time_step=1)
        except Exception as e:
            print(e)
            raise e

def test_if_statement():
    time = vip.temporal(lambda t: t)
    with pytest.raises(ValueError):
        if time < 5:
            step = vip.temporal(0)
        else:
            step = vip.temporal(1)

        vip.solve(10, time_step=1)

def test_x0_outside_bound():
    with pytest.raises(ValueError):
        x = vip.integrate(5, 0, 2, 10)

def test_integrate_discrete_signal():
    a=vip.temporal(1)
    a_d=a.delayed(1)
    with pytest.raises(NotImplementedError):
        iad=vip.integrate(a_d,0)
