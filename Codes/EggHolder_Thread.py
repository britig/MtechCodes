import _thread
import time
import GPyOpt as gpt
import numpy as np
from numpy.random import seed

# Global Variables Declaration
_bounds_list = []
_x_list = []
_y_list = []
_result_list = []
_epsilon = 100
_iter_count = 10
_delta = 1
_founded_minima_list = []
_x1_lower_range = 0
_x1_upper_range = 512
_x2_lower_range = 0
_x2_upper_range = 512
_explored_ranges = []
_thread_count = 1
#Set the dimension

# The eggholder function
def fn_my_black_box_function(x1, x2):
    y = -(x2 + 47) * np.sin(np.sqrt(abs(x1 / 2.0 + (x2 + 47.0)))) - (x1 * np.sin(np.sqrt(abs(x1 - (x2 + 47.0)))))
    return y


def fn_call_black_box_function_1(bounds):
    global _x_list, _y_list, _result_list
    x1 = bounds[0][0]
    x2 = bounds[0][1]
    _x_list.append(x1)
    _y_list.append(x2)
    result = fn_my_black_box_function(x1, x2)
    _result_list.append(result)
    return result


def fn_call_black_box_function_2(bounds):
    global _x_list, _y_list, _result_list
    x1 = bounds[0][0]
    x2 = bounds[0][1]
    _x_list.append(x1)
    _y_list.append(x2)
    result = fn_my_black_box_function(x1, x2)
    _result_list.append(result)
    return result ** 2


def fn_bayesian_optimizaton(x1_lower_bound, x1_upper_bound, x2_lower_bound, x2_upper_bound):
    global _iter_count
    bounds = [{'name': 'x1', 'type': 'continuous', 'domain': (x1_lower_bound, x1_upper_bound)},
              {'name': 'x2', 'type': 'continuous', 'domain': (x2_lower_bound, x2_upper_bound)}]
    #print("hello1")
    seed(123)
    my_problem = gpt.methods.BayesianOptimization(fn_call_black_box_function_1,  # function to optimize
                                                  bounds,  # box-constraints of the problem
                                                  acquisition_type='EI',
                                                  exact_feval=True)  # Selects the Expected improvement
    max_iter = _iter_count
    max_time = 1000  # time budget
    eps = 10e-10  # Minimum allowed distance between the last two observations

    my_problem.run_optimization(max_iter, max_time, eps)
    _founded_minima_list.append((my_problem.x_opt[0], my_problem.x_opt[1], my_problem.fx_opt))
    print("Found " + str(len(_founded_minima_list)) + "th minimum point at parameters===" + str(my_problem.x_opt) + "with function values==" + str(my_problem.fx_opt))
    return my_problem.x_opt


def fn_find_cutoffs(x1_lower_bound, x1_upper_bound, x2_lower_bound, x2_upper_bound, str_side):
    global _iter_count
    bounds = [{'name': 'x1', 'type': 'continuous', 'domain': (x1_lower_bound, x1_upper_bound)},
              {'name': 'x2', 'type': 'continuous', 'domain': (x2_lower_bound, x2_upper_bound)}]
    #print("hello2")
    seed(123)
    my_problem = gpt.methods.BayesianOptimization(fn_call_black_box_function_2,  # function to optimize
                                                  bounds,  # box-constraints of the problem
                                                  acquisition_type='EI',
                                                  exact_feval=True)  # Selects the Expected improvement
    max_iter = _iter_count
    max_time = 1000  # time budget
    eps = 10e-10  # Minimum allowed distance between the last two observations

    my_problem.run_optimization(max_iter, max_time, eps)
    print("Found Thread : " + str_side + "th iteration) zero point at parameters===" + str(my_problem.x_opt) + "with function values==" + str(my_problem.fx_opt))
    return my_problem.x_opt


def fn_my_controller(ranges):
    global _bounds_list, _x_list, _y_list, _result_list, _epsilon, _iter_count, _delta, _founded_minima_list, _x1_lower_range, _x1_upper_range, _x2_lower_range, _x2_upper_range, _explored_ranges, _thread_count

    _thread_id = _thread_count
    _thread_count = _thread_count + 1
    #for i in range(0, 100):
    #print("Stack : (" + str(len(_bounds_list)) + ") >> " + str(_bounds_list))
    #if len(_bounds_list) == 0:
    #    break
    #x1_x2_bounds = _bounds_list[-1]
    #del _bounds_list[-1]
    x1_bounds = ranges[0]
    x1_lower_bound = x1_bounds[0]
    x1_upper_bound = x1_bounds[1]
    x2_bounds = ranges[1]
    x2_lower_bound = x2_bounds[0]
    x2_upper_bound = x2_bounds[1]
    print("Current exploring range (Thread : " + str(_thread_id) + ") > " + str(ranges))
    minimum_point = fn_bayesian_optimizaton(x1_lower_bound, x1_upper_bound, x2_lower_bound, x2_upper_bound)
    x1_minimum_point = minimum_point[0]
    x2_minimum_point = minimum_point[1]
    #_explored_ranges.append(ranges)

    # left zero point
    left_zero_point = [fn_max((x1_minimum_point - _epsilon), x1_lower_bound), fn_max((x2_minimum_point - _epsilon), x2_lower_bound)]
    left_zero_point_prev = left_zero_point
    count_1 = 1
    while(True):
        left_zero_point = fn_find_cutoffs(left_zero_point[0], x1_minimum_point, left_zero_point[1], x2_minimum_point, str(str(_thread_id) +' > left ('+str(count_1)))
        if(round(left_zero_point_prev[0], 2) == round(left_zero_point[0], 2) and round(left_zero_point_prev[1], 2) == round(left_zero_point[1], 2)):
            break
        else:
            left_zero_point_prev = left_zero_point
        count_1 = count_1 + 1
    # left side
    new_x1_bounds_1 = (x1_lower_bound, left_zero_point[0])
    new_x2_bounds_1 = (x2_lower_bound, left_zero_point[1])

    # right zero point
    right_zero_point = [fn_min((x1_minimum_point + _epsilon), x1_upper_bound), fn_min((x2_minimum_point + _epsilon), x2_upper_bound)]
    right_zero_point_prev = right_zero_point
    count_2 = 1
    while(True):
        right_zero_point = fn_find_cutoffs(x1_minimum_point, right_zero_point[0], x2_minimum_point, right_zero_point[1], str(str(_thread_id) +' > right ('+str(count_2)))
        if(round(right_zero_point_prev[0], 2) == round(right_zero_point[0], 2) and round(right_zero_point_prev[1], 2) == round(right_zero_point[1], 2)):
            break
        else:
            right_zero_point_prev = right_zero_point
        count_2 = count_2 + 1

    # right side
    new_x1_bounds_2 = (right_zero_point[0], x1_upper_bound)
    new_x2_bounds_2 = (right_zero_point[1], x2_upper_bound)

    flag_1 = 0
    flag_2 = 0
    for ranges in _explored_ranges:
        explored_ranges_x1_bounds = ranges[0]
        explored_ranges_x1_lower_bound = explored_ranges_x1_bounds[0]
        explored_ranges_x1_upper_bound = explored_ranges_x1_bounds[1]
        explored_ranges_x2_bounds = ranges[1]
        explored_ranges_x2_lower_bound = explored_ranges_x2_bounds[0]
        explored_ranges_x2_upper_bound = explored_ranges_x2_bounds[1]
        if (round(explored_ranges_x1_lower_bound, 2) == round(new_x1_bounds_1[0], 2) and round(explored_ranges_x1_upper_bound, 2) == round(new_x1_bounds_1[1], 2) and round(explored_ranges_x2_lower_bound, 2) == round(new_x2_bounds_1[0], 2) and round(explored_ranges_x2_upper_bound, 2) == round(new_x2_bounds_1[1], 2)):
           flag_1 = 1

        if (round(explored_ranges_x1_lower_bound, 2) == round(new_x1_bounds_2[0], 2) and round(explored_ranges_x1_upper_bound, 2) == round(new_x1_bounds_2[1], 2) and round(explored_ranges_x2_lower_bound, 2) == round(new_x2_bounds_2[0], 2) and round(explored_ranges_x2_upper_bound, 2) == round(new_x2_bounds_2[1], 2)):
            flag_2 = 1

    if flag_1 == 0:
        #_bounds_list.append([new_x1_bounds_1, new_x2_bounds_1])
        try:
            _thread.start_new_thread(fn_my_controller, ([new_x1_bounds_1, new_x2_bounds_1], ))
            _explored_ranges.append([new_x1_bounds_1, new_x2_bounds_1])
        except:
            pass
    if flag_2 == 0:
        #_bounds_list.append([new_x1_bounds_2, new_x2_bounds_2])
        try:
            _thread.start_new_thread(fn_my_controller, ([new_x1_bounds_2, new_x2_bounds_2], ))
            _explored_ranges.append([new_x1_bounds_2, new_x2_bounds_2])
        except:
            pass
    if _thread_id == 1:
        while(True):
            time.sleep(100)
            print("** I'm Main **")


def fn_max(num1, num2):
    if(num1>num2):
        return num1
    else:
        return num2

def fn_min(num1, num2):
    if(num1<num2):
        return num1
    else:
        return num2


if __name__ == '__main__':
    #_bounds_list.append([(_x1_lower_range, _x1_upper_range), (_x2_lower_range, _x2_upper_range)])
    _explored_ranges.append([(_x1_lower_range, _x1_upper_range), (_x2_lower_range, _x2_upper_range)])
    fn_my_controller([(_x1_lower_range, _x1_upper_range), (_x2_lower_range, _x2_upper_range)])
