import juliacall as jc 
jl = jc.newmodule("FrankWolfeModule")
jl.seval("using PythonCall")
jl.seval("using FrankWolfe")
jl.seval("using LinearAlgebra")
jl.seval("using GLPK")
jl.seval("using MathOptInterface")
jl.seval("import MathOptInterface as MOI")