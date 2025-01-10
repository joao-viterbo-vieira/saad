# modelo de constraint programming para problema de alocação de armazéns a clientes
# versão com novas restrições
# forçar a um uso mínimo de capacidade se o armazém for aberto

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

    # conceito adicionado - clientes que não podem seer servidos pelo mesmo armazém
    # Clientes com números sequenciais não podem compartilhar o mesmo armazém
    #prohibited_pairs = [(i, i + 1) for i in range(1, 50, 2)]

    # Clientes divisíveis por 5 não podem compartilhar o mesmo armazém
    #prohibited_pairs += [(i, j) for i in range(5, 51, 5) for j in range(5, 51, 5) if i < j]

    # Adjust indices to zero-based
    prohibited_pairs = [(i - 1, i) for i in range(2, 51, 2)]  # Sequential pairs
    prohibited_pairs += [
        (i, j)
        for i in range(5, 50, 5)
        for j in range(5, 50, 5)
        if i < j
    ]  # Multiples of 5

    # conceito adicionado - warehouses que tem que ser abertos se determinado warehouses for aberto

    # Initialize the dependent_warehouses array
    dependent_warehouses = []

    # Create dependency pairs for the first 5 warehouses
    for i in range(5):
        dependent_warehouses.append((i, i + 5))

    return nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost, prohibited_pairs, dependent_warehouses


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
    if constraints_config["assign_customer_to_warehouse"]:
        for j in range(nCustomers):
            model.Add(sum(y[i][j] for i in range(nWarehouses)) >= 1)

    # 2. A quantidade total servida a cada cliente deve ser igual à sua demanda
    if constraints_config["serve_exact_demand"]:
        for j in range(nCustomers):
            model.Add(sum(amountServed[i][j] for i in range(nWarehouses)) == demand[j])

    # 3. A quantidade total servida por cada armazém não deve exceder sua capacidade
    if constraints_config["warehouse_capacity"]:
        for i in range(nWarehouses):
            model.Add(
                sum(amountServed[i][j] for j in range(nCustomers)) <= capacity[i] * x[i]
            )

    # 4. amountServed[i][j] <= demanda[j] * y[i][j]
    if constraints_config["serve_demand_with_y"]:
        for i in range(nWarehouses):
            for j in range(nCustomers):
                model.Add(amountServed[i][j] <= demand[j] * y[i][j])

    # 5. y[i][j] <= x[i]
    if constraints_config["assign_to_open_warehouse"]:
        for i in range(nWarehouses):
            for j in range(nCustomers):
                model.Add(y[i][j] <= x[i])

    # 6. Se um armazém estiver aberto, ele deve servir pelo menos 80% de sua capacidade
    if constraints_config["minimum_capacity_usage"]:
        for i in range(nWarehouses):
            model.Add(
                sum(amountServed[i][j] for j in range(nCustomers)) >= int(0.8 * capacity[i]) * x[i]
            )

    # 7. Adicionar restrições para cada par de clientes
    #for j1-1, j2-1 in prohibited_pairs:
    #    for i in range(nWarehouses):
    #        model.Add(y[i][j1] + y[i][j2] <= 1)

    # 7. Adicionar restrições para cada par de clientes
    if constraints_config["prohibited_pairs"]:
        for j1, j2 in prohibited_pairs:
            # Ajuste dos índices de j1 e j2 para índice baseado em 0
            j1 -= 1
            j2 -= 1

            # Verificar se os índices estão dentro do intervalo válido
            if j1 >= 0 and j1 < nCustomers and j2 >= 0 and j2 < nCustomers:
                for i in range(nWarehouses):
                    model.Add(y[i][j1] + y[i][j2] <= 1)
            else:
                print(f"Índices proibidos inválidos: j1={j1 + 1}, j2={j2 + 1}")

    # 8. Restrições: Se um armazém i estiver aberto, o armazém j também deve estar aberto
    if constraints_config["dependent_warehouses"]:
        for i, j in dependent_warehouses:
            model.Add(x[i] == x[j])  # Se i está aberto, j deve estar aberto também

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
                total_served = sum(solver.Value(amountServed[i][j]) for j in range(nCustomers))
                print(f"  - Armazém {i + 1} está aberto. Total fornecido: {total_served} unidades")

        print("\nArmazéns Fechados:")
        for i in range(nWarehouses):
            if solver.Value(x[i]) == 0:
                print(f"  - Armazém {i + 1} está fechado.")

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
        nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost, prohibited_pairs, dependent_warehouses = (
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
            prohibited_pairs,
            dependent_warehouses,
            constraints_config,
            time_limit_seconds=time_limit_seconds,
        )
    except Exception as e:
        print(f"Erro: {e}")