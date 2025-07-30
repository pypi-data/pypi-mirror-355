from ._julia_env import jl

def wrap_objective_function(f):
    """
    Wraps a Python objective function to be compatible with FrankWolfe.jl functions
    """
    return jl.seval("f -> (x -> pyconvert(Float64, f(x)))")(f)

    