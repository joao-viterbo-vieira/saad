# este parser divide transforma o custo total em custo unitario por unidade de demanda
import csv

# Define the output file name
dat_file = ".dat/facility_location_93.dat"

# Open your input data file (adjust path as necessary)
input_file = "data/cap93.txt"

# Read the data from your file
with open(input_file, "r") as f:
    lines = f.readlines()

# Prepare the CPLEX data
num_warehouses, num_customers = map(int, lines[0].split())
warehouse_capacities = []
warehouse_costs = []
customer_demands = []
serve_costs = []


# Function to clean up numeric values (handle decimal points correctly)
def clean_value(value):
    try:
        cleaned_value = float(
            value.strip().replace(",", ".")
        )  # Ensure proper handling of decimals
        return cleaned_value
    except ValueError:
        print(f"Error cleaning value: {value}")
        return None  # Return None if there's an error


# Read the warehouse data
for i in range(1, num_warehouses + 1):
    capacity, cost = map(clean_value, lines[i].split())
    if None not in (capacity, cost):
        warehouse_capacities.append(capacity)
        warehouse_costs.append(cost)
    else:
        print(f"Error in warehouse data: {lines[i]}")

# Read the customer data
customer_index = num_warehouses + 1
for _ in range(num_customers):
    # First line: Customer demand
    demand = clean_value(
        lines[customer_index].strip()
    )  # Customer demand is a floating-point number
    if demand is not None:
        customer_demands.append(demand)
    else:
        print(f"Error in customer demand: {lines[customer_index]}")

    # Next lines: Cost of serving the demand from each warehouse
    customer_index += 1
    customer_costs = []

    # Read the cost lines until we have the same number of costs as customers
    while len(customer_costs) < num_warehouses:
        costs = list(map(clean_value, lines[customer_index].split()))
        if None not in costs:
            customer_costs.extend(costs)  # Append all costs from this line
        else:
            print(f"Error in customer costs: {lines[customer_index]}")
        customer_index += 1

    serve_costs.append(customer_costs)

# Divide only transport costs by the corresponding customer's demand
transport_cost_matrix = []
for warehouse_idx in range(num_warehouses):
    transport_costs_for_warehouse = []
    for customer_idx in range(num_customers):
        # Divide the cost by the corresponding customer's demand
        cost = serve_costs[customer_idx][warehouse_idx] / customer_demands[customer_idx]
        transport_costs_for_warehouse.append(cost)
    transport_cost_matrix.append(transport_costs_for_warehouse)

# Write the data in CPLEX .dat format
with open(dat_file, "w") as dat:
    dat.write(f"nWarehouses = {num_warehouses};\n")
    dat.write(f"nCustomers = {num_customers};\n")
    dat.write(
        f"fixedCost = {warehouse_costs};\n"
    )  # This corresponds to the warehouse fixed costs (not divided)
    dat.write(f"capacity = {warehouse_capacities};\n")
    dat.write(f"demand = {customer_demands};\n")

    # Write the transport cost matrix in the correct format
    dat.write("transportCost = [\n")
    for warehouse_costs_for_customer in transport_cost_matrix:
        dat.write(f"  {warehouse_costs_for_customer},\n")
    dat.write("];\n")

print(f"Data successfully written to {dat_file}")