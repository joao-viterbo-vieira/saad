import re
import ast


def read_data_file_antigo(filename):
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
    #    Procuramos algo do tipo "fixedCost = [ ... ];"
    fixedCost_match = re.search(r"fixedCost\s*=\s*\[(.*?)\];", content, re.DOTALL)
    fixedCost_str = fixedCost_match.group(1)
    # Converter a string em lista
    fixedCost = [float(x) for x in fixedCost_str.replace("\n", "").split(",")]

    # 4) Extrair capacity
    capacity_match = re.search(r"capacity\s*=\s*\[(.*?)\];", content, re.DOTALL)
    capacity_str = capacity_match.group(1)
    capacity = [float(x) for x in capacity_str.replace("\n", "").split(",")]

    # 5) Extrair demand
    demand_match = re.search(r"demand\s*=\s*\[(.*?)\];", content, re.DOTALL)
    demand_str = demand_match.group(1)
    demand = [float(x) for x in demand_str.replace("\n", "").split(",")]

    # 6) Extrair transportCost, que é uma matriz
    #    Aqui podemos tentar 'literal_eval' caso esteja em formato compatível com Python
    transportCost_match = re.search(
        r"transportCost\s*=\s*\[(.*?)\];", content, re.DOTALL
    )
    transportCost_str = transportCost_match.group(1).strip()

    # Ajustes para ficar num formato Python: coloca chaves externas "[]" e remove quebras se preciso
    transportCost_str = "[" + transportCost_str + "]"
    transportCost_str = transportCost_str.replace(";", "")  # remover ';' se existirem
    transportCost = ast.literal_eval(transportCost_str)

    # Atenção colocar as restrições extras aqui pode ser necessário acrescentar ou retirar.

    return nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost


# 1) Ler dados do ficheiro
(nWarehouses, nCustomers, fixedCost, capacity, demand, transportCost) = read_data_file(
    "facility_location.dat"
)
# dar print dos valores
print("nWarehouses = ", nWarehouses)
print("nCustomers = ", nCustomers)
print("fixedCost = ", fixedCost)
print("capacity = ", capacity)
print("demand = ", demand)
print("transportCost = ", transportCost)
