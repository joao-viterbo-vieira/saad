import re
import ast
from ortools.sat.python import cp_model


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

    return nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost


def solve_capacitated_warehouse_location(
    nWarehouses,
    nCustomers,
    fixedCost,
    capacity,
    demand,
    transportCost,
    time_limit_seconds=300,
):
    """
    Resolve o problema de Localização de Armazéns Capacitados usando OR-Tools com Programação por Restrições.
    time_limit_seconds: limite de tempo em segundos (default = 300 s = 5 minutos)
    """
    model = cp_model.CpModel()

    # Certificar que capacity e demand são inteiros
    capacity = [int(c) for c in capacity]
    demand = [int(d) for d in demand]

    # Definir variáveis de decisão
    # x[i] = 1 se o armazém i estiver aberto, 0 caso contrário
    x = [model.NewBoolVar(f"x_{i}") for i in range(nWarehouses)]

    # y[i][j] = 1 se o cliente j for atribuído ao armazém i, 0 caso contrário
    y = [
        [model.NewBoolVar(f"y_{i}_{j}") for j in range(nCustomers)]
        for i in range(nWarehouses)
    ]

    # amountServed[i][j] = quantidade fornecida pelo armazém i para o cliente j
    # Variável inteira entre 0 e 5000 (inteiros)
    amountServed = [
        [model.NewIntVar(0, 5000, f"amountServed_{i}_{j}") for j in range(nCustomers)]
        for i in range(nWarehouses)
    ]

    # Função objetivo: minimizar custos fixos + custos de transporte
    model.Minimize(
        sum(fixedCost[i] * x[i] for i in range(nWarehouses))
        + sum(
            transportCost[i][j] * amountServed[i][j]
            for i in range(nWarehouses)
            for j in range(nCustomers)
        )
    )

    # Restrições

    # 1. Cada cliente deve ser atribuído a pelo menos um armazém
    for j in range(nCustomers):
        model.Add(sum(y[i][j] for i in range(nWarehouses)) >= 1)

    # 2. A quantidade total servida a cada cliente deve ser igual à sua demanda
    for j in range(nCustomers):
        model.Add(sum(amountServed[i][j] for i in range(nWarehouses)) == demand[j])

    # 3. A quantidade total servida por cada armazém não deve exceder sua capacidade
    for i in range(nWarehouses):
        model.Add(
            sum(amountServed[i][j] for j in range(nCustomers)) <= capacity[i] * x[i]
        )

    # 4. amountServed[i][j] <= demanda[j] * y[i][j]
    for i in range(nWarehouses):
        for j in range(nCustomers):
            model.Add(amountServed[i][j] <= demand[j] * y[i][j])

    # 5. y[i][j] <= x[i]
    for i in range(nWarehouses):
        for j in range(nCustomers):
            model.Add(y[i][j] <= x[i])

    # Definir o solucionador com limite de tempo
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.log_search_progress = True  # Para ver o progresso

    # Resolver o problema
    status = solver.Solve(model)

    # Processar e exibir os resultados
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"\nCusto Total Ótimo: {solver.ObjectiveValue():.2f}\n")
        print("Armazéns a Abrir:")
        for i in range(nWarehouses):
            if solver.Value(x[i]) == 1:
                print(f"  - Armazém {i + 1} está aberto.")

        print("\nFornecimento aos Clientes:")
        for j in range(nCustomers):
            print(f"\nCliente {j + 1} é atendido por:")
            for i in range(nWarehouses):
                served = solver.Value(amountServed[i][j])
                if served > 0:
                    print(f"  -> Armazém {i + 1} com fornecimento: {served} unidades")
    elif status == cp_model.INFEASIBLE:
        print("O problema não tem solução viável.")
    elif status == cp_model.MODEL_INVALID:
        print("O modelo é inválido.")
    else:
        print("O solver não encontrou uma solução ótima dentro do tempo limite.")


if __name__ == "__main__":
    # Caminho para o ficheiro de dados
    data_file = "wh_ficheiro_dados.txt"

    try:
        # 1) Ler dados do ficheiro
        nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost = (
            read_data_file(data_file)
        )

        # 2) Resolver o problema
        # Define o limite de tempo (exemplo: 5 minutos = 300 segundos)
        time_limit_seconds = 300  # 5 minutos

        solve_capacitated_warehouse_location(
            nWarehouses,
            nCustomers,
            fixedCost,
            capacity,
            demand,
            transportCost,
            time_limit_seconds=time_limit_seconds,
        )
    except Exception as e:
        print(f"Erro: {e}")
