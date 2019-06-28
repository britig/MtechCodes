import GPyOpt as gpt
import numpy as np
from numpy.random import seed
import time

import mainPed as cm

start_time = time.time()

# Global Variables Declaration
_bounds_list = []
_epsilon = 1 #50
_iter_count_opt = 20 #0
_iter_count_cutoff = 10
_founded_minima_list = []
_rounding_constant = 1
_omitted_regions = []
# dimension
_dimension = 3


# The black box function
def fn_my_black_box_function(parameter_values):
	y = parameter_values[0] * parameter_values[1] * parameter_values[2] *  parameter_values[3] * parameter_values[4] * parameter_values[5] * parameter_values[6] * parameter_values[7] * parameter_values[8] * parameter_values[9]# f(x,y,z) = x*y*z
	# y = -abs(np.sin(parameter_values[0]) * np.cos(parameter_values[1]) * np.exp(abs(1 - (np.sqrt(parameter_values[0] ** 2 + parameter_values[1] ** 2)) / np.pi)))  # HolderTableFunction
	return y


# This is called during actual sampling for finding the global minima
def fn_call_black_box_function_1(bounds):
	parameter_values = []
	for i in range(_dimension):
		parameter_values.append(bounds[0][i])
	result = fn_my_black_box_function(parameter_values)
	return result


# This function is called while finding the nearest point where function becomes zero
# The observation is sent as a square of the function to maintain continuity
def fn_call_black_box_function_2(bounds):
	parameter_values = []
	for i in range(_dimension):
		parameter_values.append(bounds[0][i])
	result = fn_my_black_box_function(parameter_values)
	return result ** 2


# Bayesian Optimization module for finding the global minima within the given bounds
def fn_bayesian_optimization(lower_upper_bound_list):
	global _iter_count_opt
	value_list = []
	for i in range(_dimension):
		dict_value = {'name': 'x' + str(i), 'type': 'continuous',
					  'domain': (lower_upper_bound_list[i][0], lower_upper_bound_list[i][1])}
		value_list.append(dict_value)
	bounds = value_list
	my_problem = gpt.methods.BayesianOptimization(fn_call_black_box_function_1,  # function to optimize
												  bounds,  # box-constraints of the problem
												  acquisition_type='LCB',
												  exact_feval=True)  # Selects the Expected improvement
	max_iter = _iter_count_opt
	max_time = 1000  # time budget
	eps = 10e-10  # Minimum allowed distance between the last two observations

	my_problem.run_optimization(max_iter, max_time, eps)
	new_tup =[]
	statement = ''
	print("Minimum value in Bayesian Optimization"+ str(my_problem.fx_opt))
	return my_problem.x_opt, my_problem.fx_opt


# Bayesian Optimization for finding the cutoff points within the given modules
def fn_find_cutoffs(lower_upper_bound_list, str_side):
	global _iter_count_cutoff
	value_list = []
	for i in range(_dimension):
		dict_value = {'name': 'x' + str(i), 'type': 'continuous',
					  'domain': (lower_upper_bound_list[i][0], lower_upper_bound_list[i][1])}
		value_list.append(dict_value)
	bounds = value_list
	my_problem = gpt.methods.BayesianOptimization(fn_call_black_box_function_2,  # function to optimize
												  bounds,  # box-constraints of the problem
												  acquisition_type='EI',
												  exact_feval=True)  # Selects the Expected improvement
	max_iter = _iter_count_cutoff
	max_time = 1000  # time budget
	eps = 10e-10  # Minimum allowed distance between the last two observations

	my_problem.run_optimization(max_iter, max_time, eps)
	print("Found " + str_side + "th iteration) zero point at parameters===" + str(
		my_problem.x_opt) + "with function values==" + str(my_problem.fx_opt))
	return my_problem.x_opt


def fn_my_controller():
	global _bounds_list, _epsilon, _omitted_regions
	while True:
		print("Stack : (" + str(len(_bounds_list)) + ") >> " + str(_bounds_list))
		if len(_bounds_list) == 0:
			break
		dimension_bounds = _bounds_list[-1]
		del _bounds_list[-1]
		print("Current exploring range : " + str(dimension_bounds))
		minimum_point, minimum_value = cm.fn_bayesian_optimization(dimension_bounds)
		# Skip if minimum value very close to zero
		if round(minimum_value) >= -1:
			# if the least nminimum in a region is 0 then the whole region should be omitted from search space
			_omitted_regions.append(dimension_bounds)
			continue
		statement = ''
		new_tup = []
		for i in range(_dimension):
			new_tup.append(minimum_point[i])
			statement = statement + str(minimum_point[i]) + ','
		new_tup.append(minimum_value)
		_founded_minima_list.append(new_tup)
		print("Found " + str(len(_founded_minima_list)) + "th minimum point====== (" + statement + str(minimum_value) + ")")
		new_region_list = []
		dim_zero_points_list = []
		omitted_list = []
		for i in range(_dimension):
			# Left search for dimension i
			left_zero_point = fn_max((minimum_point[i] - _epsilon), dimension_bounds[i][0])
			left_zero_point_prev = left_zero_point
			count_left = 1
			# create the lower upper bound list where bounds are same for every other dimension except i
			lower_upper_bound_list_left = []
			for j in range(_dimension):
				if j != i:
					lower_upper_bound_list_left.append((minimum_point[j], minimum_point[j]))
				else:
					lower_upper_bound_list_left.append((left_zero_point, minimum_point[j]))
			while True:
				left_zero_point_1 = cm.fn_find_cutoffs(lower_upper_bound_list_left, str('left ' + str(i) + ' (' + str(count_left)))
				left_zero_point = round(left_zero_point_1[i])
				if abs(left_zero_point_prev - left_zero_point) < 0.1 :
					break
				else:
					left_zero_point_prev = left_zero_point
				count_left = count_left + 1
				lower_upper_bound_list_left.append((left_zero_point, minimum_point[i]))

			# left side for i dimension (Region 1)
			zero_list_left = []
			for j in range(0, i):
				zero_list_left.append(dim_zero_points_list[j])
			zero_list_left.append((dimension_bounds[i][0], left_zero_point))
			for j in range(i + 1, _dimension):
				zero_list_left.append((dimension_bounds[j][0], dimension_bounds[j][1]))

			new_region_list.append(zero_list_left)

			# Right search for dimension i
			right_zero_point = fn_min((minimum_point[i] + _epsilon), dimension_bounds[i][1])
			right_zero_point_prev = right_zero_point
			count_right = 1
			lower_upper_bound_list_right = []
			for j in range(_dimension):
				if j != i:
					lower_upper_bound_list_right.append((minimum_point[j], minimum_point[j]))
				else:
					lower_upper_bound_list_right.append((minimum_point[j], right_zero_point))
			while True:
				right_zero_point_1 = cm.fn_find_cutoffs(lower_upper_bound_list_right,
													 str('right ' + str(i) + ' (' + str(count_right)))
				right_zero_point = round(right_zero_point_1[i])
				if abs(right_zero_point_prev - right_zero_point) < 0.1:
					break
				else:
					right_zero_point_prev = right_zero_point
				count_right = count_right + 1
				lower_upper_bound_list_right[i] = (minimum_point[i], right_zero_point)

			# right side for i dimension (Region 1)
			zero_list_right = []
			for j in range(0, i):
				zero_list_right.append(dim_zero_points_list[j])
			zero_list_right.append((right_zero_point, dimension_bounds[i][1]))
			for j in range(i + 1, _dimension):
				zero_list_right.append((dimension_bounds[j][0], dimension_bounds[j][1]))

			new_region_list.append(zero_list_right)
			omitted_list.append((left_zero_point, right_zero_point))
			dim_zero_points_list.append((left_zero_point, right_zero_point))

		print("Region list :" + str(new_region_list))
		_omitted_regions.append(omitted_list)
		# Check if a zero region belongs to omitted list

		for k in range(len(new_region_list)):
			# Region k
			flag = 0
			print("RegionA : " + str(new_region_list[k]))
			for j in range(_dimension):
				if abs(new_region_list[k][j][0] - new_region_list[k][j][1]) < 0.5:
					flag = 1
					break
			if fn_check_ommited_regions(new_region_list[k]):
				flag = 1
			if flag == 0:
				_bounds_list.append(new_region_list[k])
				print("RegionB : " + str(new_region_list[k]))


def fn_max(num1, num2):
	if num1 > num2:
		return num1
	else:
		return num2


def fn_min(num1, num2):
	if num1 < num2:
		return num1
	else:
		return num2


def fn_check_ommited_regions(check_region):
	global _omitted_regions
	_flag = 0
	for region in _omitted_regions:
		_flag = 0
		for i in range(_dimension):
			if round(region[i][0]) <= round(check_region[i][0]) and round(region[i][1]) >= round(check_region[i][1]):
				_flag = 1
			else:
				_flag = 0
				break
		if _flag == 1:
			return True
	return False


if __name__ == '__main__':
	seed(123)
	#_bounds_list.append([(-50, 50), (-50, 50), (-50, 50), (-50, 50), (-50, 50), (-50, 50),(-50, 50),(-50, 50),(-50, 50),(-50, 50)])
	_bounds_list.append([(40,60), (0,10), (15,20)])
	fn_my_controller()
	print(str(_founded_minima_list))
	print("Omitted Regions list===" + str(_omitted_regions))
	print("time elapsed: {:.2f}s".format(time.time() - start_time))
