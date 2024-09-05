def create_indexed_map(start, step, values=[]):
    indexed_map = {}
    index = start
    for value in values:
        indexed_map[index] = value
        index = index + step
    return indexed_map