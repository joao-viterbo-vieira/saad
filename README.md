
# Capacitated Warehouse Location Project

This repository contains multiple approaches (Linear Programming, Constraint Programming) to solve the Capacitated Warehouse Location Problem using:
- OR-Tools (CBC solver)
- DOcplex (CPLEX solver)
- Python scripts showing different solver integrations and constraints

## Folder Structure

- **V4/**  
  - LP_V4.py: Linear optimization with OR-Tools.  
  - CP_V4.py: Constraint programming with OR-Tools CP-SAT.

- **cplex/**  
  - cplex_LP_model.py: Linear optimization with the DOcplex library.  
  - cplex_CP_model.py: Constraint programming with DOcplex CP.

- **wh_ficheiro_dados.txt**  
  Example data file containing parameters: number of warehouses/customers, fixed costs, capacities, demands, and transport costs.
