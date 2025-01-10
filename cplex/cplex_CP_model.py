import re
import ast
from docplex.cp.model import CpoModel


def read_data_file(filename):
    """
    Lê o ficheiro de dados do problema (ex.: dados.txt) e devolve
    nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost
    """
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # 1) Extrair nWarehouses
    nWarehouses_match = re.search(r"nWarehouses\s*=\s*(\d+)\s*;", content)
    if not nWarehouses_match:
        raise ValueError("nWarehouses não encontrado no ficheiro de dados.")
    nWarehouses = int(nWarehouses_match.group(1))

    # 2) Extrair nCustomers
    nCustomers_match = re.search(r"nCustomers\s*=\s*(\d+)\s*;", content)
    if not nCustomers_match:
        raise ValueError("nCustomers não encontrado no ficheiro de dados.")
    nCustomers = int(nCustomers_match.group(1))

    # 3) Extrair fixedCost como lista de floats
    fixedCost_match = re.search(r"fixedCost\s*=\s*\[(.*?)\];", content, re.DOTALL)
    if not fixedCost_match:
        raise ValueError("fixedCost não encontrado no ficheiro de dados.")
    fixedCost_str = fixedCost_match.group(1)
    fixedCost = [float(x.strip()) for x in fixedCost_str.replace("\n", "").split(",")]

    # 4) Extrair capacity
    capacity_match = re.search(r"capacity\s*=\s*\[(.*?)\];", content, re.DOTALL)
    if not capacity_match:
        raise ValueError("capacity não encontrado no ficheiro de dados.")
    capacity_str = capacity_match.group(1)
    capacity = [float(x.strip()) for x in capacity_str.replace("\n", "").split(",")]

    # 5) Extrair demand
    demand_match = re.search(r"demand\s*=\s*\[(.*?)\];", content, re.DOTALL)
    if not demand_match:
        raise ValueError("demand não encontrado no ficheiro de dados.")
    demand_str = demand_match.group(1)
    demand = [float(x.strip()) for x in demand_str.replace("\n", "").split(",")]

    # 6) Extrair transportCost como matriz
    transportCost_match = re.search(
        r"transportCost\s*=\s*\[(.*?)\];", content, re.DOTALL
    )
    if not transportCost_match:
        raise ValueError("transportCost não encontrado no ficheiro de dados.")
    transportCost_str = transportCost_match.group(1).strip()
    transportCost_str = "[" + transportCost_str + "]"
    transportCost_str = transportCost_str.replace(";", "")
    transportCost = ast.literal_eval(transportCost_str)

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
        # Add more pairs as needed
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
    time_limit_seconds=300,
):
    """
    Resolve o problema de Localização de Armazéns Capacitados usando docplex com Programação por Restrições.
    time_limit_seconds: limite de tempo em segundos (default = 300 s = 5 minutos)
    """
    model = CpoModel()

    # Certificar que capacity e demand são inteiros
    capacity = [int(c) for c in capacity]
    demand = [int(d) for d in demand]

    # Definir variáveis de decisão
    # x[i] = 1 se o armazém i estiver aberto, 0 caso contrário
    x = [model.binary_var(name=f"x_{i}") for i in range(nWarehouses)]

    # y[i][j] = 1 se o cliente j for atribuído ao armazém i, 0 caso contrário
    y = [
        [model.binary_var(name=f"y_{i}_{j}") for j in range(nCustomers)]
        for i in range(nWarehouses)
    ]

    # amountServed[i][j] = quantidade fornecida pelo armazém i para o cliente j
    # Variável inteira entre 0 e 5000 (inteiros)
    amountServed = [
        [model.integer_var(0, 5000, name=f"amountServed_{i}_{j}") for j in range(nCustomers)]
        for i in range(nWarehouses)
    ]

    # Função objetivo: minimizar custos fixos + custos de transporte
    objective = (
        sum(fixedCost[i] * x[i] for i in range(nWarehouses))
        + sum(
            transportCost[i][j] * amountServed[i][j]
            for i in range(nWarehouses)
            for j in range(nCustomers)
        )
    )
    model.minimize(objective)

    # Restrições

    # 1. Cada cliente deve ser atribuído a pelo menos um armazém
    for j in range(nCustomers):
        model.add_constraint(sum(y[i][j] for i in range(nWarehouses)) >= 1)

    # 2. A quantidade total servida a cada cliente deve ser igual à sua demanda
    for j in range(nCustomers):
        model.add_constraint(sum(amountServed[i][j] for i in range(nWarehouses)) == demand[j])

    # 3. A quantidade total servida por cada armazém não deve exceder sua capacidade
    for i in range(nWarehouses):
        model.add_constraint(
            sum(amountServed[i][j] for j in range(nCustomers)) <= capacity[i] * x[i]
        )

    # 4. amountServed[i][j] <= demanda[j] * y[i][j]
    for i in range(nWarehouses):
        for j in range(nCustomers):
            model.add_constraint(amountServed[i][j] <= demand[j] * y[i][j])

    # 5. y[i][j] <= x[i]
    for i in range(nWarehouses):
        for j in range(nCustomers):
            model.add_constraint(y[i][j] <= x[i])

    # 6. If a warehouse is open, it must be utilized at least 80% of its capacity
    for i in range(nWarehouses):
        model.add_constraint(
            model.sum(amountServed[i][j] for j in range(nCustomers))
            >= 0.8 * capacity[i] * x[i]
        )

    # 7. Certain pairs of customers cannot be served by the same warehouse
    for (c1, c2) in incompatiblePairs:
        for i in range(nWarehouses):
            model.add_constraint(y[i][c1] + y[i][c2] <= 1)

    # 8. If one warehouse in a group is open, all others in the group must also open
    for group in groups:
        for i in group:
            for j in group:
                if i != j:
                    model.add_constraint(x[i] == x[j])  # Synchronize open/close statuses

    # 9. Tie amountServed to y[i][j]
    for i in range(nWarehouses):
        for j in range(nCustomers):
            model.add_constraint(amountServed[i][j] >= y[i][j])


    # Resolver o problema
    solution = model.solve(TimeLimit=time_limit_seconds)

    # Processar e exibir os resultados
    if solution:
        objective_value = solution.get_objective_values()[0]  # Retorna o valor da função objetivo
        print(f"\nCusto Total Ótimo: {objective_value:.2f}\n")
        print("Armazéns a Abrir:")
        for i in range(1, nWarehouses):
            if solution[x[i]] == 1:
                print(f"  - Armazém {i} está aberto.")

        print("\nFornecimento aos Clientes:")
        for j in range(1, nCustomers):
            print(f"\nCliente {j} é atendido por:")
            for i in range(1, nWarehouses):
                served = solution[amountServed[i][j]]
                if served > 0:
                    print(f"  -> Armazém {i} com fornecimento: {served} unidades")
    else:
        print("O solver não encontrou uma solução ótima dentro do tempo limite.")


if __name__ == "__main__":
    # Caminho para o ficheiro de dados
    data_file = ".dat/facility_location.dat"

    try:
        # 1) Ler dados do ficheiro
        nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost, incompatiblePairs, groups, = (
            read_data_file(data_file)
        )

        # 2) Resolver o problema
        # Define o limite de tempo (exemplo: 5 minutos = 300 segundos)
        time_limit_seconds = 1200  # 20 minutos

        solve_capacitated_warehouse_location(
            nWarehouses,
            nCustomers,
            fixedCost,
            capacity,
            demand,
            transportCost,
            incompatiblePairs,
            groups,
            time_limit_seconds=time_limit_seconds,
        )
    except Exception as e:
        print(f"Erro: {e}")