# Extended Capacity Warehouse Location Problem

This repository contains multiple approaches (Mixed Integer Programming, Constraint Programming) to solve the Capacitated Warehouse Location Problem using:
- OR-Tools (CBC solver, CP-SAT solver)
- DOcplex (CPLEX solver) 
- Python scripts for data management and solver integrations

## Folder Structure

- **OR-tools_MIP_CP/**
  - MIP_V5.py: Mixed Integer Programming with OR-Tools
  - CP_V5.py: Constraint programming with OR-Tools CP-SAT

  It is possible to enable or disable only these 3 constraints: `minimum_capacity_usage`, `prohibited_pairs`, and `dependent_warehouses`.
  Ensure that all data directories used in the code are configured to point to the data folder within the project directory.

- **DOcplex_MIP_CP/**
  - cplex_MIP_model.py: Mixed Integer Programming with DOcplex
  - cplex_CP_model.py: Constraint programming with DOcplex CP
    
  Ensure that all data directories used in the code are configured to point to the data folder within the project directory.

- **DataManagementScripts/**
  - python_code_map_file.py: Data mapping utilities
  - read_data_V2.py: Data file parsing functions

- **data/**
  - facility_location_41.dat
  - facility_location_44.dat
  - facility_location_51.dat
  - facility_location_92.dat
  - facility_location_93.dat
  - facility_location_123.dat
  - facility_location_124.dat
  - facility_location_133.dat

- **extra/scripts_ibm_ilog_cplex/**
  - wh_constraint_programming.txt: CP model definition
  - wh_programacao_linear.txt: MIP model definition  
  - wh_ficheiro_dados.txt: Example data file format
  - Note: Initial examples in ibm_ilog_cplex
## Data Files
The data files in the `data/` directory contain:
- Number of warehouses and customers
- Fixed costs for opening warehouses
- Warehouse capacities
- Customer demands 
- Transportation costs
- Prohibited pairs
- Dependent warehouses


## Results
Results comparing CP vs MIP approaches are stored in Results_CP_vs_MIP.xlsx

## Report
Final Report: Extended_Capacity_Warehouse_Location_Report.pdf

## Presentation
Final presentation

## Contributors
- [@jcns1107](https://github.com/jcns1107)
- [@ghostcat-pro](https://github.com/ghostcat-pro)
