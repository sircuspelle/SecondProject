def wide_field(board):
    # получим поле с расширенными границами
    field = board.copy()

    for y in range(len(field)):
        # расширяем границы каждой строки
        buffer = [0]
        buffer.extend(field[y])
        buffer.append(0)
        field[y] = buffer

    buffer = [0 for i in range(len(field[0]))]
    field.append(buffer)

    buffer = [buffer]
    buffer.extend(field)

    return buffer


def where_we_go(table, pos, pre_dir):
    x = pos[0] + 1
    y = pos[1] + 1
    pre_dyr = tuple(-i for i in pre_dir)
    print(pre_dyr)

    ways = [-1, 1]

    # searching for road
    move_y = 0
    for move_x in ways:
        neighbour = table[y + move_y][x + move_x]
        if (move_x, move_y) == pre_dyr:
            # print(f'{move_x, move_y}^оттуда пришли')
            continue
        if neighbour == '-':
            # print(f'{move_x, move_y}^road')
            return x + move_x - 1, y + move_y - 1

    move_x = 0
    for move_y in ways:
        neighbour = table[y + move_y][x + move_x]
        if (move_x, move_y) == pre_dyr:
            # print(f'{move_x, move_y}^оттуда пришли')
            continue
        if neighbour == '-':
            # print(f'{move_x, move_y}^road')
            return x + move_x - 1, y + move_y - 1

    return False
