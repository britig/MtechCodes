# from mpl_toolkits import mplot3d
# import GPy
import GPyOpt
import numpy as np
from numpy.random import seed

# import matplotlib
# import matplotlib.cm as cm
# import matplotlib.pyplot as plt

x_list = []
y_list = []
result_list = []


# Function definition of minimizing distance
# The eggholder function
def my_f(x1, x2):
    y = -(x2 + 47) * np.sin(np.sqrt(abs(x1 / 2.0 + (x2 + 47.0)))) - (x1 * np.sin(np.sqrt(abs(x1 - (x2 + 47.0)))))
    return y


def call(bounds):
    global x_list, y_list, result_list
    x1 = bounds[0][0]
    x2 = bounds[0][1]
    x_list.append(x1)
    y_list.append(x2)
    res = my_f(x1, x2)
    result_list.append(res)
    return res


def call_cutoff(bounds):
    global x_list, y_list, result_list
    x1 = bounds[0][0]
    x2 = bounds[0][1]
    x_list.append(x1)
    y_list.append(x2)
    res = my_f(x1, x2)
    result_list.append(res)
    return res**2


def bayesian_optimisation_module(lower_bound1, upper_bound1, lower_bound2, upper_bound2, iter_count):
    bounds = [{'name': 'x1', 'type': 'continuous', 'domain': (lower_bound1, upper_bound1)},
              {'name': 'x2', 'type': 'continuous', 'domain': (lower_bound2, upper_bound2)}]
    print("hello2")
    seed(123)
    my_problem = GPyOpt.methods.BayesianOptimization(call,  # function to optimize
                                                     bounds,  # box-constraints of the problem
                                                     acquisition_type='EI',
                                                     exact_feval=True)  # Selects the Expected improvement
    max_iter = iter_count
    max_time = 1000  # time budget
    eps = 10e-10  # Minimum allowed distance between the last two observations

    my_problem.run_optimization(max_iter, max_time, eps)
    print("Found counterexample at parameters===" + str(my_problem.x_opt) + "with function values==" + str(my_problem.fx_opt))
    param_val = my_problem.x_opt
    param1 = param_val[0]
    param2 = param_val[1]
    search_cutoff(100, param1, param2)


def search_cutoff(epsilon, x1, x2):
    bounds_lower = [{'name': 'x1', 'type': 'continuous', 'domain': (x1 - epsilon, x1)},
                    {'name': 'x2', 'type': 'continuous', 'domain': (x2 - epsilon, x2)}]
    seed(123)
    max_iter = 50
    max_time = 1000  # time budget
    eps = 10e-10  # Minimum allowed distance between the last two observations
    my_problem_lower = GPyOpt.methods.BayesianOptimization(call_cutoff,  # function to optimize
                                                          bounds_lower,  # box-constraints of the problem
                                                          acquisition_type='EI',
                                                          exact_feval=True)  # Selects the Expected improvement
    my_problem_lower.run_optimization(max_iter, max_time, eps)
    print('Lower Bound Found At===' + str(my_problem_lower.x_opt) + 'with function value==' + str(my_problem_lower.fx_opt))
    param_val_lower = my_problem_lower.x_opt
    param_lower1 = param_val_lower[0]
    param_lower2 = param_val_lower[1]

    bounds_higher = [{'name': 'x1', 'type': 'continuous', 'domain': (x1, x1 + epsilon)},
                    {'name': 'x2', 'type': 'continuous', 'domain': (x2, x2 + epsilon)}]

    my_problem_higher = GPyOpt.methods.BayesianOptimization(call_cutoff,  # function to optimize
                                                           bounds_higher,  # box-constraints of the problem
                                                           acquisition_type='EI',
                                                           exact_feval=True)  # Selects the Expected improvement
    my_problem_higher.run_optimization(max_iter, max_time, eps)
    print('Higher Bound Found At===' + str(my_problem_higher.x_opt) + 'with function value==' + str(my_problem_higher.fx_opt))
    param_val_higher = my_problem_higher.x_opt
    param_higher1 = param_val_higher[0]
    param_higher2 = param_val_higher[1]
    bayesian_optimisation_module(0, param_lower1, 0, param_lower2, 200)
    bayesian_optimisation_module(0, param_higher1, 0, param_higher1, 200)


# Main entry point
if __name__ == "__main__":
    # First parameter value
    print("hello")
    bayesian_optimisation_module(0, 512, 0, 512, 100)
