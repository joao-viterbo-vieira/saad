import re
import ast
from ortools.linear_solver import pywraplp

# Custo Total Ótimo: 1150951.65


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

    # 6) Extrair transportCost, que é uma matriz
    transportCost_match = re.search(
        r"transportCost\s*=\s*\[(.*?)\];", content, re.DOTALL
    )
    if not transportCost_match:
        raise ValueError("transportCost não encontrado no ficheiro de dados.")
    transportCost_str = transportCost_match.group(1).strip()

    # Convertendo para lista de listas
    transportCost_str = "[" + transportCost_str + "]"
    transportCost_str = transportCost_str.replace(";", "")
    try:
        transportCost = ast.literal_eval(transportCost_str)
    except Exception as e:
        raise ValueError(f"Erro ao interpretar transportCost: {e}")

    # Verificações de consistência
    if len(fixedCost) != nWarehouses:
        raise ValueError("O tamanho de fixedCost não corresponde a nWarehouses.")
    if len(capacity) != nWarehouses:
        raise ValueError("O tamanho de capacity não corresponde a nWarehouses.")
    if len(demand) != nCustomers:
        raise ValueError("O tamanho de demand não corresponde a nCustomers.")
    if len(transportCost) != nWarehouses:
        raise ValueError(
            "O número de linhas em transportCost não corresponde a nWarehouses."
        )
    for idx, row in enumerate(transportCost):
        if len(row) != nCustomers:
            raise ValueError(
                f"O número de colunas na linha {idx + 1} de transportCost não corresponde a nCustomers."
            )

    # Inicializa as variáveis para os pares proibidos
    prohibited_pairs = [(i - 1, i) for i in range(2, 51, 2)]  # Pares sequenciais
    prohibited_pairs += [
        (i, j) for i in range(5, 50, 5) for j in range(5, 50, 5) if i < j
    ]  # Múltiplos de 5

    # Dependência entre armazéns
    dependent_warehouses = []
    for i in range(5):
        dependent_warehouses.append((i, i + 5))

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
    prohibited_pairs,
    dependent_warehouses,
    constraints_config,
    time_limit=180000,
):
    """
    Resolve o problema de Localização de Armazéns Capacitados usando OR-Tools com solver CBC.
    time_limit: limite de tempo em milissegundos (default = 60000 ms = 1 minuto)
    """
    # Criação do solver
    solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        print("Solver CBC não está disponível.")
        return

    # Definir o limite de tempo
    solver.SetTimeLimit(time_limit)  # Tempo em milissegundos

    # Índices (0-based em Python)
    Warehouses = range(nWarehouses)
    Customers = range(nCustomers)

    # Variáveis de decisão
    x = {i: solver.BoolVar(f"x_{i}") for i in Warehouses}
    y = {(i, j): solver.BoolVar(f"y_{i}_{j}") for i in Warehouses for j in Customers}
    amountServed = {
        (i, j): solver.IntVar(0, 5000, f"amountServed_{i}_{j}")
        for i in Warehouses
        for j in Customers
    }

    # Função objetivo: minimizar custos fixos + custos de transporte
    objective = solver.Sum(fixedCost[i] * x[i] for i in Warehouses) + solver.Sum(
        transportCost[i][j] * amountServed[i, j] for i in Warehouses for j in Customers
    )
    solver.Minimize(objective)

    # Restrições

    # 1. Cada cliente deve ser atribuído a pelo menos um armazém
    if constraints_config["assign_customer_to_warehouse"]:
        for j in Customers:
            solver.Add(solver.Sum(y[i, j] for i in Warehouses) >= 1)

    # 2. A quantidade total servida a cada cliente deve ser igual à sua demanda
    if constraints_config["serve_exact_demand"]:
        for j in Customers:
            solver.Add(solver.Sum(amountServed[i, j] for i in Warehouses) == demand[j])

    # 3. A quantidade total servida por cada armazém não deve exceder sua capacidade multiplicada por x[i]
    if constraints_config["warehouse_capacity"]:
        for i in Warehouses:
            solver.Add(
                solver.Sum(amountServed[i, j] for j in Customers) <= capacity[i] * x[i]
            )

    # 4. amountServed[i][j] <= demanda[j] * y[i][j]
    if constraints_config["serve_demand_with_y"]:
        for i in Warehouses:
            for j in Customers:
                solver.Add(amountServed[i, j] <= demand[j] * y[i, j])

    # 5. y[i][j] <= x[i]
    if constraints_config["assign_to_open_warehouse"]:
        for i in Warehouses:
            for j in Customers:
                solver.Add(y[i, j] <= x[i])

    # 6. Se um armazém estiver aberto, ele deve ser utilizado em pelo menos 80% de sua capacidade
    if constraints_config["minimum_capacity_usage"]:
        for i in Warehouses:
            solver.Add(
                solver.Sum(amountServed[i, j] for j in Customers)
                >= 0.8 * capacity[i] * x[i]
            )

    # 7. Certos pares de clientes não podem ser atendidos pelo mesmo armazém
    if constraints_config["prohibited_pairs"]:
        for c1, c2 in prohibited_pairs:
            for i in Warehouses:
                solver.Add(y[i, c1 - 1] + y[i, c2 - 1] <= 1)

    # 8. Dependência entre armazéns
    if constraints_config["dependent_warehouses"]:
        for i, j in dependent_warehouses:
            solver.Add(x[i] <= x[j])

    # Resolver o problema
    status = solver.Solve()

    # Processar e exibir os resultados
    if status == pywraplp.Solver.OPTIMAL:
        print(f"\nCusto Total Ótimo: {solver.Objective().Value():.2f}\n")
        print("Armazéns a Abrir e Quantidade Total Servida:")
        for i in Warehouses:
            if x[i].solution_value() > 0.5:
                total_served = sum(
                    amountServed[i, j].solution_value() for j in Customers
                )
                print(
                    f"  - Armazém {i + 1} está aberto. Quantidade Total Servida: {total_served:.2f} unidades"
                )

        # Exibir os armazéns que não estão abertos
        print("\nArmazéns Não Abertos:")
        for i in Warehouses:
            if x[i].solution_value() <= 0.5:  # Verifica se o armazém não está aberto
                print(f"  - Armazém {i + 1} não está aberto.")

        print("\nFornecimento aos Clientes:")
        for j in Customers:
            print(f"\nCliente {j + 1} é atendido por:")
            for i in Warehouses:
                served = amountServed[i, j].solution_value()
                if served > 0:
                    print(f"  -> Armazém {i + 1} com fornecimento: {served} unidades")
    elif status == pywraplp.Solver.INFEASIBLE:
        print("O problema não tem solução viável.")
    elif status == pywraplp.Solver.UNBOUNDED:
        print("O problema está sem limites.")
    else:
        print("O solver não encontrou uma solução ótima dentro do tempo limite.")


if __name__ == "__main__":
    # Caminho para o ficheiro de dados
    data_file = "wh_ficheiro_dados.txt"

    # Configuração de ativação/desativação de restrições
    constraints_config = {
        "assign_customer_to_warehouse": True,
        "serve_exact_demand": True,
        "warehouse_capacity": True,
        "serve_demand_with_y": True,
        "assign_to_open_warehouse": True,
        "minimum_capacity_usage": True,
        "prohibited_pairs": True,
        "dependent_warehouses": True,
    }

    try:
        # 1) Ler dados do ficheiro
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

        # 2) Resolver o problema
        # Define o limite de tempo (exemplo: 5 minutos = 300000 milissegundos)
        time_limit_ms = 300000  # 5 minutos

        solve_capacitated_warehouse_location(
            nWarehouses,
            nCustomers,
            fixedCost,
            capacity,
            demand,
            transportCost,
            prohibited_pairs,
            dependent_warehouses,
            constraints_config,
            time_limit=time_limit_ms,
        )

    except Exception as e:
        print(f"Erro: {e}")
