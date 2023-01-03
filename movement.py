def load_matrix(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    level_map = list(map(lambda x: x.ljust(max_width, '.'), level_map))

    new_map = [[level_map[y][x] for x in range(max_width)] for y in range(len(level_map))]
    return new_map.copy()


board = load_matrix('map_0.txt')

def wide_field(field):
    # получим поле с расширенными границами
    buffer = [0 for i in range(len(field[0]))]
    field.append(buffer.copy())
    buffer.extend([0, 0])
    buffer = [buffer]
    buffer.extend(field)
    field = buffer
    buffer = [0]
    buffer.extend(field[0])
    buffer.append(0)
    field[1] = buffer

    for y in range(1, len(field) + 1):
        # расширяем границы каждой строки
        buffer = [0]
        buffer.extend(field[y + 1])
        buffer.append(0)
        field[y + 1] = buffer


def where_we_go(pos, table, pre_dyr):
    x = pos[1]
    y = pos[0]

    dyrx = pre_dyr[1]
    dyry = pre_dyr[0]

    # searching for road
    for move_y in range(-1, 2):
        for move_x in range(-1, 2):
            if (move_y, move_x) == pre_dyr:
                pass

            neighbour = table[y + move_y][x + move_x]
            if neighbour == '-':
                return move_y, move_x


