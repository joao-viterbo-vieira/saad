# Capacitated Warehouse Location Project

This repository contains multiple approaches (Linear Programming, Constraint Programming) to solve the Capacitated Warehouse Location Problem using:
- OR-Tools (CBC solver)
- DOcplex (CPLEX solver) 
- Python scripts for data management and solver integrations

## Folder Structure

- **OR-tools_LP_CP/**
  - LP_V5.py: Linear optimization with OR-Tools
  - CP_V5.py: Constraint programming with OR-Tools CP-SAT

- **DOcplex_LP_CP/**
  - cplex_LP_model.py: Linear optimization with DOcplex
  - cplex_CP_model.py: Constraint programming with DOcplex CP

- **DataManagementScripts/**
  - python_code_map_file.py: Data mapping utilities
  - read_data_V2.py: Data file parsing functions

- **.dat/**
  - cap44.dat, cap92.dat, cap93.dat, cap123.dat, cap124.dat, cap133.dat: Test instances

- **scripts_ibm_ilog_cplex/**
  - wh_constraint_programming.txt: CP model definition
  - wh_programacao_linear.txt: LP model definition  
  - wh_ficheiro_dados.txt: Example data file format

## Data Files
The data files in the `.dat/` directory contain:
- Number of warehouses and customers
- Fixed costs for opening warehouses
- Warehouse capacities
- Customer demands 
- Transportation costs

## Results
Results comparing CP vs LP approaches are stored in Results_CP_vs_LP.xlsx
