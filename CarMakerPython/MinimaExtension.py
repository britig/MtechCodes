import GPyOpt as gpt
import numpy as np
from numpy.random import seed
import time

import mainPed as cm

start_time = time.time()

# Global Variables Declaration
_bounds_list = []
_epsilon = 5 #50
_iter_count_opt = 20 #0
_iter_count_cutoff = 10
_founded_minima_list = []
_rounding_constant = 1
_omitted_regions = []
# dimension
_dimension = 3

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
		print("The minimum point and value are: " + str(minimum_point) + str(minimum_value))
		# Skip if minimum value very close to zero
		if round(minimum_value) >= 0:
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
				lower_upper_bound_list_left[i]=(left_zero_point, minimum_point[i])

			# left side for i dimension (Region 1)
			zero_list_left = []
			for j in range(0, i):
				zero_list_left.append(dim_zero_points_list[j])
			zero_list_left.append((dimension_bounds[i][0], (left_zero_point-0.1)))
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
			zero_list_right.append(((right_zero_point+0.1), dimension_bounds[i][1]))
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
				print("*******************************************" + str(new_region_list[k][j][0]) + str(new_region_list[k][j][1]))
				if abs(new_region_list[k][j][0] - new_region_list[k][j][1]) < 1:#0.5:
					print("*******************************************>> here 1 :" + str(abs(new_region_list[k][j][0] - new_region_list[k][j][1])) +  str(flag))
					flag = 1
					break
			if fn_check_ommited_regions(new_region_list[k]):
				print("*******************************************>> here 2 : " +str(fn_check_ommited_regions(new_region_list[k])) + " <> "+ str(flag))
				flag = 1
			if flag == 0:
				_bounds_list.append(new_region_list[k])
				print("RegionB : " + str(new_region_list[k]))
				print("*******************************************>> here 3 : " + str(flag))


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
	_bounds_list.append([(40,60), (1,10), (5,20)])
	#_bounds_list.append([(60,60), (0,0), (15, 20)])
	fn_my_controller()
	print(str(_founded_minima_list))
	print("Omitted Regions list===" + str(_omitted_regions))
	print("time elapsed: {:.2f}s".format(time.time() - start_time))

