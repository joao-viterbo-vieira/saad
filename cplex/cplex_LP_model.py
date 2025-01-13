import re
import ast
from docplex.mp.model import Model


def read_data_file(filename):
    """
    Lê o ficheiro de dados do problema (ex.: facility_location.dat) e devolve
    nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost,
    prohibited_pairs e dependent_warehouses.
    """
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # 1) Extrair nWarehouses
    nWarehouses_match = re.search(r"nWarehouses\s*=\s*(\d+)\s*;", content)
    nWarehouses = int(nWarehouses_match.group(1))

    # 2) Extrair nCustomers
    nCustomers_match = re.search(r"nCustomers\s*=\s*(\d+)\s*;", content)
    nCustomers = int(nCustomers_match.group(1))

    # 3) Extrair fixedCost como lista de floats
    fixedCost_match = re.search(r"fixedCost\s*=\s*\[(.*?)\];", content, re.DOTALL)
    fixedCost_str = fixedCost_match.group(1)
    fixedCost = [float(x) for x in fixedCost_str.replace("\n", "").split(",")]

    # 4) Extrair capacity
    capacity_match = re.search(r"capacity\s*=\s*\[(.*?)\];", content, re.DOTALL)
    capacity_str = capacity_match.group(1)
    capacity = [float(x) for x in capacity_str.replace("\n", "").split(",")]

    # 5) Extrair demand
    demand_match = re.search(r"demand\s*=\s*\[(.*?)\];", content, re.DOTALL)
    demand_str = demand_match.group(1)
    demand = [float(x) for x in demand_str.replace("\n", "").split(",")]

    # 6) Extrair transportCost (matriz)
    transportCost_match = re.search(
        r"transportCost\s*=\s*\[(.*?)\];", content, re.DOTALL
    )
    transportCost_str = transportCost_match.group(1).strip()

    # Ajustes para ficar num formato Python
    transportCost_str = "[" + transportCost_str + "]"
    transportCost_str = transportCost_str.replace(";", "")
    transportCost = ast.literal_eval(transportCost_str)

    # 7) Extrair prohibited_pairs
    #    Note que no seu txt o prohibited_pairs aparece em formato: prohibited_pairs = [(1, 2), (3, 4), ...]
    #    Faremos o parse buscando o trecho entre colchetes.
    prohibited_pairs = []
    pp_match = re.search(r"prohibited_pairs\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if pp_match:
        pp_str = "[" + pp_match.group(1).strip() + "]"
        prohibited_pairs = ast.literal_eval(pp_str)

    # 8) Extrair dependent_warehouses
    #    Mesmo procedimento.
    dependent_warehouses = []
    dw_match = re.search(r"dependent_warehouses\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if dw_match:
        dw_str = "[" + dw_match.group(1).strip() + "]"
        dependent_warehouses = ast.literal_eval(dw_str)

    return (
        nWarehouses,
        nCustomers,
        fixedCost,
        capacity,
        demand,
        transportCost,
        prohibited_pairs,
        dependent_warehouses,
    )



def solve_capacitated_warehouse_location(
    nWarehouses,
    nCustomers,
    fixedCost,
    capacity,
    demand,
    transportCost,
    incompatiblePairs,
    groups,
    time_limit=300000,
):
    """
    Solve the Capacitated Warehouse Location Problem using DOcplex.
    time_limit: time limit in seconds (default = 300 seconds)
    """
    model = Model("Capacitated_Warehouse_Location")

    # Decision Variables
    # x[i] = 1 if warehouse i is open, 0 otherwise
    x = model.binary_var_list(nWarehouses, name="x")

    # y[i][j] = 1 if customer j is assigned to warehouse i, 0 otherwise
    y = model.binary_var_matrix(nWarehouses, nCustomers, name="y")

    # amountServed[i][j] = amount served by warehouse i to customer j
    amountServed = model.continuous_var_matrix(
        nWarehouses, nCustomers, name="amountServed"
    )

    # Objective Function: Minimize fixed costs + transportation costs
    model.minimize(
        model.sum(fixedCost[i] * x[i] for i in range(nWarehouses))
        + model.sum(
            transportCost[i][j] * amountServed[i, j]
            for i in range(nWarehouses)
            for j in range(nCustomers)
        )
    )

    # Constraints

    # 1. Each customer is assigned to at least one warehouse
    for j in range(nCustomers):
        model.add_constraint(model.sum(y[i, j] for i in range(nWarehouses)) >= 1)


    # 2. The total amount served to each customer equals their demand
    for j in range(nCustomers):
        model.add_constraint(
            model.sum(amountServed[i, j] for i in range(nWarehouses)) == demand[j]
        )

    # 3. The total served by each warehouse cannot exceed its capacity if open
    for i in range(nWarehouses):
        model.add_constraint(
            model.sum(amountServed[i, j] for j in range(nCustomers)) <= capacity[i] * x[i]
        )

    # 4. amountServed[i][j] <= demand[j] * y[i][j]
    for i in range(nWarehouses):
        for j in range(nCustomers):
            model.add_constraint(amountServed[i, j] <= demand[j] * y[i, j])

    # 5. y[i][j] <= x[i]
    for i in range(nWarehouses):
        for j in range(nCustomers):
            model.add_constraint(y[i, j] <= x[i])

    # 6. If a warehouse is open, it must be utilized at least 80% of its capacity
    for i in range(nWarehouses):
        model.add_constraint(
            model.sum(amountServed[i, j] for j in range(nCustomers))
            >= 0.8 * capacity[i] * x[i]
        )

    # 7. Certain pairs of customers cannot be served by the same warehouse
    for (c1, c2) in incompatiblePairs:
        for i in range(nWarehouses):
            model.add_constraint(y[i, c1 - 1] + y[i, c2 - 1] <= 1)

    # 8. If one warehouse in a group is open, all others in the group must also open
    for i, j in groups:
            model.add_constraint(x[i] <= x[j])  # Synchronize open/close statuses

    # 9. Tie amountServed to y[i][j]
    for i in range(nWarehouses):
        for j in range(nCustomers):
            model.add_constraint(amountServed[i, j] >= y[i, j])

    # Set time limit
    model.parameters.timelimit = time_limit

    # Solve the model
    solution = model.solve(log_output=True)

    if solution:
        print("\nCustomer Assignments:")
        for j in range(nCustomers):
            print(f"Customer {j} is served by:")
            for i in range(nWarehouses):
                if y[i, j].solution_value == 1:
                    print(f"  -> Warehouse {i + 1} = {amountServed[i, j].solution_value}")

        print(f"Optimal Total Cost: {solution.objective_value:.2f}")
        print("\nWarehouses to Open:")
        for i in range(nWarehouses):
            if x[i].solution_value > 0.5:
                print(f"  - Warehouse {i + 1}")     
    else:
        print("No optimal solution found within the time limit.")



if __name__ == "__main__":
    data_file = ".dat/facility_location_124.dat"

    try:
        # Read data from file
        (
            nWarehouses,
            nCustomers,
            fixedCost,
            capacity,
            demand,
            transportCost,
            prohibited_pairs,
            dependent_warehouses,
        ) = read_data_file(data_file)

        # Solve the problem
        solve_capacitated_warehouse_location(
            nWarehouses,
            nCustomers,
            fixedCost,
            capacity,
            demand,
            transportCost,
            prohibited_pairs,
            dependent_warehouses,
        )
    except Exception as e:
        print(f"Error: {e}")
