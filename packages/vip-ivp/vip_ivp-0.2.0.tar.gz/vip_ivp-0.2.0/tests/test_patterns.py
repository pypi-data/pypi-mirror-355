import time

import matplotlib
import numpy as np
import pandas as pd

import vip_ivp as vip


def test_collections_get_methods():
    l = vip.temporal([1, 2, 3, 4])
    di = vip.temporal({"a": 5, "b": 6})
    arr = vip.temporal(np.array([1, 2, 3, 4, 5]))
    arr_slice = arr[2:]

    b = vip.integrate(l[0], 0)
    c = vip.integrate(di["b"], 0)
    d = vip.integrate(arr_slice[0], 0)

    vip.solve(10, time_step=1)

    print(l[0].values)
    print(di["b"].values)
    print(arr_slice[0].values)


def test_logical_operators():
    x_a = vip.temporal(lambda t: np.sin(t))
    x_b = vip.temporal(lambda t: np.sin(t + np.pi / 2))
    a = x_a >= 0
    b = x_b >= 0

    # and
    a_and_b = a & b
    b_and_a = b & a
    # or
    a_or_b = a | b
    b_or_a = b | a
    # xor
    a_xor_b = a ^ b
    b_xor_a = b ^ a
    # not
    not_a = ~a

    vip.solve(20)
    # Assertions
    # and
    assert np.array_equal(a_and_b.values, np.logical_and(a.values, b.values))
    assert np.array_equal(b_and_a.values, np.logical_and(a.values, b.values))
    # or
    assert np.array_equal(a_or_b.values, np.logical_or(a.values, b.values))
    assert np.array_equal(b_or_a.values, np.logical_or(a.values, b.values))
    # xor
    assert np.array_equal(a_xor_b.values, np.logical_xor(a.values, b.values))
    assert np.array_equal(b_xor_a.values, np.logical_xor(a.values, b.values))
    # not
    assert np.array_equal(not_a.values, np.logical_not(a.values))


def test_t_eval_over_time_step():
    t_eval = [0, 2, 2.5, 7]
    a = vip.temporal(1)

    vip.solve(10, t_eval=t_eval)

    assert np.array_equal(t_eval, a.t)


def test_solvers():
    methods = ['RK23', 'RK45', 'DOP853', 'Radau', 'BDF', 'LSODA']
    for method in methods:
        vip.new_system()
        d_n = vip.loop_node()
        n = vip.integrate(d_n, 1)
        d_n.loop_into(-0.5 * n)

        start = time.time()
        vip.solve(10, method=method, time_step=0.001)
        print(f"{method}: {time.time() - start}s")


def test_use_numpy_function():
    x = vip.temporal(5)
    a = vip.integrate(x, 0)

    np.random.seed(10)
    map_length = 100
    map_x = np.linspace(0, 100, map_length)
    map_y = np.random.rand(map_length)
    y = vip.f(np.interp)(a, map_x, map_y)

    vip.solve(10, time_step=0.01)

    error_array = y.values - np.interp(a.values, map_x, map_y)

    assert np.all(error_array == 0)


def test_use_basic_function():
    def basic_function(x: float) -> int:
        if x > 0:
            return 1
        else:
            return -1

    input = vip.temporal(lambda t: np.cos(t))
    output = vip.f(basic_function)(input)

    input.to_plot()
    output.to_plot()

    vip.solve(10, plot=False)


def test_use_numpy_method():
    array_source = vip.temporal([lambda t: t, lambda t: 2 * t, lambda t: 3 * t, lambda t: 4 * t])
    reshaped_array = array_source.m(array_source.output_type.reshape)((2, 2))
    square_array_source = vip.temporal([[lambda t: t, lambda t: 2 * t], [lambda t: 3 * t, lambda t: 4 * t]])
    # reshaped_array.to_plot()
    vip.solve(3, 1)
    print(array_source.values[0])
    print(reshaped_array.values)
    print(square_array_source.values)
    # Bug explanation: When the TemporalVariable possess a numpy array that is computed from an operation, it does not
    # manipulate the shape to have the time dimensions the last instead of the first.

    assert np.array_equal(reshaped_array.values, square_array_source.values)


def test_multidimensional_integration_source():
    arr = np.array([5, 4])
    arr_x0 = np.array([1, 0])
    lis = [5, 4]
    lis_x0 = [1, 0]
    dic = {"a": 5, "b": 4}
    dic_x0 = {"a": 1, "b": 0}

    # Integrate with sources
    da = vip.temporal(arr)
    a = vip.integrate(da, arr_x0)
    dd = vip.temporal(dic)
    d = vip.integrate(dd, dic_x0)

    # Integrate with python variables
    a2 = vip.integrate(arr, arr_x0)
    a3 = vip.integrate(lis, lis_x0)
    d2 = vip.integrate(dic, dic_x0)

    vip.solve(10, time_step=1)

    a0_fun = lambda t: 5 * t + 1
    a1_fun = lambda t: 4 * t

    # Get values
    print(a.values)
    print(d.values)

    # Evaluate integration from source
    assert np.allclose(a[0].values, a0_fun(a[0].t))
    assert np.allclose(a[1].values, a1_fun(a[1].t))
    assert np.allclose(a.values[0], a0_fun(a[0].t))
    assert np.allclose(a.values[1], a1_fun(a[1].t))
    assert np.allclose(d["a"].values, a0_fun(a[0].t))
    assert np.allclose(d["b"].values, a1_fun(a[1].t))
    # Evaluate integration from python variables
    assert np.allclose(a2[0].values, a0_fun(a[0].t))
    assert np.allclose(a2[1].values, a1_fun(a[1].t))
    assert np.allclose(a3[0].values, a0_fun(a[0].t))
    assert np.allclose(a3[1].values, a1_fun(a[1].t))
    assert np.allclose(d2["a"].values, a0_fun(a[0].t))
    assert np.allclose(d2["b"].values, a1_fun(a[1].t))


def test_array_integration_loop_node():
    dx = vip.loop_node(shape=2)
    x = vip.integrate(dx, [1, 2])
    dx.loop_into([-0.5 * x[0], -0.4 * x[1]])

    dx1 = vip.loop_node()
    x1 = vip.integrate(dx1, 1.0)
    dx1.loop_into(-0.5 * x1)

    dx2 = vip.loop_node()
    x2 = vip.integrate(dx2, 2.0)
    dx2.loop_into(-0.4 * x2)

    vip.solve(10, time_step=1)

    assert np.array_equal(x[0].values, x1.values)
    assert np.array_equal(x[1].values, x2.values)


def test_multidimensional_integration_loop_node():
    lambdas = np.linspace(0.1, 1, 6).reshape(2, 3)
    d_n = vip.loop_node(shape=(2, 3))
    n = vip.integrate(d_n, np.ones((2, 3)))
    d_n.loop_into(-n * lambdas)

    n.to_plot()

    vip.solve(10, time_step=0.001, plot=False)


def test_multidimensional_differentiation():
    source = [lambda t: t, lambda t: 2 * t, lambda t: 3 * t, lambda t: 4 * t]
    array_source = vip.temporal(source)
    diff = array_source.derivative()
    truth = [array_source[i].derivative() for i in range(len(source))]

    array_source.to_plot()
    diff.to_plot()

    vip.solve(10, time_step=1, plot=False)
    for i in range(len(source)):
        assert np.array_equal(diff[i].values, truth[i].values)


def test_set_loop_node_multiple_times():
    source1 = vip.temporal(lambda t: t)
    source2 = vip.temporal(lambda t: 2 * t)
    loop = vip.loop_node()
    loop.loop_into(source1)
    loop.loop_into(source2, force=True)
    vip.solve(10, time_step=1)
    assert np.allclose(loop.values, np.linspace(0, 30, 11))
    assert loop.expression == "source1 + source2"


def test_conditions():
    a = vip.temporal(lambda t: t)
    b = vip.temporal(5)
    c = vip.where(a < 5, a, b)
    vip.solve(10, time_step=0.1)
    assert np.array_equal(c.values, np.where(a.values < 5, a.values, b.values))


def test_scenario_interpolation():
    scenario_dict = {"t": [0, 1, 2, 3, 4], "a": [1, 2, 3, 4, 5], "b": [0, 10, -10, 10, -10]}
    scenario_df = pd.DataFrame(scenario_dict)
    scenario_json = "tests/files/scenarii/scenario_basic.json"
    scenario_csv = "tests/files/scenarii/scenario_basic.csv"

    scenarii_inputs = [scenario_df, scenario_dict, scenario_json, scenario_csv]

    for scenario in scenarii_inputs:
        print(f"Test scenario: {scenario}")
        vip.new_system()
        scenario_variable = vip.create_scenario(scenario, time_key="t", sep=";", interpolation_kind="linear")

        vip.solve(4, time_step=0.5)

        a = scenario_variable["a"]
        b = scenario_variable["b"]

        assert a.values[0] == 1
        assert a.values[1] == 1.5
        assert b.values[0] == 0
        assert b.values[1] == 5
        assert b.values[3] == 0


def test_plot_collections():
    arr = np.array([5, 4])
    arr_x0 = np.array([1, 0])
    dic = {"a": 2, "b": 3}
    dic_x0 = {"a": 1, "b": 0}
    arr2 = np.arange(6).reshape(2, 3)

    # Integrate with sources
    da = vip.temporal(arr)
    a = vip.integrate(da, arr_x0)
    dd = vip.temporal(dic)
    d = vip.integrate(dd, dic_x0)
    a2 = vip.temporal(arr2)

    matplotlib.use('Agg')
    a.to_plot("Array")
    a2.to_plot("2D array")
    d.to_plot("Dict")

    vip.solve(10, 0.1)
    print(a2.values)


def test_array_comparisons_operators():
    f1 = lambda t: t
    f2 = lambda t: 2.5 * t

    a = vip.temporal([5, 5])
    b = vip.temporal([f1, f2])

    # Equality
    equ_arr = a == b
    equ1 = b[0] == a[0]
    equ2 = b[1] == a[1]

    # Inequality
    neq_arr = a != b
    neq1 = b[0] != a[0]
    neq2 = b[1] != a[1]

    # Less than
    lt_arr = b < a
    lt1 = b[0] < a[0]
    lt2 = b[1] < a[1]

    # Greater than
    gt_arr = b > a
    gt1 = b[0] > a[0]
    gt2 = b[1] > a[1]

    # Less than or equal
    le_arr = b <= a
    le1 = b[0] <= a[0]
    le2 = b[1] <= a[1]

    # Greater than or equal
    ge_arr = b >= a
    ge1 = b[0] >= a[0]
    ge2 = b[1] >= a[1]

    vip.solve(10, 1)

    # Assertions for equality
    equ_arr.values
    assert np.array_equal(equ_arr[0].values, equ1.values)
    assert np.array_equal(equ_arr[1].values, equ2.values)

    # Assertions for inequality
    assert np.array_equal(neq_arr[0].values, neq1.values)
    assert np.array_equal(neq_arr[1].values, neq2.values)

    # Assertions for less than
    assert np.array_equal(lt_arr[0].values, lt1.values)
    assert np.array_equal(lt_arr[1].values, lt2.values)

    # Assertions for greater than
    assert np.array_equal(gt_arr[0].values, gt1.values)
    assert np.array_equal(gt_arr[1].values, gt2.values)

    # Assertions for less than or equal
    assert np.array_equal(le_arr[0].values, le1.values)
    assert np.array_equal(le_arr[1].values, le2.values)

    # Assertions for greater than or equal
    assert np.array_equal(ge_arr[0].values, ge1.values)
    assert np.array_equal(ge_arr[1].values, ge2.values)


def test_bounded_integration_by_constant():
    a = vip.temporal(1)
    ia_inc = vip.integrate(a, 2, maximum=5, minimum=2)
    ia_dec = vip.integrate(-a, 5, maximum=5, minimum=2)

    # ia_inc.to_plot("Integral")
    # ia_dec.to_plot("Decreasing integral")

    vip.solve(10)

    assert ia_inc.values[-1] == 5
    assert ia_inc.values[0] == 2
    assert ia_dec.values[0] == 5
    assert ia_dec.values[-1] == 2


def test_bounded_integration_by_variable():
    a = vip.temporal(1)
    signal = vip.temporal(lambda t: 6 - t)
    ia_inc = vip.integrate(a, 0, maximum=signal)
    ia_dec = vip.integrate(-a, 0, minimum=-signal)

    # ia_inc.to_plot("Integral")
    # ia_dec.to_plot("Decreasing integral")

    vip.solve(10, time_step=1)

    assert ia_inc.values[3] == 3
    assert ia_inc.values[-1] == -4
    assert ia_dec.values[3] == -3
    assert ia_dec.values[-1] == 4


def test_delete_event():
    a = vip.temporal(lambda t: t)

    crossing = a.crosses(6)
    vip.terminate_on(crossing & (a < 3))

    vip.solve(10)
    print(a.solver.events)

    assert a.t[-1] == 10


def test_variable_step_solving():
    # Exponential decay : dN/dt = - λ * N
    d_n = vip.loop_node()
    n = vip.integrate(d_n, 1)
    d_n.loop_into(-0.5 * n)

    # Choose which variables to plot
    # n.to_plot()
    # d_n.to_plot()

    # Solve the system. The plot will automatically show.
    vip.solve(10, time_step=None)


def test_simultaneous_actions():
    a = vip.temporal(5)
    ia = vip.integrate(a, 0)

    crossing = ia.crosses(10)
    ia.reset_on(crossing, 0)
    vip.terminate_on(crossing)

    ia.to_plot("IA")

    vip.solve(10)

    assert ia.t[-1] == 2


def test_set_timeout():
    a = vip.temporal(1)
    ia = vip.integrate(a, 0)

    timeout = vip.timeout_trigger(3)
    ia.reset_on(timeout, 0)

    ia.to_plot()
    timeout.to_plot()

    vip.solve(10, time_step=1)
    assert ia.values[3] == 0


def test_set_interval():
    a = vip.temporal(1)
    ia = vip.integrate(a, 0)

    interval = vip.interval_trigger(2)
    ia.reset_on(interval, 0)

    ia.to_plot()
    interval.to_plot()

    vip.solve(10, time_step=1)

    assert np.all(ia.values[0::2] == 0)
    assert np.allclose(ia.values[1::2], np.full_like(ia.values[1::2], 1))


# TEMPORARILY DELETED. IT WILL BECOME RELEVANT AGAIN WITH STATEFUL VARIABLES

# def test_increment_timeout():
#     count = vip.temporal(0)
#
#     vip.set_timeout(count.action_set_to(count + 1), 2)
#
#     count.to_plot()
#     vip.solve(10, time_step=1)
#
#     assert count.values[0] == 0
#     assert count.values[2] == 1
#     assert count.values[-1] == 1
#
#
# def test_increment_interval():
#     count = vip.temporal(0)
#     vip.set_interval(count.action_set_to(count + 1), 2)
#
#     count.to_plot()
#     vip.solve(10, time_step=1)
#
#     print(count.values)
#     print(count.t)
#
#     assert count.values[0] == 0
#     assert count.values[2] == 1
#     assert count.values[4] == 2
#     assert count.values[6] == 3
#     assert count.values[8] == 4
#     assert count.values[10] == 5


def test_loop_with_delay():
    start = time.time()
    a = vip.loop_node()
    b = a.delayed(1)

    a.loop_into(b + 1)

    # a.to_plot()
    # b.to_plot()

    vip.solve(10, time_step=1)
    print(a.values)
    print(time.time() - start)


def test_state_variable():
    def relay(u, previous_state):
        u_up = 0.5
        u_low = -0.5
        if u > u_up:
            state = 1
        elif u < u_low:
            state = -1
        else:
            state = previous_state
        y = 5 * state
        return y, state

    u = vip.temporal(lambda t: np.sin(t))
    relay_state = vip.loop_node()
    previous_state = relay_state.delayed(1, 1)
    o = vip.f(relay)(u, previous_state)[:]
    y = o[0]
    relay_state.loop_into(o[1])

    u.to_plot()
    relay_state.to_plot()

    vip.solve(10)
