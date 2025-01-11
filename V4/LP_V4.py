import re
import ast
import io
import sys
from ortools.linear_solver import pywraplp
import math

# Custo Total Ótimo: 1150951.65


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
    time_limit=300,  # Em segundos
):
    """
    Resolve o problema de Localização de Armazéns Capacitados usando OR-Tools com solver CBC (MILP).
    time_limit: limite de tempo em segundos.
    """
    # Criação do solver
    solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        print("Solver CBC não está disponível.")
        return

    # PARA ASSEGURAR LOGS
    # Redirect stdout to capture solver logs
    log_capture = io.StringIO()
    sys.stdout = log_capture  # Redirect output to the StringIO object

    # Enable solver log
    solver.EnableOutput()

    # Restore stdout
    sys.stdout = sys.__stdout__

    ## FIM CODIGO PARA ASSEGURAR LOGS

    # Definir o limite de tempo em milissegundos
    solver.SetTimeLimit(int(time_limit * 1000))  # Convertendo para ms

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
    if constraints_config.get("assign_customer_to_warehouse", False):
        for j in Customers:
            solver.Add(solver.Sum(y[i, j] for i in Warehouses) >= 1)

    # 2. A quantidade total servida a cada cliente deve ser igual à sua demanda
    if constraints_config.get("serve_exact_demand", False):
        for j in Customers:
            solver.Add(solver.Sum(amountServed[i, j] for i in Warehouses) == demand[j])

    # 3. A quantidade total servida por cada armazém não deve exceder sua capacidade multiplicada por x[i]
    if constraints_config.get("warehouse_capacity", False):
        for i in Warehouses:
            solver.Add(
                solver.Sum(amountServed[i, j] for j in Customers) <= capacity[i] * x[i]
            )

    # 4. amountServed[i][j] <= demanda[j] * y[i][j]
    if constraints_config.get("serve_demand_with_y", False):
        for i in Warehouses:
            for j in Customers:
                solver.Add(amountServed[i, j] <= demand[j] * y[i, j])

    # 5. y[i][j] <= x[i]
    if constraints_config.get("assign_to_open_warehouse", False):
        for i in Warehouses:
            for j in Customers:
                solver.Add(y[i, j] <= x[i])

    # 6. Se um armazém estiver aberto, ele deve ser utilizado em pelo menos 80% de sua capacidade
    if constraints_config.get("minimum_capacity_usage", False):
        for i in Warehouses:
            min_80_cap = math.floor(0.8 * capacity[i])  # arredondando para baixo
            solver.Add(
                solver.Sum(amountServed[i, j] for j in Customers) >= min_80_cap * x[i]
            )

    # 7. Certos pares de clientes não podem ser atendidos pelo mesmo armazém
    if constraints_config.get("prohibited_pairs", False):
        for c1, c2 in prohibited_pairs:
            # Ajustar índices se necessário (caso venham 1-based)
            c1_adj = c1 - 1
            c2_adj = c2 - 1
            for i in Warehouses:
                solver.Add(y[i, c1_adj] + y[i, c2_adj] <= 1)

    # 8. Dependência entre armazéns (x[i] <= x[j])
    if constraints_config.get("dependent_warehouses", False):
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
