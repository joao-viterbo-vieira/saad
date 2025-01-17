# modelo de constraint programming para problema de alocação de armazéns a clientes
# versão com novas restrições
# forçar a um uso mínimo de capacidade se o armazém for aberto

import re
import ast
from ortools.sat.python import cp_model
import math


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
    prohibited_pairs,
    dependent_warehouses,
    constraints_config,
    time_limit_seconds=300,
):
    """
    Resolve o problema de Localização de Armazéns Capacitados usando OR-Tools com Programação por Restrições (CP-SAT).
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
    # Aumentado para 5.000.000 para coincidir com o LP
    amountServed = [
        [
            model.NewIntVar(0, 5_000_000, f"amountServed_{i}_{j}")
            for j in range(nCustomers)
        ]
        for i in range(nWarehouses)
    ]

    # -------------------------------------------------
    # Função objetivo: minimizar custos fixos + transporte
    # -------------------------------------------------
    model.Minimize(
        sum(fixedCost[i] * x[i] for i in range(nWarehouses))
        + sum(
            transportCost[i][j] * amountServed[i][j]
            for i in range(nWarehouses)
            for j in range(nCustomers)
        )
    )

    # --------------------------------
    # Restrições
    # --------------------------------

    # 1. Cada cliente deve ser atribuído a >= 1 armazém
    if constraints_config.get("assign_customer_to_warehouse", False):
        for j in range(nCustomers):
            model.Add(sum(y[i][j] for i in range(nWarehouses)) >= 1)

    # 2. A quantidade total servida a cada cliente == demanda
    if constraints_config.get("serve_exact_demand", False):
        for j in range(nCustomers):
            model.Add(sum(amountServed[i][j] for i in range(nWarehouses)) == demand[j])

    # 3. A quantidade total servida por cada armazém <= capacidade * x[i]
    if constraints_config.get("warehouse_capacity", False):
        for i in range(nWarehouses):
            model.Add(
                sum(amountServed[i][j] for j in range(nCustomers)) <= capacity[i] * x[i]
            )

    # 4. amountServed[i][j] <= demanda[j] * y[i][j]
    if constraints_config.get("serve_demand_with_y", False):
        for i in range(nWarehouses):
            for j in range(nCustomers):
                model.Add(amountServed[i][j] <= demand[j] * y[i][j])

    # 5. y[i][j] <= x[i]
    if constraints_config.get("assign_to_open_warehouse", False):
        for i in range(nWarehouses):
            for j in range(nCustomers):
                model.Add(y[i][j] <= x[i])

    # 6. Se armazém aberto, deve servir >= 80% de sua capacidade
    if constraints_config.get("minimum_capacity_usage", False):
        for i in range(nWarehouses):
            # No LP/DOcplex atual usamos sum(...) >= 0.8 * capacity[i] * x[i].
            # Como CP-SAT lida só com inteiros, faremos "arredondar para cima" pra não afrouxar a restrição:
            capacity_80 = math.ceil(0.8 * capacity[i])
            model.Add(
                sum(amountServed[i][j] for j in range(nCustomers)) >= capacity_80 * x[i]
            )

    # 7. Pares de clientes que não podem ser atendidos pelo mesmo armazém
    if constraints_config.get("prohibited_pairs", False):
        for c1, c2 in prohibited_pairs:
            j1 = c1 - 1
            j2 = c2 - 1
            if 0 <= j1 < nCustomers and 0 <= j2 < nCustomers:
                for i in range(nWarehouses):
                    model.Add(y[i][j1] + y[i][j2] <= 1)
            else:
                print(f"Índices inválidos: j1={c1}, j2={c2}")

    # 8. Dependência entre armazéns: x[i] <= x[j]
    if constraints_config.get("dependent_warehouses", False):
        for i, j in dependent_warehouses:
            model.Add(x[i] <= x[j])

    # 9. [Nova] Amarrar amountServed[i][j] >= y[i][j] (como no LP/DOcplex)
    #    Se y[i][j] = 1, servir pelo menos 1 unidade
    #    (No LP é “amountServed >= y[i][j]”; aqui mantemos a mesma ideia)
    for i in range(nWarehouses):
        for j in range(nCustomers):
            model.Add(amountServed[i][j] >= y[i][j])

    # -------------------
    # Resolver o modelo
    # -------------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.log_search_progress = True

    status = solver.Solve(model)

    # --------------------------------
    # Interpretar a Solução
    # --------------------------------
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"\nCusto Total Ótimo (ou factível): {solver.ObjectiveValue():.2f}\n")

        print("Armazéns Abertos:")
        for i in range(nWarehouses):
            if solver.Value(x[i]) == 1:
                total_served = sum(
                    solver.Value(amountServed[i][j]) for j in range(nCustomers)
                )
                print(f"  - Armazém {i + 1} aberto, total fornecido: {total_served}")

        print("\nArmazéns Fechados:")
        for i in range(nWarehouses):
            if solver.Value(x[i]) == 0:
                print(f"  - Armazém {i + 1} fechado.")

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
    data_file = "/Users/joaovieira/Desktop/Trabalho_SAAD/.dat/facility_location_92.dat"

    # Configuração de ativação/desativação de restrições
    constraints_config = {
        "assign_customer_to_warehouse": True,
        "serve_exact_demand": True,
        "warehouse_capacity": True,
        "serve_demand_with_y": True,
        "assign_to_open_warehouse": True,
        "minimum_capacity_usage": False,
        "prohibited_pairs": False,
        "dependent_warehouses": False,
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
