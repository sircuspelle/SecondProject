import os
import sys
import random
import pygame
import sqlite3
from moving import make_move, where_we_go

WIDTH, HEIGHT = 960, 720
CELL_SIZE = 80
START_CORDS = None
MONSTERS = None
COUNT = None
MONEYS = 20
GRAVITY = 1

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
shop_objects = pygame.sprite.Group()
particles_group = pygame.sprite.Group()
back_ground_group = pygame.sprite.Group()

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
    try:
        for i in range(len(cords)):
            if pos[0] in range(cords[i][0][0], cords[i][0][1]) \
                    and pos[1] in range(cords[i][1][0], cords[i][1][1]):
                return i
    except Exception:
        return False


def check_click(pos, cords):
    try:
        for i in range(3):
            if pos[0] in range(cords[i][0][0], cords[i][0][1]) \
                    and pos[1] in range(cords[i][1][0], cords[i][1][1]):
                return i + 1
    except Exception:
        return False



def set_money():
    money_image = load_image("money1.png")
    money_image = pygame.transform.scale(money_image, (50, 50))
    money = pygame.sprite.Sprite(objects_group)
    money.image = money_image
    money.rect = (20, 20)


def set_money_count(surface):
    color = pygame.Color('white')
    font = pygame.font.Font(None, 40)
    text = font.render(str(MONEYS), True, color)
    surface.blit(text, (70, 30))


def create_dict(table):
    # Подключение к БД
    dictionary = {}
    con = sqlite3.connect("data/information.sqlite")
    cur = con.cursor()
    # Выполнение запроса и получение всех результатов
    result = cur.execute(f"""pragma table_info({table})""").fetchall()
    result_1 = cur.execute(f"""SELECT * FROM {table}""").fetchall()
    for i in result_1:
        name = i[0]
        dictionary[name] = {}
        for j in range(1, len(result) - 1):
            elem = result[j][1]
            if elem == 'image':
                dictionary[name][elem] = load_image(i[j])
            else:
                dictionary[name][elem] = i[j]
    con.close()
    return dictionary


tile_images = {
    "place": load_image("place.png"),
    "snow": load_image("green1.png"),
    "v_road": load_image("road.png"),
    "h_road": load_image("road.png"),
    'corner_road': load_image("road_corner.png")
}

where_rotate = {  # на сколько градусов поворацивается тайл
    "#": None,
    ".": None,
    "|": None,
    "-": 90,
    '1': None,
    '2': 270,
    '3': 180,
    '4': 90
}

towers = create_dict('towers')


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_y, pos_x):
        super().__init__(objects_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(CELL_SIZE * pos_x, CELL_SIZE * pos_y)

    def rotate(self, angle):  # переворачиваем тайл
        self.image = pygame.transform.rotate(self.image, angle)


bullets = {
    "cannon": {
        'image': load_image("cannon_b.png"),
        'damage': 10
    },
    "ice_tower": {
        'image': load_image("cannon_b.png"),
        'damage': 34
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
        gr_v = self.vel_x * 0.7, self.vel_y * 0.7
        create_particles((enemy.rect.x + CELL_SIZE // 2, enemy.rect.y + CELL_SIZE // 2), gr_v)
        s = pygame.mixer.Sound("Music/DamageEffect.ogg")
        s.play()
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


T = 15


def ballistrator(enemy_pos, bullet_pos, enemy_vel):
    enemy_x, enemy_y = enemy_pos
    bullet_x, bullet_y = bullet_pos
    vel_x, vel_y = enemy_vel

    delta_x = round((enemy_x - bullet_x + T * vel_x) / T, 0)
    delta_y = round((enemy_y - bullet_y + T * vel_y) / T, 0)

    return delta_x, delta_y


class Tower(pygame.sprite.Sprite):
    def __init__(self, tower_type, pos_y, pos_x, group=towers_group):
        super().__init__(group)
        self.image = towers[tower_type]['image']
        self.rect = self.image.get_rect().move(CELL_SIZE * pos_x, CELL_SIZE * pos_y)
        self.type = tower_type
        self.x = pos_x
        self.y = pos_y

    def shout(self, enemy):
        # print('стреляю')

        dir_x = enemy.target[0] - enemy.x
        dir_y = enemy.target[1] - enemy.y

        vel_x = enemy.vel * dir_x
        vel_y = enemy.vel * dir_y

        # here i am adding 30 to get left up end of bullet sprite knowing left up tower end
        rect = CELL_SIZE * self.x + 30, CELL_SIZE * self.y + 30

        enemy_center = enemy.rect.x + CELL_SIZE // 2, enemy.rect.y + CELL_SIZE // 2

        Bullet(self.type, ballistrator(enemy_center, rect, (vel_x, vel_y)), rect)


enemies = create_dict('enemies')


class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type, pos_y, pos_x):
        super().__init__(enemies_group)
        self.image = enemies[enemy_type]['image']
        self.enemy_type = enemy_type
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(CELL_SIZE * pos_x, CELL_SIZE * pos_y)
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
            return False
        elif self.target == 'the end of the way':
            # monster achieve the end'
            if self in enemies_group:
                global lose
                lose = True
            return False
        else:
            self.rect.x += self.vel * (self.target[0] - self.x)
            self.rect.y += self.vel * (self.target[1] - self.y)
            return True

    def die(self):
        global MONEYS
        MONEYS += enemies[self.enemy_type]["moneys"]
        self.kill()


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [['.' for _ in range(width)] for _ in range(height)]
        # standard
        self.left = 0
        self.top = 0
        self.cell_size = 10
        self.towers = []
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
                    tile = Tile(LEGEND[mean], y, x)
                    if not (where_rotate[mean] is None):
                        tile.rotate(where_rotate[mean])
                except KeyError:
                    print(1)
                    Tile('place', y, x)
        set_money()  # Устанавливаем спрайт монеты

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
        return self.on_click(cell)  # надо возвращать

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
        for tower in towers_group:
            if tower == self.board[x][y]:
                tower.kill()
        tower = Tower(tower_type, x, y)
        self.board[x][y] = tower

    def render_tower(self, y, x, tower_type):  # для отрисовки башен
        self.towers.append([y, x, tower_type])


FONT = "ofont.ru_Arlekino.ttf"


class InitialWindow:
    def __init__(self, surface):
        self.surface = surface
        self.phases = [0, 0, 0]
        self.cords = [[], []]
        self.x = 250
        self.y1, self.y2 = 250, 400
        pygame.mixer.music.load("Music\MainTheme.mp3")
        pygame.mixer.music.play(-1)

    def draw(self):
        self.drawing_labels(self.y1, 'Новая игра', 0)
        self.drawing_labels(self.y2, 'Справка', 1)

    def drawing_labels(self, y, text, text_phase):
        color1, color2 = pygame.Color('white'), pygame.Color('red')
        font1, font2 = pygame.font.Font(FONT, 100), pygame.font.Font(FONT, 115)
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


class AnnotationWindow:
    def __init__(self, canvas):
        self.canvas = canvas
        self.reference_text = ['Потом здесь будет справка о игре', 'Сейчас её нет', 'Точно нет']

    def draw(self):
        self.draw_reference()
        font = pygame.font.Font(None, 70)
        txt = font.render('X', True, pygame.Color('white'))
        self.canvas.blit(txt, (920, 10))

    def draw_reference(self):
        font = pygame.font.Font(FONT, 70)
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
        for i in range(3):
            self.drawing_labels(self.x + 300 * i, f'Локация {i + 1}', i)
        font = pygame.font.Font(None, 70)
        txt = font.render('X', True, pygame.Color('white'))
        self.side.blit(txt, (920, 10))

    def drawing_labels(self, x, text, text_phase):
        color1, color2 = pygame.Color('white'), pygame.Color('red')
        font = pygame.font.Font(FONT, 55)
        txt = None
        if self.conditions[text_phase] == 0:
            txt = font.render(text, True, color1)
        elif self.conditions[text_phase] == 1:
            txt = font.render(text, True, color2)
        self.cords[text_phase] = [[x, x + txt.get_width()], [self.y, self.y + txt.get_height()]]
        self.side.blit(txt, (x, self.y))


class Shop:  # Магазин
    def __init__(self, width, height, side):
        self.width, self.height = width, height
        self.side = side
        self.shop = pygame.Surface((self.width, self.height))  # слой магазина
        self.shop.fill((pygame.Color('red')))
        self.color1 = pygame.Color('white')
        self.color2 = pygame.Color('gray')
        self.towers = [towers[i]['image'] for i in list(towers)]
        self.cannons = list(towers)
        self.prices = [towers[i]['price'] for i in list(towers)]
        self.names = [towers[i]['shop_name'] for i in list(towers)]
        self.btn_cords = [[]] * len(self.towers)

    def draw(self):
        self.side.blit(self.shop, (self.width, 0))
        for i in range(len(self.cannons)):
            Tower(self.cannons[i], 1 + i * 2, 7, shop_objects)
            self.draw_name(self.names[i], self.color1, i * CELL_SIZE)
            if MONEYS >= int(self.prices[i]):
                self.draw_buy_btn(self.color1, i * CELL_SIZE, i)
            else:
                self.draw_buy_btn(self.color2, i * CELL_SIZE, i)
            self.draw_price(self.prices[i], self.color1, i * CELL_SIZE)

    def draw_name(self, name, color, cell):  # рисуем название пушки
        font = pygame.font.Font(None, 40)
        text = font.render(name, True, color)
        self.shop.blit(text, ((self.width - text.get_width()) // 2, CELL_SIZE * 1.1 + cell * 2))

    def draw_price(self, price, color, cell):
        font = pygame.font.Font(None, 40)
        text = font.render(f'{price} монет', True, color)
        self.shop.blit(text, ((self.width - text.get_width()) // 2, CELL_SIZE * 1.6 + cell * 2))

    def draw_buy_btn(self, color, cell, count):  # Рисуем кнопку и берём её координаты
        font = pygame.font.Font(None, 60)
        text = font.render('Купить', True, color)
        self.shop.blit(text, (self.width - text.get_width(), CELL_SIZE * 1.3 + cell * 2))
        # беру координаты кнопки для последующей проверки нажатия
        self.btn_cords[count] = [[self.width * 2 - text.get_width(), self.width * 2],
                                [int(CELL_SIZE * 1.3 + cell * 2), int(CELL_SIZE * 1.3 + cell * 2 + text.get_height())]]
        print(self.btn_cords)


# событие новый враг
NEW_ENEMY = pygame.USEREVENT + 1
pygame.time.set_timer(NEW_ENEMY, 3000)


# событие стрельба
# SHOUT = pygame.USEREVENT + 2
# pygame.time.set_timer(NEW_ENEMY, 500)


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
        dist = lambda x: (x.rect.x + 40 - tower_cords[0]) ** 2 + (
                x.rect.y + 40 - tower_cords[1]) ** 2
        # we sort all enemies by distance
        killers = sorted(killers, key=dist)
        enemy = killers[0]
        # check if it in fire zone
        if dist(enemy) ** 0.5 <= CELL_SIZE * 2.1:
            tower.shout(enemy)
        # bullet_fly()


...
# для отслеживания улетевших частиц
# удобно использовать пересечение прямоугольников
screen_rect = (0, 0, WIDTH, HEIGHT)


def create_particles(position, gr):
    # количество создаваемых частиц
    particle_count = 20
    # возможные скорости
    numbers = range(-2, 2)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers), gr)


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    first = load_image("boom.png")
    fire = []
    for scale in (10, 20, 30):
        fire.append(pygame.transform.scale(first, (scale, scale)))

    def __init__(self, pos, dx, dy, gr):
        super().__init__(particles_group)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы)
        self.gravity_x, self.gravity_y = gr

    def update(self):
        # применяем гравитационный эффект:
        # движение с ускорением под действием гравитации
        self.velocity[0] += self.gravity_x
        self.velocity[1] += self.gravity_y
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # убиваем, если частица ушла за экран
        if not self.rect.colliderect(screen_rect):
            self.kill()


class BackGround(pygame.sprite.Sprite):
    image = load_image("back.png")

    def __init__(self, *group):
        # НЕОБХОДИМО вызвать конструктор родительского класса Sprite.
        # Это очень важно!!!
        super().__init__(*group)
        self.image = BackGround.image
        self.image = pygame.transform.scale(self.image, (960, 720))
        self.rect = self.image.get_rect()


# основной игровой цикл
# создадим и загрузим поле

font1 = pygame.font.Font(None, 70)
txt = font1.render('X', None, pygame.Color('white'))
font1 = pygame.font.Font(None, 100)
lose_sign = font1.render('Вы проиграли', True, pygame.Color('white'))
win_sign = font1.render('Вы выйграли', True, pygame.Color('white'))
board = Board(12, 9)
board.set_view(0, 0, CELL_SIZE)

where_set_tower = None

initial_window = InitialWindow(screen)
reference_window = AnnotationWindow(screen)
select_locations = SelectLocationsWindow(screen)
shop = Shop(WIDTH // 2, HEIGHT, screen)

entry_upper = True
reference = False
main_window = False
select_lvl = False

shop_open = False
running = True

wave = 0
num = 0
killers = []
attack = True
new_wave = False
rendered = False
lose = False
win = False
sounded = False
BackGround(back_ground_group)


def restart():
    global board
    board = Board(12, 9)
    board.set_view(0, 0, CELL_SIZE)
    global shop_open, num, wave, attack, new_wave, rendered, killers, lose, win, sounded
    global objects_group, towers_group, bullets_group, enemies_group, particles_group, MONEYS
    objects_group.empty()
    bullets_group.empty()
    towers_group.empty()
    enemies_group.empty()
    particles_group.empty()
    shop_open = False
    MONEYS = 100
    wave = 0
    num = 0
    killers = []
    attack = True
    new_wave = False
    rendered = False
    lose = False
    win = False
    sounded = False


while running:
    # основные действия
    # print(entry_upper, select_lvl, reference, main_window)
    screen.fill((0, 0, 0))
    if not main_window:
        back_ground_group.draw(screen)
    if main_window:
        if not rendered:
            FPS = 60
            objects_group.empty()
            board.render()
            rendered = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[0] in range(920, 952) and event.pos[1] in range(10, 58):
                    pygame.mixer.music.load(f"Music/MainTheme.mp3")
                    pygame.mixer.music.play(-1)
                    select_lvl = True
                    main_window = False
                # print('click')
                if not shop_open and not lose:
                    # print('need?')
                    if board.get_click(event.pos) == '#' or isinstance(board.get_click(event.pos),
                                                                       Tower):
                        # при нажатии по нужной клетке отрисовывается магазин
                        where_set_tower = board.get_cell(event.pos)
                        shop_open = True
                else:
                    # print('buy or close?')
                    if event.pos[0] > WIDTH // 2 and shop_open:
                        # проверяем пытается ли человек купить пушку
                        check = check_click(event.pos, shop.btn_cords)
                        if check:
                            cannon = list(towers)[check - 1]
                            if MONEYS >= int(towers[cannon]['price']):
                                board.set_tower(where_set_tower[1], where_set_tower[0],
                                                list(towers)[check - 1])
                                MONEYS -= int(towers[cannon]['price'])
                                shop_open = False
                                rendered = False
                    elif event.pos[0] < WIDTH // 2 and shop_open:
                        where_set_tower = None
                        shop_open = False
            # запускаем врагов
            if event.type == NEW_ENEMY and attack and not shop_open and not (lose or win):
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
            if not attack and not lose and not enemies_group:
                win = True

        if not shop_open and not (lose or win):
            make_move(killers, board)
            # print(pygame.time.get_ticks())
            if not pygame.time.get_ticks() % 15:
                make_shout(towers_group, enemies_group)
            bullet_fly()
        objects_group.draw(screen)
        screen.blit(txt, (920, 10))
        towers_group.draw(screen)
        bullets_group.draw(screen)
        enemies_group.draw(screen)
        particles_group.update()
        particles_group.draw(screen)
        if lose or win:
            if lose:
                screen.blit(lose_sign, (
                    (WIDTH - lose_sign.get_width()) // 2, (HEIGHT - lose_sign.get_height()) // 2))
                sound = pygame.mixer.Sound("Music/lose_sound.ogg")
            if win:
                screen.blit(win_sign, (
                    (WIDTH - lose_sign.get_width()) // 2, (HEIGHT - lose_sign.get_height()) // 2))
                sound = pygame.mixer.Sound("Music/win_sound.ogg")
            if not sounded:
                pygame.mixer.music.stop()
                sound.play()
                sounded = True
        if shop_open:
            shop.draw()
            shop_objects.draw(shop.side)
        set_money_count(screen)
    elif reference:
        reference_window.draw()
    elif select_lvl:
        select_locations.draw()
    elif entry_upper:
        initial_window.draw()
    if entry_upper or select_lvl or reference:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEMOTION:
                if select_lvl:
                    phase = check_motion(event.pos, select_locations.cords)
                    select_locations.conditions = [0] * len(select_locations.conditions)
                    if phase or phase == 0:
                        select_locations.conditions[phase] = 1
                elif entry_upper:
                    phase = check_motion(event.pos, initial_window.cords)
                    initial_window.phases = [0] * len(initial_window.phases)
                    if phase or phase == 0:
                        initial_window.phases[phase] = 1
            if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                if reference:
                    if event.pos[0] in range(920, 952) and event.pos[1] in range(10, 58):
                        reference = False
                        entry_upper = True
                elif select_lvl:
                    check = check_click(event.pos, select_locations.cords)
                    if event.pos[0] in range(920, 952) and event.pos[1] in range(10, 58):
                        select_lvl = False
                        entry_upper = True
                    if not (check is None):
                        select_locations.conditions = [0] * len(select_locations.conditions)
                        try:
                            restart()
                            print('restarted succesfully')
                            board.load_level(f"lvl_{check}.txt")
                            START_CORDS = board.START_CORDS
                            MONSTERS = board.MONSTERS
                            COUNT = board.COUNT
                            print(f'lvl_{check} loaded:', START_CORDS, MONSTERS, COUNT)
                            pygame.mixer.music.load(f"Music/Location{check}.mp3")
                            pygame.mixer.music.play(-1)
                            print('music loaded')
                            select_lvl = False
                            main_window = True
                        except:
                            print('error')
                            continue
                elif entry_upper:
                    check = check_click(event.pos, initial_window.cords)
                    if not (check is None):
                        initial_window.phases = [0] * 3
                    if check == 1:
                        select_lvl = True
                        entry_upper = False
                    elif check == 2:
                        reference = True
                        entry_upper = False

    clock.tick(FPS)
    pygame.display.flip()
pygame.quit()
