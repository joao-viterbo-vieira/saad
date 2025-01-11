# Adjust indices to zero-based
prohibited_pairs = [(i - 1, i) for i in range(2, 51, 2)]  # Sequential pairs
prohibited_pairs += [
    (i, j) for i in range(5, 50, 5) for j in range(5, 50, 5) if i < j
]  # Multiples of 5

# conceito adicionado - warehouses que tem que ser abertos se determinado warehouses for aberto

# Initialize the dependent_warehouses array
dependent_warehouses = []

# Create dependency pairs for the first 5 warehouses
for i in range(5):
    dependent_warehouses.append((i, i + 5))

print("prohibited_pairs =", prohibited_pairs)
print("dependent_warehouses =", dependent_warehouses)
