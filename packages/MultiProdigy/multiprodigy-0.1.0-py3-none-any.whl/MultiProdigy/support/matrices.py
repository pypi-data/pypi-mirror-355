def identity_matrix(size: int) -> list[list[int]]:
    return [[1 if i == j else 0 for j in range(size)] for i in range(size)]
