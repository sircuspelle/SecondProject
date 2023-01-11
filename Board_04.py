import os
import sys
import pygame

WIDTH, HEIGHT = 960, 720
CELL_SIZE = 80

pygame.init()
pygame.display.set_caption('Инициализация игры')
size = WIDTH, HEIGHT
screen = pygame.display.set_mode(size)

FPS = 60
clock = pygame.time.Clock()

objects_group = pygame.sprite.Group()
towers_group = pygame.sprite.Group()
bullets_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()

LEGEND = {
    ".": "grass",
    "-": "road",
    '#': 'place'
}


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def check_motion(pos, cords):
    for i in range(3):
        if pos[0] in range(cords[i][0][0], cords[i][0][1]) \
                and pos[1] in range(cords[i][1][0], cords[i][1][1]):
            return i
    return


def check_click(pos, cords):
    for i in range(3):
        if pos[0] in range(cords[i][0][0], cords[i][0][1]) \
                and pos[1] in range(cords[i][1][0], cords[i][1][1]):
            return i + 1
    return


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


def make_move(enemies, field):
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


tile_images = {
    "place": load_image("place.png"),
    "grass": load_image("green1.png"),
    "road": load_image("gray1.png")
}

tower_images = {
    "cannon": load_image("cannon1.png"),
}


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_y, pos_x):
        super().__init__(objects_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(CELL_SIZE * pos_x, CELL_SIZE * pos_y)

bullets = {
    "cannon": {
        'image': load_image("cannon_b.png"),
        'damage': 10
    }
}

class Bullet(pygame.sprite.Sprite):
    def __init__(self, bullet_type, vel, rect):
        super().__init__(bullets_group)
        self.image = bullets[bullet_type]['image']
        self.rect = self.image.get_rect().move(
            rect)
        self.damage = bullets[bullet_type]['damage']
        self.vel_x, self.vel_y = vel

    def hit(self, enemy):
        enemy.hp -= self.damage
        if enemy.hp <= 0:
            enemy.die()
        self.kill()

    def flight(self):
        # print('лечу')
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        if self.rect.x < 0 or self.rect.x > WIDTH:
            self.kill()
        if self.rect.y < 0 or self.rect.y > HEIGHT:
            self.kill()


T = 30

def ballistrator(enemy_pos, bullet_pos, enemy_vel):
    enemy_x, enemy_y = enemy_pos
    bullet_x, bullet_y = bullet_pos
    vel_x, vel_y = enemy_vel

    delta_x = round((enemy_x - bullet_x + T*vel_x) / T, 0)
    delta_y = round((enemy_y - bullet_y + T * vel_y) / T, 0)

    return delta_x, delta_y

class Tower(pygame.sprite.Sprite):
    def __init__(self, tower_type, pos_y, pos_x):
        super().__init__(towers_group)
        self.image = tower_images[tower_type]
        self.rect = self.image.get_rect().move(CELL_SIZE * pos_x, CELL_SIZE * pos_y)
        self.type = tower_type
        self.x = pos_x
        self.y = pos_y

    def shout(self, enemy):

        print('стреляю')

        dir_x = enemy.target[0] - enemy.x
        dir_y = enemy.target[1] - enemy.y

        vel_x = enemy.vel * dir_x
        vel_y = enemy.vel * dir_y


        # here i am adding 30 to get left up end of bullet sprite knowing left up tower end
        rect = CELL_SIZE * self.x + 30, CELL_SIZE * self.y + 30

        enemy_center = enemy.rect.x + CELL_SIZE//2, enemy.rect.y + CELL_SIZE//2

        Bullet(self.type, ballistrator((enemy_center), rect, (vel_x, vel_y)), rect)





enemies = {
    'yeti': {
        'image': load_image("yeti.png"),
        'hp': 100,
        'vel': 5
    }
}


class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type, pos_y, pos_x):
        super().__init__(enemies_group)
        self.image = enemies[enemy_type]['image']
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(CELL_SIZE * (pos_x + 0.5), CELL_SIZE * pos_y)
        self.x = pos_x
        self.y = pos_y
        self.hp = enemies[enemy_type]['hp']
        self.vel = enemies[enemy_type]['vel']
        self.target = (0, 0)

    def go(self, map):
        # we start to move
        if self.target == (0, 0):
            self.target = where_we_go(map, (self.x, self.y), self.target)
            # print('i am setting first target', self.target)
        else:
            # if we get the target, we set new
            tar_pos = self.target[0] * CELL_SIZE, self.target[1] * CELL_SIZE
            if tar_pos == (self.rect.x, self.rect.y):
                # print('i have got target', self.target, self.rect.x, self.rect.y)
                pre_dir = self.target[0] - self.x, self.target[1] - self.y
                self.x, self.y = self.rect.x // CELL_SIZE, self.rect.y // CELL_SIZE
                self.target = where_we_go(map, (self.x, self.y), pre_dir)
                # print('i am setting new target', self.target)

        # if we don't have place to go
        if not self.target:
            # print('fuck')
            return False
        else:
            self.rect.x += self.vel * (self.target[0] - self.x)
            self.rect.y += self.vel * (self.target[1] - self.y)
            return True

    def die(self):
        self.kill()


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [['.' for x in range(width)] for y in range(height)]
        # standart
        self.left = 0
        self.top = 0
        self.cell_size = 10
        # need
        self.START_CORDS = (0, 0)
        self.MONSTERS = []
        self.COUNT = []

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def render(self):
        for y in range(self.height):
            for x in range(self.width):
                mean = self.board[y][x]
                try:
                    Tile(LEGEND[mean], y, x)
                except KeyError:
                    Tile('place', y, x)

    def get_cell(self, mouse_pos):
        mice_x, mice_y = mouse_pos

        cond_0 = (mice_x < self.left) or (mice_x > (self.left + self.width * self.cell_size))
        cond_1 = (mice_y < self.top) or (mice_y > (self.top + self.height * self.cell_size))
        if cond_0 or cond_1:
            # print(None)
            return None

        x_cord = (mice_x - self.left) // self.cell_size
        y_cord = (mice_y - self.top) // self.cell_size

        print((x_cord, y_cord))
        return x_cord, y_cord

    def on_click(self, cell_cords):
        if cell_cords is None:
            return None
        x_cord, y_cord = cell_cords
        print(self.board[y_cord][x_cord])
        return self.board[y_cord][x_cord]

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        self.on_click(cell)

    def load_level(self, filename):
        filename = "data/" + filename
        # читаем уровень, убирая символы перевода строки
        with open(filename, 'r') as mapFile:
            level_map = [line.strip() for line in mapFile]

        info = level_map.copy()[0].split(';')
        self.START_CORDS = tuple(int(el) for el in info[0].split(','))
        self.MONSTERS = [el.split(',') for el in info[1].split('-')]
        self.COUNT = [len(self.MONSTERS[w]) for w in range(len(self.MONSTERS))]

        level_map = level_map[1:]
        # и подсчитываем максимальную длину
        max_width = max(map(len, level_map))

        # дополняем каждую строку пустыми клетками ('.')
        level_map = list(map(lambda x: x.ljust(max_width, '.'), level_map))

        new_map = [[level_map[y][x] for x in range(max_width)] for y in range(len(level_map))]
        self.board = new_map.copy()

    def set_tower(self, x, y, tower_type):
        tower = Tower(tower_type, x, y)
        self.board[x][y] = tower


class InitialWindow:
    def __init__(self, surface):
        self.surface = surface
        self.phases = [0, 0, 0]
        self.cords = [[], [], []]
        self.x = 250
        self.y1, self.y2, self.y3 = 250, 325, 400

    def draw(self):
        self.surface.fill((0, 0, 0))
        self.drawing_labels(self.y1, 'Новая игра', 0)
        self.drawing_labels(self.y2, 'Продолжить', 1)
        self.drawing_labels(self.y3, 'Справка', 2)

    def drawing_labels(self, y, text, text_phase):
        color1, color2 = pygame.Color('white'), pygame.Color('red')
        font1, font2 = pygame.font.Font(None, 100), pygame.font.Font(None, 115)
        if self.phases[text_phase] == 0:
            text = font1.render(text, True, color1)
            self.cords[text_phase] = [[self.x, self.x + text.get_width()],
                                      [y, y + text.get_height()]]
            self.surface.blit(text, (self.x, y))
        elif self.phases[text_phase] == 1:
            text = font2.render(text, True, color2)
            self.cords[text_phase] = [[self.x, self.x + text.get_width()],
                                      [y - 10, y + text.get_height() - 10]]
            self.surface.blit(text, (self.x, y - 10))

    def check_move(self, event, pos):
        if pos[0] in range(self.cords[0][0][0], self.cords[0][0][1]) \
                and event.pos[1] in range(self.cords[0][1][0], self.cords[0][1][1]):
            return 0
        elif event.pos[0] in range(self.cords[1][0][0], self.cords[1][0][1]) \
                and event.pos[1] in range(self.cords[1][1][0], self.cords[1][1][1]):
            return 1
        elif event.pos[0] in range(self.cords[2][0][0], self.cords[2][0][1]) \
                and event.pos[1] in range(self.cords[2][1][0], self.cords[2][1][1]):
            return 2
        return


class AnnotationWindow:
    def __init__(self, canvas):
        self.canvas = canvas
        self.reference_text = ['Потом здесь будет справка о игре', 'Сейчас её нет', 'Точно нет']

    def draw(self):
        self.canvas.fill((0, 0, 0))
        self.draw_reference()
        font = pygame.font.Font(None, 70)
        txt = font.render('X', True, pygame.Color('white'))
        self.canvas.blit(txt, (920, 10))

    def draw_reference(self):
        font = pygame.font.Font(None, 70)
        for i in range(len(self.reference_text)):
            txt = font.render(self.reference_text[i], True, pygame.Color('white'))
            text_width, text_height = txt.get_width(), txt.get_height()
            self.canvas.blit(txt, ((960 - text_width) // 2, 300 + int(text_height * 1.5) * i))


class SelectLocationsWindow:
    def __init__(self, side):
        self.side = side
        self.conditions = [0, 0, 0]
        self.cords = [[], [], []]
        self.x = 50
        self.y = 325

    def draw(self):
        self.side.fill((0, 0, 0))
        for i in range(3):
            self.drawing_labels(self.x + 300 * i, f'Локация {i + 1}', i)

    def drawing_labels(self, x, text, text_phase):
        color1, color2 = pygame.Color('white'), pygame.Color('red')
        font = pygame.font.Font(None, 75)
        txt = None
        if self.conditions[text_phase] == 0:
            txt = font.render(text, True, color1)
        elif self.conditions[text_phase] == 1:
            txt = font.render(text, True, color2)
        self.cords[text_phase] = [[x, x + txt.get_width()], [self.y, self.y + txt.get_height()]]
        self.side.blit(txt, (x, self.y))


# событие новый враг
NEW_ENEMY = pygame.USEREVENT + 1
pygame.time.set_timer(NEW_ENEMY, 3000)

# событие стрельба
SHOUT = pygame.USEREVENT + 2
pygame.time.set_timer(NEW_ENEMY, 500)

def bullet_fly():
    for bullet in bullets_group:
        bullet.flight()
        enemy = pygame.sprite.spritecollideany(bullet, enemies_group)
        if enemy:
            bullet.hit(enemy)

def make_shout(towers, killers):
    if not killers or not towers:
        return False
    for tower in towers:
        tower_cords = tower.rect.x + 40, tower.rect.y + 40
        dist = lambda x: (x.rect.x + 40 - tower_cords[0]) ** 2 + (x.rect.y + 40 - tower_cords[1]) ** 2
        # we sort all enemies by diatance
        killers = sorted(killers, key=dist)
        enemy = killers[0]
        # check if it in firezone
        if dist(enemy) ** 0.5 <= CELL_SIZE * 2.1:
            tower.shout(enemy)
        bullet_fly()







# основной игровой цикл
# создадим и загрузим поле

board = Board(12, 9)
board.set_view(0, 0, CELL_SIZE)


initial_window = InitialWindow(screen)
reference_window = AnnotationWindow(screen)
select_locations = SelectLocationsWindow(screen)

entry_upper = True
reference = False
main_window = False
select_lvl = False
running = True

wave = 0
num = 0
killers = []
attack = True
new_wave = False
rendered = False

while running:
    # основные действия
    if main_window:
        if not rendered:
            FPS = 30
            board.render()
            board.set_tower(6, 3, 'cannon')
            rendered = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                board.get_click(event.pos)
            # запускаем врагов
            if event.type == NEW_ENEMY and attack:
                if new_wave:
                    new_wave = False
                else:
                    if num == (COUNT[wave]):
                        num = 0
                        wave += 1
                        if wave == len(MONSTERS):
                            attack = False
                        else:
                            new_wave = True
                    else:
                        killers.append(Enemy(MONSTERS[wave][num], START_CORDS[1], START_CORDS[0]))
                        num += 1


        make_move(killers, board)
        if not clock.get_time() % 2:
            make_shout(towers_group, killers)
        else:
            bullet_fly()
        objects_group.draw(screen)
        towers_group.draw(screen)
        bullets_group.draw(screen)
        enemies_group.draw(screen)


    elif reference:
        reference_window.draw()
    elif select_lvl:
        select_locations.draw()
    elif entry_upper:
        initial_window.draw()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEMOTION:
            if select_lvl:
                phase = check_motion(event.pos, select_locations.cords)
                select_locations.conditions = [0] * len(select_locations.conditions)
                if not (phase is None):
                    select_locations.conditions[phase] = 1
            elif entry_upper:
                phase = check_motion(event.pos, initial_window.cords)
                initial_window.phases = [0] * len(initial_window.phases)
                if not (phase is None):
                    initial_window.phases[phase] = 1
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
            if reference:
                if event.pos[0] in range(920, 952) and event.pos[1] in range(10, 58):
                    reference = False
            elif select_lvl:
                check = check_click(event.pos, select_locations.cords)
                if not (check is None):
                    select_lvl = False
                    main_window = True
                    board.load_level(f"lvl_{check}.txt")
                    START_CORDS = board.START_CORDS
                    MONSTERS = board.MONSTERS
                    COUNT = board.COUNT
                    print(START_CORDS, MONSTERS, COUNT)
            elif entry_upper:
                check = check_click(event.pos, initial_window.cords)
                if not (check is None):
                    initial_window.phases = [0] * 3
                if check == 1:
                    select_lvl = True
                elif check == 3:
                    reference = True

    clock.tick(FPS)
    pygame.display.flip()
pygame.quit()