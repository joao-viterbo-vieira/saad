import re
import ast
from docplex.mp.model import Model


def read_data_file(filename):
    """
    Reads the data file and extracts:
    nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost, incompatiblePairs, groups
    """
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract number of warehouses
    nWarehouses_match = re.search(r"nWarehouses\s*=\s*(\d+)\s*;", content)
    if not nWarehouses_match:
        raise ValueError("nWarehouses not found in the data file.")
    nWarehouses = int(nWarehouses_match.group(1))

    # Extract number of customers
    nCustomers_match = re.search(r"nCustomers\s*=\s*(\d+)\s*;", content)
    if not nCustomers_match:
        raise ValueError("nCustomers not found in the data file.")
    nCustomers = int(nCustomers_match.group(1))

    # Extract fixedCost as a list of floats
    fixedCost_match = re.search(r"fixedCost\s*=\s*\[(.*?)\];", content, re.DOTALL)
    if not fixedCost_match:
        raise ValueError("fixedCost not found in the data file.")
    fixedCost = [
        float(x.strip()) for x in fixedCost_match.group(1).replace("\n", "").split(",")
    ]

    # Extract capacity
    capacity_match = re.search(r"capacity\s*=\s*\[(.*?)\];", content, re.DOTALL)
    if not capacity_match:
        raise ValueError("capacity not found in the data file.")
    capacity = [
        float(x.strip()) for x in capacity_match.group(1).replace("\n", "").split(",")
    ]

    # Extract demand
    demand_match = re.search(r"demand\s*=\s*\[(.*?)\];", content, re.DOTALL)
    if not demand_match:
        raise ValueError("demand not found in the data file.")
    demand = [
        float(x.strip()) for x in demand_match.group(1).replace("\n", "").split(",")
    ]

    # Extract transportCost (matrix)
    transportCost_match = re.search(
        r"transportCost\s*=\s*\[(.*?)\];", content, re.DOTALL
    )
    if not transportCost_match:
        raise ValueError("transportCost not found in the data file.")
    transportCost_str = "[" + transportCost_match.group(1).strip() + "]"
    transportCost = ast.literal_eval(transportCost_str.replace(";", ""))

    # Define incompatiblePairs manually as a list of tuples
    incompatiblePairs = [
         (4, 6),    # Customers 4 and 6 are served by Warehouse 1.
         (4, 30),   # Customers 4 and 30 are served by Warehouse 1.
         (6, 30),   # Customers 6 and 30 are served by Warehouse 1.
         (11, 23),  # Customers 11 and 23 are served by Warehouse 11.
         (34, 37),  # Customers 34 and 37 are served by Warehouse 6.
         (37, 38),  # Customers 37 and 38 are served by Warehouse 6.
         (41, 42),  # Customers 41 and 42 are served by Warehouse 12.
         (45, 46),  # Customers 45 and 46 are served by Warehouse 8.
         (43, 45),  # Customers 43 and 45 are served by Warehouse 8.
        # # Add more pairs as needed
    ]

    # Define groups manually as a list of lists
    groups = [
         [1, 10],       # Warehouses 1 and 5 need to open together.
         [8, 12],      # Warehouses 8 and 12 need to open together.
         [11, 14],     # Warehouses 11 and 14 need to open together.
         [2, 3, 9],    # Warehouses 2, 3, and 9 need to open together.
         [6, 9, 11],   # Warehouses 6, 9, and 11 need to open together.
         [1, 5, 12, 8] # Warehouses 1, 5, 12, and 8 need to open together.
         # Add more groups as needed
    ]

    # Consistency checks
    if len(fixedCost) != nWarehouses:
        raise ValueError("fixedCost length does not match nWarehouses.")
    if len(capacity) != nWarehouses:
        raise ValueError("capacity length does not match nWarehouses.")
    if len(demand) != nCustomers:
        raise ValueError("demand length does not match nCustomers.")
    if len(transportCost) != nWarehouses:
        raise ValueError("transportCost rows do not match nWarehouses.")
    for row in transportCost:
        if len(row) != nCustomers:
            raise ValueError("transportCost columns do not match nCustomers.")

    return nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost, incompatiblePairs, groups


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
    for group in groups:
        for i in group:
            for j in group:
                if i != j:
                    model.add_constraint(x[i - 1] == x[j - 1])  # Synchronize open/close statuses

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
    data_file = ".dat/facility_location_123.dat"

    try:
        # Read data from file
        (
            nWarehouses,
            nCustomers,
            fixedCost,
            capacity,
            demand,
            transportCost,
            incompatiblePairs,
            groups,
        ) = read_data_file(data_file)

        # Solve the problem
        solve_capacitated_warehouse_location(
            nWarehouses,
            nCustomers,
            fixedCost,
            capacity,
            demand,
            transportCost,
            incompatiblePairs,
            groups,
        )
    except Exception as e:
        print(f"Error: {e}")
