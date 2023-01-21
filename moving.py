LEGEND = {
    ".": "snow",
    "|": "v_road",
    "-": "h_road",
    '#': 'place',
    '1': 'corner_road',
    '2': 'corner_road',
    '3': 'corner_road',
    '4': 'corner_road',
    0: 'emptyness'
}


def wide_field(board):
    # получим поле с расширенными границами
    field = board.copy()

    for y in range(len(field)):
        # расширяем границы каждой строки
        buffer = [0]
        buffer.extend(field[y])
        buffer.append(0)
        field[y] = buffer

    buffer = [0 for _ in range(len(field[0]))]
    field.append(buffer)

    buffer = [buffer]
    buffer.extend(field)

    return buffer


def make_move(enemies, field):
    try:
        map = field.board.copy()
        map = wide_field(map)

        # дошли до конца
        end_way = []

        for num_enemy in range(len(enemies)):
            enemy = enemies[num_enemy]
            res = enemy.go(map)
            if not res:
                end_way.append(num_enemy)

        for i in end_way:
            enemies[i].kill()
            enemies.__delitem__(i)
    except Exception:
        return False


def where_we_go(table, pos, pre_dir):
    try:
        x = pos[0] + 1
        y = pos[1] + 1
        # where from
        pre_dyr = tuple(-i for i in pre_dir)

        ways = [-1, 1]

        # searching for road
        move_y = 0
        for move_x in ways:
            neighbour = table[y + move_y][x + move_x]
            try:
                if (move_x, move_y) == pre_dyr:
                    print(f'{move_x, move_y}^оттуда пришли')
                    continue
                if 'road' in LEGEND[neighbour]:
                    print(f'{move_x, move_y}^road')
                    return x + move_x - 1, y + move_y - 1
            except KeyError:
                continue

        move_x = 0
        for move_y in ways:
            neighbour = table[y + move_y][x + move_x]
            try:
                # we were here
                if (move_x, move_y) == pre_dyr:
                    continue
                if 'road' in LEGEND[neighbour]:
                    return x + move_x - 1, y + move_y - 1
            except KeyError:
                continue
        return 'the end of the way'
    except Exception:
        return False
