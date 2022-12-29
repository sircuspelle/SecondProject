import os
import sys
import pygame

FPS = 50
WIDTH, HEIGHT = 960, 720
CELL_SIZE = 80

pygame.init()
pygame.display.set_caption('Инициализация игры')
size = WIDTH, HEIGHT
screen = pygame.display.set_mode(size)

objects_group = pygame.sprite.Group()
bullets_group = pygame.sprite.Group()

LEGEND = {
    ".": "grass",
    "-": "road"
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


def load_level(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


objects_images = {
    "cannon": load_image("cannon1.png"),
    "place": load_image("place.png"),
    "grass": load_image("green1.png"),
    "road": load_image("gray1.png")
}

bullets_images = {
    "cannon": load_image("cannon.png")
}


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_y, pos_x):
        super().__init__(objects_group)
        self.image = objects_images[tile_type]
        self.rect = self.image.get_rect().move(CELL_SIZE * pos_x, CELL_SIZE * pos_y)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, bullet_type, vec_y, vec_x, y, x):
        super().__init__(objects_group)
        self.image = bullets_images[bullet_type]
        self.rect = self.image.get_rect().move(
            CELL_SIZE * x, CELL_SIZE * y)
        self.vec_x = vec_x
        self.vec_y = vec_y


class Tower(pygame.sprite.Sprite):
    def __init__(self, tower_type, pos_y, pos_x):
        super().__init__(objects_group)
        self.image = objects_images[tower_type]
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


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [['.'] * width for _ in range(height)]
        self.set_view(0, 0, 120)

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def render(self):
        # рисуем сам объект
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
        filename = 'data/' + filename
        with open(filename, 'r', encoding='utf8') as NewField:
            field = NewField.read().split('\n')
            self.board = field

    def set_tower(self, y, x, tower_type):
        self.board[y][x] = Tower(tower_type, y, x)


class InitialWindow:
    def __init__(self, surface):
        self.surface = surface
        self.phases = [0, 0, 0]
        self.cords = [[], [], []]
        self.x = 125
        self.y1, self.y2, self.y3 = 70, 125, 180

    def draw(self):
        self.surface.fill((0, 0, 0))
        self.drawing_labels(self.y1, 'Новая игра', 0)
        self.drawing_labels(self.y2, 'Продолжить', 1)
        self.drawing_labels(self.y3, 'Справка', 2)

    def drawing_labels(self, y, text, text_phase):
        color1, color2 = pygame.Color('white'), pygame.Color('red')
        font1, font2 = pygame.font.Font(None, 60), pygame.font.Font(None, 75)
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

    def check(self, pos):
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


# основной игровой цикл

# создадим и загрузим поле
board = Board(12, 9)
board.load_matrix("lvl_1.txt")
# запустим входное меню
initial_board = InitialWindow(screen)

entry_upper = True
reference = False
main_window = False
running = True
while running:

    if entry_upper:
        initial_board.draw()
    elif main_window:
        board.render()
        board.set_tower(5, 2, 'cannon')

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEMOTION:
            if entry_upper:
                phase = initial_board.check(event.pos)
                initial_board.phases = [0] * len(initial_board.phases)
                if phase or phase == 0:
                    initial_board.phases[phase] = 1
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
            if reference:
                reference = False
                entry_upper = True
            elif entry_upper:
                if event.pos[0] in range(initial_board.cords[0][0][0], initial_board.cords[0][0][1]) \
                        and event.pos[1] in range(initial_board.cords[0][1][0],
                                                  initial_board.cords[0][1][1]):
                    entry_upper = False
                    main_window = True
                elif event.pos[0] in range(initial_board.cords[2][0][0],
                                           initial_board.cords[2][0][1]) \
                        and event.pos[1] in range(initial_board.cords[2][1][0],
                                                  initial_board.cords[2][1][1]):
                    screen.fill((0, 0, 0))
                    entry_upper = False
                    reference = True
                    font = pygame.font.Font(None, 50)
                    txt = font.render('Позже здесь будет справка о игре', True,
                                      pygame.Color('white'))
                    screen.blit(txt, (WIDTH // 2, HEIGHT // 2))

    objects_group.draw(screen)
    pygame.display.flip()

pygame.quit()
