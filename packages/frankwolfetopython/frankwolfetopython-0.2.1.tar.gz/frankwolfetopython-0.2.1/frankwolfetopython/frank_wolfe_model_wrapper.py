"""
Python wrapper for FrankWolfe.jl
Provides a Pythonic interface to the Julia FrankWolfe optimization package.
"""

# TODO: Add support for manually setting initial point
# TODO: Add supprot for more lmos, and perhaps combine set_custom_lmo and set_lmo
# TODO: Add text for each function
# TODO: Add support for more line searches
# TODO: Make code more robust with better error handling
# TODO: Fix __str__ (make it better)
# TODO: Add necessary magic methods (__repr__, __eq__, etc.)
# TODO: Make it so if user calls solve after solving, it returns the same solution and doesn't recompute.
# TODO: Check gradient function for correctness when the user passes a non-inplace gradient funciton.

import numpy as np
import juliacall as jc
from typing import Callable, Union, Dict, Any, Tuple, List
import warnings

class FrankWolfeWrapper:
    """
    Python wrapper for FrankWolfe.jl
    """
    def __init__(self, name: str):
        self.jl = jc.newmodule("FrankWolfeWrapper")
        self.jl.seval("using FrankWolfe")
        self.jl.seval("using PythonCall")
        self.jl.seval("using LinearAlgebra")

        self.name = name

        self.__params = {
            "objective_function": None,
            "gradient": None,
            "lmo": None,
            "x0": None,
            "line_search": self.jl.FrankWolfe.Adaptive(),
            "max_iteration": 1000}
        
        self.__wrapped_functions = {}

        self.__run_history = {}

    @classmethod
    def model(cls, *args, **kwargs):
        """
        Factory method for creating a new FrankWolfeWrapper instance
        """
        return cls(*args, **kwargs)

    def __str__(self):
        """
        Returns a string representation of the model, including its name and parameters
        """
        return f"Model name: {self.name}\nModel parameters: {self.__params}"

    def set_lmo(self, lmo_type: str, *args, **kwargs):
        """
        Sets the Linear Minimization Oracle (LMO) for the optimization problem using built-in LMOs from FrankWolfe.jl
        """
        supported_lmos = { 
            "probability_simplex": self.jl.FrankWolfe.ProbabilitySimplexOracle
            } 
        if lmo_type not in supported_lmos:
            raise ValueError(f"Unsupported LMO type: {lmo_type}. Supported types: {list(supported_lmos.keys())}")
        
        self.__params["lmo"] = supported_lmos[lmo_type](*args, **kwargs)

    def set_line_search(self, line_search_type: str):
        """
        Sets the line search method for the optimization problem using built-in line search methods from FrankWolfe.jl
        """
        line_search_map = {
            "adaptive": self.jl.FrankWolfe.Adaptive(),
            "backtracking": self.jl.FrankWolfe.Backtracking()
        }

        if line_search_type not in line_search_map:
            warnings.warn(f"Line search type '{line_search_type}' not recognized. Defaulting to 'adaptive'.")
            self.__params["line_search"] = line_search_map["adaptive"]
        else:
            self.__params["line_search"] = line_search_map[line_search_type]

    def __compute_extreme_point(self, direction: np.ndarray):
        """
        Computes the extreme point for the given direction using the LMO
        """
        return self.jl.FrankWolfe.compute_extreme_point(
            self.__params["lmo"],
            direction)

    def set_initial_point(self, direction: np.ndarray):
        """
        Sets the initial point for the optimization problem
        """
        self.__params["x0"] = self.__compute_extreme_point(direction)

    def __wrap_objective_function(self, f: Callable) -> Any:
        func_id = id(f)
        if func_id not in self.__wrapped_functions:
            self.__wrapped_functions[func_id] = self.jl.seval(
                "f -> (x -> pyconvert(Float64, f(x)))")(f)
        self.__params["objective_function"] = self.__wrapped_functions[func_id]

        return self.__wrapped_functions[func_id]
    
    def set_objective(self, expression: Callable):
        """
        Sets the objective function for the optimization problem
        """
        self.__params["objective_function"] = self.__wrap_objective_function(expression)

    def set_gradient(self, expression: Callable):
        """
        Sets the gradient function for the optimization problem; accepts either a function g(x) -> grad or g(storage, x)
        """
        import inspect

        sig = inspect.signature(expression)
        if len(sig.parameters) == 1:
            def in_place_grad(storage, x):
                storage[:] = expression(x)
            self.__params["gradient"] = in_place_grad
        else:
            self.__params["gradient"] = expression
    
    def set_max_iteration(self, max_iteration: int):
        """
        Sets the maximum number of iterations for the optimization problem
        """
        self.__params["max_iteration"] = max_iteration

    def set_custom_lmo(self, constraints: List[Tuple[np.ndarray, np.ndarray, str]]):
        """
        Sets a custom Linear Minimization Oracle (LMO) for the optimization problem with user-defined linear constraints
        """
        self.jl.seval("using MathOptInterface")
        self.jl.seval("import MathOptInterface")
        self.jl.seval("MOI = MathOptInterface")
        self.jl.seval("using GLPK")
        script = "optimizer = GLPK.Optimizer()\n"

        for idx, (A, b, sense) in enumerate(constraints):
            if not isinstance(A, np.ndarray) or not isinstance(b, np.ndarray):
                raise ValueError("A and b must be numpy arrays.")
            if A.ndim != 2 or b.ndim != 1:
                raise ValueError("A must be 2D, b must be 1D.")
            if A.shape[0] != b.shape[0]:
                raise ValueError("Rows of A must match length of b.")
            
            n_vars = A.shape[1]
            n_cons = A.shape[0]
            A = A.astype(float)
            b = b.astype(float)
            A_jl = "[" + "; ".join(" ".join(str(A[i, j]) for j in range(n_vars)) for i in range(n_cons)) + "]"
            b_jl = "[" + "; ".join(str(bi) for bi in b) + "]"

            if sense == "leq":
                constr_type = "MOI.LessThan"
            elif sense == "eq":
                constr_type = "MOI.EqualTo"
            elif sense == "geq":
                constr_type = "MOI.GreaterThan"
            else:
                raise ValueError("sense must be 'leq', 'eq', or 'geq'")
            
            # Add variables only once
            if idx == 0:
                script += f"x = MOI.add_variables(optimizer, {n_vars})\n"
            script += f"A = {A_jl}\n"
            script += f"b = {b_jl}\n"
            script += f"for i in 1:{n_cons}\n"
            script += f"    MOI.add_constraint(optimizer, MOI.ScalarAffineFunction(MOI.ScalarAffineTerm.(A[i, :], x), 0.0), {constr_type}(b[i]))\n"
            script += "end\n"

        self.jl.seval(script)
        self.__params["lmo"] = self.jl.FrankWolfe.MathOptLMO(self.jl.optimizer)

    def solve(self, verbose=False, epsilon=1e-8, **kwargs) -> Dict[str, Any]:
        """
        Solves the optimization problem using the Frank-Wolfe algorithm
        """
        supported_functions = {self.jl.frank_wolfe}

        return self.jl.frank_wolfe(
            self.__params["objective_function"], 
            self.__params["gradient"], 
            self.__params["lmo"],
            self.__params["x0"], 
            line_search=self.__params["line_search"],
            max_iteration=self.__params["max_iteration"],
            epsilon=epsilon,
            verbose=verbose
        )
    
    ### Add functionality for additional frank wolfe methods (blended conditional pairwise gradient)

# quadratic interface

# final boss: conic interface



