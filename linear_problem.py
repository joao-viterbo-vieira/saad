import re
import ast
from ortools.linear_solver import pywraplp


def read_data_file(filename):
    """
    Lê o ficheiro de dados do problema (ex.: dados.txt) e devolve
    nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost
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
    fixedCost = [float(x.strip()) for x in fixedCost_str.replace("\n", "").split(",")]

    # 4) Extrair capacity
    capacity_match = re.search(r"capacity\s*=\s*\[(.*?)\];", content, re.DOTALL)
    capacity_str = capacity_match.group(1)
    capacity = [float(x.strip()) for x in capacity_str.replace("\n", "").split(",")]

    # 5) Extrair demand
    demand_match = re.search(r"demand\s*=\s*\[(.*?)\];", content, re.DOTALL)
    demand_str = demand_match.group(1)
    demand = [float(x.strip()) for x in demand_str.replace("\n", "").split(",")]

    # 6) Extrair transportCost como matriz
    transportCost_match = re.search(
        r"transportCost\s*=\s*\[(.*?)\];", content, re.DOTALL
    )
    transportCost_str = transportCost_match.group(1).strip()
    transportCost_str = "[" + transportCost_str + "]"
    transportCost_str = transportCost_str.replace(";", "")
    transportCost = ast.literal_eval(transportCost_str)

    return nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost


def solve_capacitated_warehouse_location(
    nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost
):
    """
    Resolve o problema de Localização de Armazéns Capacitados usando OR-Tools.
    """
    solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        print("Solver não disponível.")
        return

    Warehouses = range(nWarehouses)
    Customers = range(nCustomers)

    # Variáveis de decisão
    open_vars = {i: solver.BoolVar(f"open_{i}") for i in Warehouses}
    supply_vars = {
        (i, j): solver.NumVar(0, solver.infinity(), f"supply_{i}_{j}")
        for i in Warehouses
        for j in Customers
    }

    # Função objetivo
    solver.Minimize(
        solver.Sum(fixedCost[i] * open_vars[i] for i in Warehouses)
        + solver.Sum(
            transportCost[i][j] * supply_vars[i, j]
            for i in Warehouses
            for j in Customers
        )
    )

    # Restrição de demanda
    for j in Customers:
        constraint = solver.Constraint(demand[j], demand[j])
        for i in Warehouses:
            constraint.SetCoefficient(supply_vars[i, j], 1)

    # Restrição de capacidade
    for i in Warehouses:
        constraint = solver.Constraint(0, capacity[i])
        for j in Customers:
            constraint.SetCoefficient(supply_vars[i, j], 1)
        constraint.SetCoefficient(open_vars[i], -capacity[i])

    # Restrição de ligação (supply <= demand * open)
    for i in Warehouses:
        for j in Customers:
            constraint = solver.Constraint(0, solver.infinity())
            constraint.SetCoefficient(supply_vars[i, j], 1)
            constraint.SetCoefficient(open_vars[i], -demand[j])

    # Resolver o problema
    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print(f"\nCusto Total Ótimo: {solver.Objective().Value():.2f}\n")
        print("Armazéns a Abrir:")
        for i in Warehouses:
            if open_vars[i].solution_value() > 0.5:
                print(f"  - Armazém {i + 1} está aberto.")

        print("\nFornecimento aos Clientes:")
        for j in Customers:
            print(f"\nCliente {j + 1} é atendido por:")
            for i in Warehouses:
                supplied_amount = supply_vars[i, j].solution_value()
                if supplied_amount > 1e-6:
                    print(
                        f"  -> Armazém {i + 1} com fornecimento: {supplied_amount:.2f}"
                    )
    elif status == pywraplp.Solver.INFEASIBLE:
        print("O problema não tem solução viável.")
    elif status == pywraplp.Solver.UNBOUNDED:
        print("O problema está sem limites.")
    else:
        print("O solver não encontrou uma solução ótima.")


if __name__ == "__main__":
    data_file = "wh_ficheiro_dados.txt"

    try:
        nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost = (
            read_data_file(data_file)
        )
        solve_capacitated_warehouse_location(
            nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost
        )
    except Exception as e:
        print(f"Erro: {e}")
