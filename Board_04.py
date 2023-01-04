import os
import sys
import pygame

from movement import wide_field, where_we_go


WIDTH, HEIGHT = 960, 720
CELL_SIZE = 80

pygame.init()
pygame.display.set_caption('Инициализация игры')
size = WIDTH, HEIGHT
screen = pygame.display.set_mode(size)

FPS = 60
clock = pygame.time.Clock()

objects_group = pygame.sprite.Group()
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


tile_images = {
    "place": load_image("place.png"),
    "grass": load_image("green1.png"),
    "road": load_image("gray1.png")
}

tower_images = {
    "cannon": load_image("cannon1.png"),
}

bullets = {
    "cannon": {
        'image': load_image("cannon.png"),
        'damage': 50
    }
}


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_y, pos_x):
        super().__init__(objects_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(CELL_SIZE * pos_x, CELL_SIZE * pos_y)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, bullet_type, vec_y, vec_x, y, x):
        super().__init__(objects_group)
        self.image = bullets[bullet_type]['image']
        self.rect = self.image.get_rect().move(
            CELL_SIZE * x, CELL_SIZE * y)
        self.damage = bullets[bullet_type]['damge']
        self.vec_x = vec_x
        self.vec_y = vec_y

    def hit(self, enemy):
        enemy.hp -= self.damage
        self.kill()


class Tower(pygame.sprite.Sprite):
    def __init__(self, tower_type, pos_y, pos_x):
        super().__init__(objects_group)
        self.image = tower_images[tower_type]
        self.rect = self.image.get_rect().move(CELL_SIZE * pos_x, CELL_SIZE * pos_y)
        self.type = tower_type
        self.x = pos_x
        self.y = pos_y

    def shout(self, matrix):
        for y in range(1, -2, -1):
            for x in range(-1, 2):
                if matrix[self.y + y][self.x + x] == '^':
                    Bullet(self.type, y, x, self.y, self.x)
                    return True
        return False

enemies = {
    'yeti': {
        'image': load_image("yeti.png"),
        'hp': 100,
        'vel': 40
    }
}

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type, pos_y, pos_x):
        super().__init__(enemies_group)
        self.image = enemies[enemy_type]['image']
        self.rect = self.image.get_rect().move(CELL_SIZE * pos_x, CELL_SIZE * pos_y)
        self.x = pos_x
        self.y = pos_y
        self.hp = enemies[enemy_type]['hp']
        self.vel = enemies[enemy_type]['vel']
        self.diry = 0
        self.dirx = 0

    def go(self, dirx, diry):
        self.rect.x += self.vel * dirx
        self.rect.y += self.vel * diry



class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [['.' for x in range(width)] for y in range(height)]
        self.left = 0
        self.top = 0
        self.cell_size = 10

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

        # print((x_cord, y_cord))
        return x_cord, y_cord

    def on_click(self, cell_cords):
        if cell_cords is None:
            return None
        x_cord, y_cord = cell_cords
        return self.board[y_cord][x_cord]

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        self.on_click(cell)

    def load_matrix(self, filename):
        filename = "data/" + filename
        # читаем уровень, убирая символы перевода строки
        with open(filename, 'r') as mapFile:
            level_map = [line.strip() for line in mapFile]

        # и подсчитываем максимальную длину
        max_width = max(map(len, level_map))

        # дополняем каждую строку пустыми клетками ('.')
        level_map = list(map(lambda x: x.ljust(max_width, '.'), level_map))

        new_map = [[level_map[y][x] for x in range(max_width)] for y in range(len(level_map))]
        self.board = new_map.copy()

    def set_tower(self, y, x, tower_type):
        tower = Tower(tower_type, y, x)
        self.board[y][x] = tower


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

NEW_ENEMY = pygame.USEREVENT + 1
pygame.time.set_timer(NEW_ENEMY, 5000)




# основной игровой цикл
# создадим и загрузим поле

board = Board(12, 9)
board.set_view(0, 0, CELL_SIZE)
board.load_matrix("lvl_1.txt")

killers = []

def make_move(enemies, field):
    map = field.board.copy()
    map = wide_field(map)

    for enemy in enemies:
        pos = (enemy.x, enemy.y)
        pre_dyr = (enemy.diry, enemy.dirx)
        enemy.go(*where_we_go(pos, map, pre_dyr))


# (x, y)
start_cords = (11, 5)
start = (CELL_SIZE * start_cords[0], CELL_SIZE * start_cords[1])
MONSTERS = [['yeti', 'yeti'], ['yeti']]
count = [len(MONSTERS[w]) for w in range(len(MONSTERS))]


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
attack = True


while running:
    # основные действия
    if main_window:
        FPS = 5
        board.render()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                board.get_click(event.pos)
            # запускаем врагов
            if event.type == NEW_ENEMY and attack:
                killers.append(Enemy(MONSTERS[wave][num], start_cords[1], start_cords[0]))
                if num == (count[wave] - 1):
                    num = 0
                    wave += 1
                    if wave == len(MONSTERS):
                        attack = False
                else:
                    num += 1

                print(killers)

        make_move(killers, board)

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
                if not(phase is None):
                    select_locations.conditions[phase] = 1
            elif entry_upper:
                phase = check_motion(event.pos, initial_window.cords)
                initial_window.phases = [0] * len(initial_window.phases)
                if not(phase is None):
                    initial_window.phases[phase] = 1
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
            if reference:
                if event.pos[0] in range(920, 952) and event.pos[1] in range(10, 58):
                    reference = False
            elif select_lvl:
                check = check_click(event.pos, select_locations.cords)
                if not(check is None):
                    select_lvl = False
                    main_window = True
                    board.load_matrix(f"lvl_{check}.txt")
            elif entry_upper:
                check = check_click(event.pos, initial_window.cords)
                if not(check is None):
                    initial_window.phases = [0] * 3
                if check == 1:
                    select_lvl = True
                elif check == 3:
                    reference = True

    objects_group.draw(screen)
    enemies_group.draw(screen)
    clock.tick(FPS)
    pygame.display.flip()
pygame.quit()
