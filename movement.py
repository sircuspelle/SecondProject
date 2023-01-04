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


def where_we_go(pos, table, pre_dyr):
    x = pos[0] + 1
    y = pos[1] + 1

    # searching for road
    for move_y in range(-1, 2):
        for move_x in range(-1, 2):
            if (move_y, move_x) == pre_dyr:
                pass

            neighbour = table[y + move_y][x + move_x]
            if neighbour == '-':
                print(f'{x}-{move_x}, {y}-{move_y}')
                return move_x, move_y