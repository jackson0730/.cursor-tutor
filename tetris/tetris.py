import pygame
import random
import os
import pygame.mixer

# 初始化 Pygame
pygame.init()

# 设置游戏窗口
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BLOCK_SIZE = 30

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
PREVIEW_COLOR = (128, 128, 128, 128)  # 半透明的灰色
PAUSED_TEXT_COLOR = (255, 255, 255)
RISING_BLOCK_COLOR = (70, 70, 70)  # 上升方块的深灰色

# 在颜色定义后添加游戏状态变量
score = 0
level = 1
lines_cleared_total = 0
game_over = False
paused = False
countdown_time = 30000  # 30秒倒计时（毫秒）
countdown_timer = countdown_time
last_rise_level = 1  # 上一次上升的层数

# 创建游戏窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('俄罗斯方块')

# 定义游戏区域大小
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_OFFSET_X = (WINDOW_WIDTH - GRID_WIDTH * BLOCK_SIZE) // 2
GRID_OFFSET_Y = (WINDOW_HEIGHT - GRID_HEIGHT * BLOCK_SIZE) // 2

# 定义方块形状
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

# 调整方块颜色为更暗的色调
LIGHT_CYAN = (100, 200, 200)
LIGHT_YELLOW = (200, 200, 100)
LIGHT_MAGENTA = (200, 100, 200)
LIGHT_RED = (200, 100, 100)
LIGHT_GREEN = (100, 200, 100)
LIGHT_BLUE = (100, 100, 200)
LIGHT_ORANGE = (200, 150, 100)

# 更新方块颜色
SHAPE_COLORS = [LIGHT_CYAN, LIGHT_YELLOW, LIGHT_MAGENTA, LIGHT_ORANGE, LIGHT_BLUE, LIGHT_GREEN, LIGHT_RED]

# 创建游戏网格
grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

# 初始化音频系统
pygame.mixer.init()

# 设置资源文件路径
ASSETS_DIR = "assets"
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# 字体设置
try:
    FONT_PATH = os.path.join(ASSETS_DIR, "calibri.ttf")
    game_font = pygame.font.Font(FONT_PATH, 36)
except:
    # 如果找不到 Calibri 字体，使用系统默认字体
    game_font = pygame.font.SysFont("calibri", 36)

# 加载音效
try:
    rotate_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "rotate.wav"))
    move_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "move.wav"))
    clear_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "clear.wav"))
    drop_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "drop.wav"))
    warning_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "warning.wav"))
    
    # 设置音量
    rotate_sound.set_volume(0.3)
    move_sound.set_volume(0.3)
    clear_sound.set_volume(0.5)
    drop_sound.set_volume(0.4)
    warning_sound.set_volume(0.6)
except:
    # 如果找不到音效文件，创建空的音效对象
    rotate_sound = move_sound = clear_sound = drop_sound = warning_sound = pygame.mixer.Sound(buffer=bytes(0))

# 加载背景音乐
try:
    pygame.mixer.music.load(os.path.join(ASSETS_DIR, "background.mp3"))
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)  # -1 表示循环播放
except:
    pass

def draw_grid():
    # 绘制游戏区域边框
    pygame.draw.rect(screen, WHITE, 
                    (GRID_OFFSET_X - 2, GRID_OFFSET_Y - 2, 
                     GRID_WIDTH * BLOCK_SIZE + 4, GRID_HEIGHT * BLOCK_SIZE + 4), 2)
    
    # 绘制网格线
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            pygame.draw.rect(screen, (50, 50, 50),
                           (GRID_OFFSET_X + x * BLOCK_SIZE,
                            GRID_OFFSET_Y + y * BLOCK_SIZE,
                            BLOCK_SIZE, BLOCK_SIZE), 1)

class Tetromino:
    def __init__(self):
        self.shape = random.choice(SHAPES)
        self.color = SHAPE_COLORS[SHAPES.index(self.shape)]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0
    
    def draw(self):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    # 绘制方块主体
                    pygame.draw.rect(screen, self.color,
                                   (GRID_OFFSET_X + (self.x + x) * BLOCK_SIZE,
                                    GRID_OFFSET_Y + (self.y + y) * BLOCK_SIZE,
                                    BLOCK_SIZE, BLOCK_SIZE))
                    # 绘制黑色边框
                    pygame.draw.rect(screen, BLACK,
                                   (GRID_OFFSET_X + (self.x + x) * BLOCK_SIZE,
                                    GRID_OFFSET_Y + (self.y + y) * BLOCK_SIZE,
                                    BLOCK_SIZE, BLOCK_SIZE), 1)
    
    def move(self, dx, dy):
        self.x += dx
        self.y += dy
    
    def can_move(self, dx, dy):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.x + x + dx
                    new_y = self.y + y + dy
                    if (new_x < 0 or new_x >= GRID_WIDTH or
                        new_y >= GRID_HEIGHT or
                        (new_y >= 0 and grid[new_y][new_x])):
                        return False
        return True
    
    def rotate(self):
        rotated_shape = list(zip(*self.shape[::-1]))
        old_shape = self.shape
        self.shape = [list(row) for row in rotated_shape]
        
        if not self.is_valid_position():
            self.shape = old_shape
        else:
            rotate_sound.play()  # 播放旋转音效
    
    def is_valid_position(self):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.x + x
                    new_y = self.y + y
                    if (new_x < 0 or new_x >= GRID_WIDTH or
                        new_y >= GRID_HEIGHT or
                        (new_y >= 0 and grid[new_y][new_x])):
                        return False
        return True

# 创建当前方块
current_piece = Tetromino()
fall_time = 0
fall_speed = 1000  # 每秒移动一格
last_time = pygame.time.get_ticks()

# 创建下一个方块
next_piece = Tetromino()

def lock_piece(piece):
    global next_piece
    # 将方块固定到网格中
    for y, row in enumerate(piece.shape):
        for x, cell in enumerate(row):
            if cell:
                grid[piece.y + y][piece.x + x] = piece.color
    # 更新当前方块为下一个方块
    current_piece.shape = next_piece.shape
    current_piece.color = next_piece.color
    current_piece.x = GRID_WIDTH // 2 - len(current_piece.shape[0]) // 2
    current_piece.y = 0
    # 生成新的下一个方块
    next_piece = Tetromino()

# 添加制文本的函数
def draw_text(text, size, color, x, y):
    font = pygame.font.SysFont("calibri", size)
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    rect.topleft = (x, y)
    screen.blit(surface, rect)

def check_game_over():
    # 检查新方块是否能放置在起始位置
    for x, cell in enumerate(current_piece.shape[0]):
        if cell and grid[current_piece.y][current_piece.x + x]:
            return True
    return False

# 修改 clear_lines 函数，返回得分
def clear_lines():
    global score, level, lines_cleared_total, fall_speed
    lines_cleared = 0
    y = GRID_HEIGHT - 1
    while y >= 0:
        if all(grid[y]):
            for move_y in range(y, 0, -1):
                grid[move_y] = grid[move_y - 1][:]
            grid[0] = [0] * GRID_WIDTH
            lines_cleared += 1
        else:
            y -= 1
    
    if lines_cleared > 0:
        clear_sound.play()  # 播放消除音效
        score += (lines_cleared * 100) * level
        lines_cleared_total += lines_cleared
        level = lines_cleared_total // 10 + 1
        fall_speed = max(100, 1000 - (level - 1) * 100)
    
    return lines_cleared

def draw_locked_pieces():
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x]:
                # 绘制方块主体
                pygame.draw.rect(screen, grid[y][x],
                               (GRID_OFFSET_X + x * BLOCK_SIZE,
                                GRID_OFFSET_Y + y * BLOCK_SIZE,
                                BLOCK_SIZE, BLOCK_SIZE))
                # 绘制黑色边框
                pygame.draw.rect(screen, BLACK,
                               (GRID_OFFSET_X + x * BLOCK_SIZE,
                                GRID_OFFSET_Y + y * BLOCK_SIZE,
                                BLOCK_SIZE, BLOCK_SIZE), 1)

def draw_next_piece():
    # 绘制下一个方块
    start_x = WINDOW_WIDTH - 150
    start_y = 50
    draw_text("Next:", 36, WHITE, start_x, start_y - 40)
    for y, row in enumerate(next_piece.shape):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(screen, next_piece.color,
                               (start_x + x * BLOCK_SIZE,
                                start_y + y * BLOCK_SIZE,
                                BLOCK_SIZE, BLOCK_SIZE))
                pygame.draw.rect(screen, BLACK,
                               (start_x + x * BLOCK_SIZE,
                                start_y + y * BLOCK_SIZE,
                                BLOCK_SIZE, BLOCK_SIZE), 1)

# 添加按键延迟控制常量
INITIAL_DELAY = 200  # 首次按下到开始持续移动的延迟（毫秒）
MOVE_REPEAT = 50    # 持续移动时的间隔（毫秒）

# 修改游戏主循环
running = True
fast_fall_speed = 50  # 快速下落时的速度（毫秒）
normal_fall_speed = 1000  # 正常下落速度（毫秒）
current_fall_speed = normal_fall_speed

# 添加按键状态和计时器
keys = {
    pygame.K_LEFT: {"pressed": False, "time": 0},
    pygame.K_RIGHT: {"pressed": False, "time": 0},
    pygame.K_DOWN: {"pressed": False, "time": 0}
}

# 添加获取落点位置的函数
def get_ghost_position(piece):
    ghost_y = piece.y
    while piece.can_move(0, ghost_y - piece.y + 1):
        ghost_y += 1
    return ghost_y

# 添加绘制预览方块的函数
def draw_ghost_piece(piece):
    ghost_y = get_ghost_position(piece)
    for y, row in enumerate(piece.shape):
        for x, cell in enumerate(row):
            if cell:
                # 绘制半透明的预览方块
                pygame.draw.rect(screen, PREVIEW_COLOR,
                               (GRID_OFFSET_X + (piece.x + x) * BLOCK_SIZE,
                                GRID_OFFSET_Y + (ghost_y + y) * BLOCK_SIZE,
                                BLOCK_SIZE, BLOCK_SIZE))
                # 绘制虚线边框
                for i in range(0, BLOCK_SIZE, 4):  # 每4像素画一个点
                    pygame.draw.rect(screen, WHITE,
                                   (GRID_OFFSET_X + (piece.x + x) * BLOCK_SIZE + i,
                                    GRID_OFFSET_Y + (ghost_y + y) * BLOCK_SIZE,
                                    2, 1))  # 水平线
                    pygame.draw.rect(screen, WHITE,
                                   (GRID_OFFSET_X + (piece.x + x) * BLOCK_SIZE,
                                    GRID_OFFSET_Y + (ghost_y + y) * BLOCK_SIZE + i,
                                    1, 2))  # 垂直线

# 添加上升方块的函数
def add_rising_blocks():
    global grid, score, level, game_over
    warning_sound.play()  # 播放警告音效
    
    # 根据等级计算上升层数（1-5层）
    rise_levels = min(5, max(1, level // 2))
    
    # 检查是否会导致游戏结束
    for y in range(rise_levels):
        if any(grid[y]):
            game_over = True
            return
    
    # 将现有方块上移
    for y in range(rise_levels, GRID_HEIGHT):
        grid[y - rise_levels] = grid[y][:]
    
    # 在底部添加新的随机空缺方块
    for y in range(GRID_HEIGHT - rise_levels, GRID_HEIGHT):
        # 随机选择一个位置作为空缺
        gap = random.randint(0, GRID_WIDTH - 1)
        new_row = [RISING_BLOCK_COLOR] * GRID_WIDTH
        new_row[gap] = 0  # 在随机位置留下空缺
        grid[y] = new_row
    
    return rise_levels

# 添加倒计时显示函数
def draw_countdown():
    seconds = countdown_timer // 1000
    draw_text("Time:", 36, WHITE, WINDOW_WIDTH - 150, 150)
    # 当倒计时小于10秒时显示红色
    color = RED if seconds < 10 else WHITE
    draw_text(f"{seconds}s", 36, color, WINDOW_WIDTH - 150, 190)

while running:
    current_time = pygame.time.get_ticks()
    delta_time = current_time - last_time
    last_time = current_time
    
    if not game_over and not paused:
        fall_time += delta_time
        # 更新倒计时
        countdown_timer -= delta_time
        if countdown_timer <= 0:
            # 添加上升方块
            rise_levels = add_rising_blocks()
            if not game_over:
                # 给玩家额外的分数奖励
                score += rise_levels * 50
                # 重置倒计时（随着等级提高，时间缩短）
                countdown_time = max(10000, 30000 - (level - 1) * 2000)  # 最少10秒
                countdown_timer = countdown_time
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:  # 添加暂停功能
                paused = not paused
            elif not paused and not game_over:  # 只在非暂停状态处理其他按键
                if event.key in keys:
                    keys[event.key]["pressed"] = True
                    keys[event.key]["time"] = current_time
                    # 立即移动一次
                    if event.key == pygame.K_LEFT and current_piece.can_move(-1, 0):
                        current_piece.move(-1, 0)
                    elif event.key == pygame.K_RIGHT and current_piece.can_move(1, 0):
                        current_piece.move(1, 0)
                if event.key == pygame.K_UP:
                    current_piece.rotate()
                if event.key == pygame.K_r and game_over:
                    # 重置游戏状态
                    grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
                    current_piece = Tetromino()
                    next_piece = Tetromino()
                    score = 0
                    level = 1
                    lines_cleared_total = 0
                    fall_speed = 1000
                    game_over = False
                    paused = False
                    countdown_time = 30000
                    countdown_timer = countdown_time
        elif event.type == pygame.KEYUP and not game_over:
            if event.key in keys:
                keys[event.key]["pressed"] = False
                keys[event.key]["time"] = 0
    
    # 只在非暂停状态处理持续按键
    if not paused and not game_over:
        # 持续按住按键的处理
        for key in [pygame.K_LEFT, pygame.K_RIGHT]:
            if keys[key]["pressed"]:
                held_time = current_time - keys[key]["time"]
                if held_time > INITIAL_DELAY:
                    # 计算应该移动多少次
                    moves = (held_time - INITIAL_DELAY) // MOVE_REPEAT
                    if moves > keys[key].get("last_moves", -1):
                        dx = -1 if key == pygame.K_LEFT else 1
                        if current_piece.can_move(dx, 0):
                            current_piece.move(dx, 0)
                        keys[key]["last_moves"] = moves
            else:
                keys[key]["last_moves"] = -1
        
        # 下落键的处理
        if keys[pygame.K_DOWN]["pressed"]:
            current_fall_speed = fast_fall_speed
            move_sound.play()  # 播放加速音效
        else:
            current_fall_speed = normal_fall_speed
        
        if not game_over:
            # 方块自动下落
            if fall_time >= current_fall_speed:
                if current_piece.can_move(0, 1):
                    current_piece.move(0, 1)
                else:
                    lock_piece(current_piece)
                    drop_sound.play()  # 播放方块落地音效
                    clear_lines()
                    
                    # 检查游戏是否结束
                    if check_game_over():
                        game_over = True
                    
                    # 重置下落速度
                    current_fall_speed = normal_fall_speed
                fall_time = 0
    
    # 绘制部分
    screen.fill(BLACK)
    draw_grid()
    draw_locked_pieces()
    
    if not game_over:
        # 绘制预览方块（在当前方块之前绘制）
        draw_ghost_piece(current_piece)
        current_piece.draw()
    
    draw_next_piece()
    draw_countdown()  # 添加倒计时显示
    
    # 显示分数和等级
    draw_text(f"Score: {score}", 36, WHITE, 30, 30)
    draw_text(f"Level: {level}", 36, WHITE, 30, 70)
    draw_text("P: Pause", 36, WHITE, 30, 110)  # 添加暂停提示
    
    # 显示暂停状态
    if paused:
        draw_text("PAUSED", 48, PAUSED_TEXT_COLOR, WINDOW_WIDTH//2 - 80, WINDOW_HEIGHT//2 - 30)
        draw_text("Press P to Continue", 36, PAUSED_TEXT_COLOR, WINDOW_WIDTH//2 - 120, WINDOW_HEIGHT//2 + 20)
    
    # 显示游戏结束信息
    if game_over:
        draw_text("Game Over!", 48, RED, WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 30)
        draw_text("Press R to Restart", 36, WHITE, WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 20)
    
    pygame.display.flip()

# 退出游戏
pygame.quit()