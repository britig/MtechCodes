import GPyOpt as gpt
import numpy as np
from numpy.random import seed

# Global Variables Declaration
_bounds_list = []
_x_list = []
_y_list = []
_result_list = []
_epsilon = 2
_iter_count_opt = 10
_iter_count_cutoff = 10
#_delta = 1
_founded_minima_list = []
_x1_lower_range = -10
_x1_upper_range = 10
_x2_lower_range = -10
_x2_upper_range = 10
_rounding_constant = 1
_omitted_regions = []


# The EggHolder function treated as black box function
def fn_my_black_box_function(x1, x2):
    y = -abs(np.sin(x1)*np.cos(x2)*np.exp(abs(1-(np.sqrt(x1**2+x2**2))/np.pi)))#-(x2 + 47) * np.sin(np.sqrt(abs(x1 / 2.0 + (x2 + 47.0)))) - (x1 * np.sin(np.sqrt(abs(x1 - (x2 + 47.0)))))
    return y


#This is called during actual sampling for finding the global minima
def fn_call_black_box_function_1(bounds):
    global _x_list, _y_list, _result_list
    x1 = bounds[0][0]
    x2 = bounds[0][1]
    _x_list.append(x1)
    _y_list.append(x2)
    result = fn_my_black_box_function(x1, x2)
    _result_list.append(result)
    return result

#This function is called while finding the point where function becomes zero
#The observation is sent as a square of the function to maintain continuity
def fn_call_black_box_function_2(bounds):
    global _x_list, _y_list, _result_list
    x1 = bounds[0][0]
    x2 = bounds[0][1]
    _x_list.append(x1)
    _y_list.append(x2)
    result = fn_my_black_box_function(x1, x2)
    _result_list.append(result)
    return result ** 2

#Bayesian Optimization module for finding the global minima within the given bounds
def fn_bayesian_optimizaton(x1_lower_bound, x1_upper_bound, x2_lower_bound, x2_upper_bound):
    global _iter_count_opt
    bounds = [{'name': 'x1', 'type': 'continuous', 'domain': (x1_lower_bound, x1_upper_bound)},
              {'name': 'x2', 'type': 'continuous', 'domain': (x2_lower_bound, x2_upper_bound)}]
    # print("hello1")
    seed(123)
    my_problem = gpt.methods.BayesianOptimization(fn_call_black_box_function_1,  # function to optimize
                                                  bounds,  # box-constraints of the problem
                                                  acquisition_type='EI',
                                                  exact_feval=True)  # Selects the Expected improvement
    max_iter = _iter_count_opt
    max_time = 1000  # time budget
    eps = 10e-10  # Minimum allowed distance between the last two observations

    my_problem.run_optimization(max_iter, max_time, eps)
    _founded_minima_list.append((my_problem.x_opt[0], my_problem.x_opt[1], my_problem.fx_opt))
    #print("Found " + str(len(_founded_minima_list)) + "th minimum point at parameters===" + str(my_problem.x_opt) + "with function values==" + str(my_problem.fx_opt))
    print("Found " + str(len(_founded_minima_list)) + "th minimum point====== (" + str(my_problem.x_opt[0]) + "," + str(my_problem.x_opt[1]) + "," + str(my_problem.fx_opt) + ")")
    return my_problem.x_opt, my_problem.fx_opt

#Bayesian Optimization for finding the cutoff points within the given modules
def fn_find_cutoffs(x1_lower_bound, x1_upper_bound, x2_lower_bound, x2_upper_bound, str_side):
    global _iter_count_cutoff
    bounds = [{'name': 'x1', 'type': 'continuous', 'domain': (x1_lower_bound, x1_upper_bound)},
              {'name': 'x2', 'type': 'continuous', 'domain': (x2_lower_bound, x2_upper_bound)}]
    # print("hello2")
    seed(123)
    my_problem = gpt.methods.BayesianOptimization(fn_call_black_box_function_2,  # function to optimize
                                                  bounds,  # box-constraints of the problem
                                                  acquisition_type='EI',
                                                  exact_feval=True)  # Selects the Expected improvement
    max_iter = _iter_count_cutoff
    max_time = 1000  # time budget
    eps = 10e-10  # Minimum allowed distance between the last two observations

    my_problem.run_optimization(max_iter, max_time, eps)
    print("Found " + str_side + "th iteration) zero point at parameters===" + str(my_problem.x_opt) + "with function values==" + str(my_problem.fx_opt))
    return my_problem.x_opt


def fn_my_controller():
    global _bounds_list, _epsilon, _omitted_regions
    while (True):
        print("Stack : (" + str(len(_bounds_list)) + ") >> " + str(_bounds_list))
        if len(_bounds_list) == 0:
            break
        x1_x2_bounds = _bounds_list[-1]
        del _bounds_list[-1]
        x1_bounds = x1_x2_bounds[0]
        x1_lower_bound = x1_bounds[0]
        x1_upper_bound = x1_bounds[1]
        x2_bounds = x1_x2_bounds[1]
        x2_lower_bound = x2_bounds[0]
        x2_upper_bound = x2_bounds[1]
        print("Current exploring range : " + str(x1_x2_bounds))
        minimum_point, minimum_value = fn_bayesian_optimizaton(x1_lower_bound, x1_upper_bound, x2_lower_bound, x2_upper_bound)
        if round(minimum_value, 0) >= 0:
            continue
        x1_minimum_point = minimum_point[0]
        x2_minimum_point = minimum_point[1]
        # _explored_ranges.append(x1_x2_bounds)

        # left zero point keeping x2 constant
        left_zero_x1_point = fn_max((x1_minimum_point - _epsilon), x1_lower_bound)
        left_zero_x1_point_prev = left_zero_x1_point
        count_left_x1 = 1
        # Left search for x1
        while (True):
            left_zero_point_1 = fn_find_cutoffs(left_zero_x1_point, x1_minimum_point, x2_minimum_point,
                                                x2_minimum_point, str('left x1 (' + str(count_left_x1)))
            left_zero_x1_point = left_zero_point_1[0]
            if (round(left_zero_x1_point_prev, _rounding_constant) == round(left_zero_x1_point, _rounding_constant)):
                break
            else:
                left_zero_x1_point_prev = left_zero_x1_point
            count_left_x1 = count_left_x1 + 1
        # left side for x1 (Region 1)
        new_x1_bounds_1 = (x1_lower_bound, left_zero_x1_point)
        new_x2_bounds_1 = (x2_lower_bound, x2_upper_bound)

        # left zero point keeping x1 constant
        down_zero_x2_point = fn_max((x2_minimum_point - _epsilon), x2_lower_bound)
        down_zero_x2_point_prev = down_zero_x2_point
        count_left_x2 = 1
        # Left search for x2
        while (True):
            down_zero_point_2 = fn_find_cutoffs(x1_minimum_point, x1_minimum_point, down_zero_x2_point,
                                                x2_minimum_point, str('left x2 (' + str(count_left_x2)))
            down_zero_x2_point = down_zero_point_2[1]
            if (round(down_zero_x2_point_prev, _rounding_constant) == round(down_zero_x2_point, _rounding_constant)):
                break
            else:
                down_zero_x2_point_prev = down_zero_x2_point
                count_left_x2 = count_left_x2 + 1
        # left side for x2 (Region 2)
        new_x1_bounds_2 = (left_zero_x1_point, x1_upper_bound)
        new_x2_bounds_2 = (x2_lower_bound, down_zero_x2_point)

        # right zero point keeping x2 constant
        right_zero_x1_point = fn_min((x1_minimum_point + _epsilon), x1_upper_bound)
        right_zero_x1_point_prev = right_zero_x1_point
        count_right_x1 = 1
        while (True):
            right_zero_point_1 = fn_find_cutoffs(x1_minimum_point, right_zero_x1_point, x2_minimum_point,
                                                 x2_minimum_point, str('right x1 (' + str(count_right_x1)))
            right_zero_x1_point = right_zero_point_1[0]
            if (round(right_zero_x1_point_prev, _rounding_constant) == round(right_zero_x1_point, _rounding_constant)):
                break
            else:
                right_zero_x1_point_prev = right_zero_x1_point
            count_right_x1 = count_right_x1 + 1
        # right side for x1 (Region 3)
        new_x1_bounds_3 = (right_zero_x1_point, x1_upper_bound)
        new_x2_bounds_3 = (down_zero_x2_point, x2_upper_bound)

        # right zero point keeping x2 constant
        top_zero_x2_point = fn_min((x2_minimum_point + _epsilon), x2_upper_bound)
        top_zero_x2_point_prev = top_zero_x2_point
        count_right_x2 = 1
        while (True):
            right_zero_point_2 = fn_find_cutoffs(x1_minimum_point, x1_minimum_point, x2_minimum_point,
                                                 top_zero_x2_point, str('right x2 (' + str(count_right_x2)))
            top_zero_x2_point = right_zero_point_2[1]
            if (round(top_zero_x2_point_prev, _rounding_constant) == round(top_zero_x2_point, _rounding_constant)):
                break
            else:
                top_zero_x2_point_prev = top_zero_x2_point
                count_right_x2 = count_right_x2 + 1
        # right side for x2 (Region 4)
        new_x1_bounds_4 = (left_zero_x1_point, right_zero_x1_point)
        new_x2_bounds_4 = (top_zero_x2_point, x2_upper_bound)

        #print([new_x1_bounds_1, new_x2_bounds_1])

        #Region 1
        print("1a : " + str([new_x1_bounds_1, new_x2_bounds_1]))
        #Line Check and Region Check
        if (round(new_x1_bounds_1[0]) != round(new_x1_bounds_1[1])) and (round(new_x2_bounds_1[0]) != round(new_x2_bounds_1[1])) \
                and (not(fn_check_ommited_regions([new_x1_bounds_1[0], new_x1_bounds_1[1], new_x2_bounds_1[0], new_x2_bounds_1[1]]))):
            _bounds_list.append([new_x1_bounds_1, new_x2_bounds_1])
            print("1b : " + str([new_x1_bounds_1, new_x2_bounds_1]))


        #Region 2
        print("2a : " + str([new_x1_bounds_2, new_x2_bounds_2]))
        if (round(new_x1_bounds_2[0]) != round(new_x1_bounds_2[1])) and (round(new_x2_bounds_2[0]) != round(new_x2_bounds_2[1])) \
                and (not(fn_check_ommited_regions([new_x1_bounds_2[0], new_x1_bounds_2[1], new_x2_bounds_2[0], new_x2_bounds_2[1]]))):
            _bounds_list.append([new_x1_bounds_2, new_x2_bounds_2])
            print("2b : " + str([new_x1_bounds_2, new_x2_bounds_2]))

        #Region 3
        print("3a : " + str([new_x1_bounds_3, new_x2_bounds_3]))
        if (round(new_x1_bounds_3[0]) != round(new_x1_bounds_3[1])) and (round(new_x2_bounds_3[0]) != round(new_x2_bounds_3[1])) \
                and (not(fn_check_ommited_regions([new_x1_bounds_3[0], new_x1_bounds_3[1], new_x2_bounds_3[0], new_x2_bounds_3[1]]))):
            _bounds_list.append([new_x1_bounds_3, new_x2_bounds_3])
            print("3b : " + str([new_x1_bounds_3, new_x2_bounds_3]))


        #Region 4
        print("4a : " + str([new_x1_bounds_4, new_x2_bounds_4]))
        if (round(new_x1_bounds_4[0]) != round(new_x1_bounds_4[1])) and (round(new_x2_bounds_4[0]) != round(new_x2_bounds_4[1])) \
                and (not (fn_check_ommited_regions([new_x1_bounds_4[0], new_x1_bounds_4[1], new_x2_bounds_4[0], new_x2_bounds_4[1]]))):
            _bounds_list.append([new_x1_bounds_4, new_x2_bounds_4])
            print("4b : " + str([new_x1_bounds_4, new_x2_bounds_4]))

        #print("Stack 2 : (" + str(len(_bounds_list)) + ") >> " + str(_bounds_list))
        _omitted_regions.append([left_zero_x1_point, right_zero_x1_point, down_zero_x2_point, top_zero_x2_point])
        #print("Ommitted Regions list==="+str(_omitted_regions))


def fn_max(num1, num2):
    if (num1 > num2):
        return num1
    else:
        return num2


def fn_min(num1, num2):
    if (num1 < num2):
        return num1
    else:
        return num2


def fn_check_ommited_regions(check_region):
    global _omitted_regions
    for region in _omitted_regions:
        region_point_1 = region[0]
        region_point_2 = region[1]
        region_point_3 = region[2]
        region_point_4 = region[3]

        check_region_point_1 = check_region[0]
        check_region_point_2 = check_region[1]
        check_region_point_3 = check_region[2]
        check_region_point_4 = check_region[3]


        if      (round(region_point_1) <= round(check_region_point_1) \
                #and round(region_point_2) >= round(check_region_point_1) \
                #and round(region_point_1) <= round(check_region_point_2) \
                and round(region_point_2) >= round(check_region_point_2) \
                and round(region_point_3) <= round(check_region_point_3) \
                #and round(region_point_4) >= round(check_region_point_3) \
                #and round(region_point_3) <= round(check_region_point_4) \
                and round(region_point_4) >= round(check_region_point_4)) :
            return True

    return False


if __name__ == '__main__':
    _bounds_list.append([(_x1_lower_range, _x1_upper_range), (_x2_lower_range, _x2_upper_range)])
    fn_my_controller()
    print(str(_founded_minima_list))
    print("Ommitted Regions list===" + str(_omitted_regions))
