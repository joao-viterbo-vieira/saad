import re
import ast


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


if __name__ == "__main__":
    # Exemplo de uso
    (
        nWarehouses,
        nCustomers,
        fixedCost,
        capacity,
        demand,
        transportCost,
        prohibited_pairs,
        dependent_warehouses,
    ) = read_data_file("teste.txt")

    print("nWarehouses =", nWarehouses)
    print("nCustomers =", nCustomers)
    print("fixedCost =", fixedCost)
    print("capacity =", capacity)
    print("demand =", demand)
    print("transportCost =", transportCost)
    print("prohibited_pairs =", prohibited_pairs)
    print("dependent_warehouses =", dependent_warehouses)
