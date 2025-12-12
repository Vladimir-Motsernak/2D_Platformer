import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = join(script_dir, "assets", dir1, dir2)

    if not os.path.isdir(path):
        all_sprites = {}
        base = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        base.fill((255, 0, 255, 255))
        placeholder = pygame.transform.scale2x(base)

        if direction:
            names = ["idle", "hit", "jump", "double_jump", "fall", "run"]
            for name in names:
                all_sprites[name + "_right"] = [placeholder]
                all_sprites[name + "_left"] = [pygame.transform.flip(placeholder, True, False)]
        else:
            all_sprites["off"] = [placeholder]
            all_sprites["on"] = [placeholder]
            all_sprites["idle"] = [placeholder]

        return all_sprites

    images = [f for f in listdir(path) if isfile(join(path, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            original_name = image.replace(".png", "").replace(".jpg", "")

            sprite_mapping = {
                "Idle": "idle",
                "Hurt": "hit",
                "Jump": "jump",
                "Death": "death",
                "Run": "run",
                "Walk": "run"
            }

            name = sprite_mapping.get(original_name, original_name.lower())
            all_sprites[name + "_right"] = sprites
            all_sprites[name + "_left"] = flip(sprites)

            if name == "jump":
                all_sprites["double_jump_right"] = sprites
                all_sprites["double_jump_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "").replace(".jpg", "")] = sprites

    return all_sprites


def get_block(size):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = join(script_dir, "assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height, character="snowl"):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.health = 5
        self.max_health = 5
        self.immunity_frames = 0
        self.immunity_duration = 120  # 2 seconds at 60 FPS (immunity after taking damage)
        # Load character sprite sheet (placeholder slots allowed)
        self.SPRITES = load_sprite_sheets("MainCharacters", character if character else "missing", 32, 32, True)

    def jump(self):
        # Only allow jump if vertical velocity is reasonable
        if self.y_vel < 9.81:
            self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        # Only take damage if not in immunity frames and health is above zero
        if self.immunity_frames <= 0 and self.health > 0:
            self.hit = True
            self.health -= 1
            self.immunity_frames = self.immunity_duration

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        # Apply gravity to player's vertical velocity
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        # Handle hit animation timing
        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        # Decrease immunity frames each tick
        if self.immunity_frames > 0:
            self.immunity_frames -= 1

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        # Reset jumping state when player lands on ground
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def jump(self):
        # Allow up to a double jump; stronger impulses to better counter downward velocity
        if self.jump_count >= 2:
            return

        # First jump is strong, double jump is stronger to overcome downward momentum
        if self.jump_count == 0:
            self.y_vel = -self.GRAVITY * 5
        else:
            self.y_vel = -self.GRAVITY * 6

        self.animation_count = 0
        self.jump_count += 1

        # Reset fall accumulation so gravity doesn't immediately overpower the jump
        self.fall_count = 0

    def hit_head(self):
        # Bounce player down when hitting ceiling
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        # Determine which animation to show based on player state
        if self.health <= 0:
            sprite_sheet = "death"  # Death animation when health reaches zero
        elif self.hit:
            sprite_sheet = "hit"  # Hit animation when taking damage
        elif self.y_vel < 0:
            # Jumping animations based on jump count
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
            else:
                sprite_sheet = "jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"  # Falling animation
        elif self.x_vel != 0:
            sprite_sheet = "run"  # Running animation when moving
        else:
            sprite_sheet = "idle"  # Idle animation when stationary

        sprite_sheet_name = sprite_sheet + "_" + self.direction

        # Safeguard in case direction sheet missing
        if sprite_sheet_name not in self.SPRITES:
            sprite_sheet_name = "idle_" + self.direction

        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        # Update collision rectangle and mask for pixel-perfect collision
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        # Flicker effect during immunity frames for visual feedback
        if self.immunity_frames <= 0 or (self.immunity_frames // 5) % 2 == 0:
            win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        # Animate fire trap
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class LevelEnd(Object):
    """Flag/door that completes the level when reached"""
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "level_end")
        # Create a simple flag visual indicator
        self.image.fill((0, 0, 0, 0))
        # Flag pole (brown)
        pygame.draw.rect(self.image, (139, 69, 19), (width//2 - 5, 0, 10, height))
        # Flag (golden)
        pygame.draw.polygon(self.image, (255, 215, 0), [
            (width//2 + 5, 10),
            (width - 10, 30),
            (width//2 + 5, 50)
        ])
        self.mask = pygame.mask.from_surface(self.image)


def get_background(name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image = pygame.image.load(join(script_dir, "assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    # Create tiled background
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw_hearts(window, player):
    """Draw heart UI for player health display"""
    heart_size = 30
    padding = 10

    for i in range(player.max_health):
        x = padding + i * (heart_size + 5)
        y = padding

        # Draw heart shape - red if filled, gray if empty
        if i < player.health:
            color = (255, 0, 0)  # Red for filled hearts
        else:
            color = (100, 100, 100)  # Gray for empty hearts

        # Simple heart shape using circles and triangle
        pygame.draw.circle(window, color, (x + heart_size//4, y + heart_size//3), heart_size//4)
        pygame.draw.circle(window, color, (x + 3*heart_size//4, y + heart_size//3), heart_size//4)
        pygame.draw.polygon(window, color, [
            (x, y + heart_size//3),
            (x + heart_size//2, y + heart_size),
            (x + heart_size, y + heart_size//3)
        ])


def draw_level_indicator(window, current_level):
    """Draw current level number on screen"""
    font = pygame.font.Font(None, 36)
    text = font.render(f"Level {current_level}", True, (255, 255, 255))
    text_rect = text.get_rect(topright=(WIDTH - 20, 20))

    # Draw black outline for better visibility
    outline_color = (0, 0, 0)
    for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
        outline_text = font.render(f"Level {current_level}", True, outline_color)
        window.blit(outline_text, (text_rect.x + dx, text_rect.y + dy))

    window.blit(text, text_rect)


def draw(window, background, bg_image, player, objects, offset_x, current_level):
    # Draw tiled background
    for tile in background:
        window.blit(bg_image, tile)

    # Draw all game objects
    for obj in objects:
        obj.draw(window, offset_x)

    # Draw player
    player.draw(window, offset_x)

    # Draw UI elements
    draw_hearts(window, player)
    draw_level_indicator(window, current_level)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    """Handle collisions when player moves vertically"""
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                # Landing on top of object
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                # Hitting head on bottom of object
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    """Check for horizontal collision without actually moving player"""
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    # Undo the test movement
    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    """Handle player movement and collision detection"""
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    # Move player based on input if no collision
    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)

    # Check for level completion by touching the flag
    for obj in vertical_collide + [collide_left, collide_right]:
        if obj and obj.name == "level_end":
            return True  # Level completed

    # Check for fire damage - only when falling/on ground or moving horizontally
    if player.y_vel >= 0:  # Only when falling or on ground (prevents damage when jumping up through fire)
        to_check = [collide_left, collide_right, *vertical_collide]
        for obj in to_check:
            if obj and obj.name == "fire":
                player.make_hit()
    else:  # When jumping up, only check horizontal collisions
        to_check = [collide_left, collide_right]
        for obj in to_check:
            if obj and obj.name == "fire":
                player.make_hit()

    return False  # Level not completed


def place_flag_on_platform(objects, desired_x, flag_w, flag_h, default_y):
    """Try to place a flag at desired_x so its bottom sits on the top of a platform if present."""
    for obj in objects:
        if isinstance(obj, Block) and obj.rect.x == desired_x:
            flag_y = obj.rect.y - flag_h
            return LevelEnd(desired_x, flag_y, flag_w, flag_h)
    # fallback
    return LevelEnd(desired_x, default_y, flag_w, flag_h)


def create_level_1():
    """Create level 1 layout - Tutorial/Easy level with basic platforming"""
    block_size = 96

    # Create floor across entire level
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 4) // block_size)]

    objects = [*floor]

    # Starting safe platform
    objects.append(Block(0, HEIGHT - block_size * 2, block_size))
    objects.append(Block(block_size, HEIGHT - block_size * 2, block_size))

    # First obstacle - single fire pit (easy to jump over)
    fire1 = Fire(block_size * 4, HEIGHT - block_size - 64, 16, 32)
    fire1.on()
    objects.append(fire1)

    # Platforms around fire
    objects.append(Block(block_size * 3, HEIGHT - block_size * 3, block_size))
    objects.append(Block(block_size * 5, HEIGHT - block_size * 3, block_size))

    # Gentle staircase section (introduces vertical movement)
    for i in range(5):
        objects.append(Block(block_size * (7 + i), HEIGHT - block_size * (2 + i), block_size))

    # Fire hazard on elevated platform
    fire2 = Fire(block_size * 9, HEIGHT - block_size * 5 - 64, 16, 32)
    fire2.on()
    objects.append(fire2)

    # Simple gap jumping section
    objects.append(Block(block_size * 13, HEIGHT - block_size * 6, block_size))
    objects.append(Block(block_size * 15, HEIGHT - block_size * 5, block_size))
    objects.append(Block(block_size * 17, HEIGHT - block_size * 4, block_size))

    # Final platform before flag
    for i in range(4):
        objects.append(Block(block_size * (19 + i), HEIGHT - block_size * 3, block_size))

    # Level end flag - place on top of final platform if found
    flag_x = block_size * 22
    default_y = HEIGHT - block_size * 4 - 80
    level_end = place_flag_on_platform(objects, flag_x, 50, 80, default_y)
    objects.append(level_end)

    return objects


def create_level_2():
    """Create level 2 layout - Medium difficulty with longer jumps and more hazards"""
    block_size = 96

    # Extended floor
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 5) // block_size)]

    objects = [*floor]

    # Starting area
    objects.append(Block(0, HEIGHT - block_size * 2, block_size))

    # Multiple fire obstacles in a row (requires careful timing) - fewer and more spaced
    for i in range(2):
        fire = Fire(block_size * (3 + i * 3), HEIGHT - block_size - 64, 16, 32)
        fire.on()
        objects.append(fire)

    # High platforms requiring double jump mastery (slightly lower)
    objects.append(Block(block_size * 9, HEIGHT - block_size * 5, block_size))
    objects.append(Block(block_size * 11, HEIGHT - block_size * 6, block_size))
    objects.append(Block(block_size * 13, HEIGHT - block_size * 5, block_size))

    # Descending section with fire hazards
    for i in range(4):
        objects.append(Block(block_size * (15 + i), HEIGHT - block_size * (6 - i), block_size))
        if i % 2 == 1:
            fire = Fire(block_size * (15 + i), HEIGHT - block_size * (7 - i) - 64, 16, 32)
            fire.on()
            objects.append(fire)

    # Final challenge - narrow platforms with gaps (less punishing)
    for i in range(5):
        objects.append(Block(block_size * (20 + i * 2), HEIGHT - block_size * 4, block_size))

    # Level end flag
    flag_x = block_size * 29
    default_y = HEIGHT - block_size * 5 - 80
    level_end = place_flag_on_platform(objects, flag_x, 50, 80, default_y)
    objects.append(level_end)

    return objects


def create_level_3():
    """Create level 3 layout - Reduced difficulty to be beatable"""
    block_size = 96

    # Floor with smaller gaps (made easier)
    floor = []
    for i in range(-WIDTH // block_size, (WIDTH * 6) // block_size):
        # Smaller gaps than before
        if not (9 <= i <= 9 or 19 <= i <= 20 or 30 <= i <= 31):
            floor.append(Block(i * block_size, HEIGHT - block_size, block_size))

    objects = [*floor]

    # Starting platform
    for i in range(3):
        objects.append(Block(i * block_size, HEIGHT - block_size * 2, block_size))

    # First challenge - reachable floating platforms lowered
    objects.append(Block(block_size * 5, HEIGHT - block_size * 3, block_size))
    objects.append(Block(block_size * 7, HEIGHT - block_size * 4, block_size))

    # Easier gaps and platforms
    objects.append(Block(block_size * 9, HEIGHT - block_size * 3, block_size))
    objects.append(Block(block_size * 11, HEIGHT - block_size * 2, block_size))

    # Fire gauntlet on narrow platforms - reduced count
    for i in range(2):
        objects.append(Block(block_size * (13 + i * 2), HEIGHT - block_size * 5, block_size))
        fire = Fire(block_size * (14 + i * 2), HEIGHT - block_size * 5 - 64, 16, 32)
        fire.on()
        objects.append(fire)

    # Second easier pit
    objects.append(Block(block_size * 22, HEIGHT - block_size * 4, block_size))
    objects.append(Block(block_size * 25, HEIGHT - block_size * 5, block_size))

    # Final platforms to flag (more forgiving)
    for i in range(3):
        objects.append(Block(block_size * (36 + i), HEIGHT - block_size * 3, block_size))

    # Level end flag
    flag_x = block_size * 38
    default_y = HEIGHT - block_size * 4 - 80
    level_end = place_flag_on_platform(objects, flag_x, 50, 80, default_y)
    objects.append(level_end)

    return objects


def create_level_4():
    """Create level 4 layout - toned down difficulty"""
    block_size = 96

    # Fewer and smaller gaps
    floor = []
    for i in range(-WIDTH // block_size, (WIDTH * 7) // block_size):
        if not (6 <= i <= 9 or 22 <= i <= 25 or 36 <= i <= 38):
            floor.append(Block(i * block_size, HEIGHT - block_size, block_size))

    objects = [*floor]

    # Starting area
    for i in range(4):
        objects.append(Block(i * block_size, HEIGHT - block_size * 2, block_size))

    # Simplified spiral
    spiral_positions = [
        (6, 3), (8, 4), (10, 5), (11, 5)
    ]
    for x, y in spiral_positions:
        objects.append(Block(block_size * x, HEIGHT - block_size * y, block_size))
        # Fewer fire hazards
        if (x + y) % 4 == 0:
            fire = Fire(block_size * x, HEIGHT - block_size * y - 64, 16, 32)
            fire.on()
            objects.append(fire)

    # Bridge section with fewer fires
    for i in range(6):
        objects.append(Block(block_size * (14 + i), HEIGHT - block_size * 6, block_size))
        if i % 3 == 1:
            fire = Fire(block_size * (14 + i), HEIGHT - block_size * 6 - 64, 16, 32)
            fire.on()
            objects.append(fire)

    # Descending challenge
    descend_positions = [(22, 5), (24, 4), (26, 3), (28, 3)]
    for x, y in descend_positions:
        objects.append(Block(block_size * x, HEIGHT - block_size * y, block_size))

    # Final platforms
    for i in range(3):
        objects.append(Block(block_size * (44 + i), HEIGHT - block_size * 3, block_size))

    # Level end flag
    flag_x = block_size * 46
    default_y = HEIGHT - block_size * 4 - 80
    level_end = place_flag_on_platform(objects, flag_x, 50, 80, default_y)
    objects.append(level_end)

    return objects


def create_level_5():
    """Create level 5 layout - expert but less brutal than before"""
    block_size = 96

    # Less sparse floor
    floor = []
    for i in range(-WIDTH // block_size, (WIDTH * 8) // block_size):
        if i < 4 or (14 <= i <= 18) or (45 <= i <= 50) or i >= 62:
            floor.append(Block(i * block_size, HEIGHT - block_size, block_size))

    objects = [*floor]

    # Starting safe zone
    for i in range(3):
        objects.append(Block(i * block_size, HEIGHT - block_size * 2, block_size))

    # Tower climb simplified
    tower_climb = [(4, 3), (6, 4), (5, 5), (7, 5)]
    for x, y in tower_climb:
        objects.append(Block(block_size * x, HEIGHT - block_size * y, block_size))
        if y % 2 == 0:
            fire = Fire(block_size * x, HEIGHT - block_size * y - 64, 16, 32)
            fire.on()
            objects.append(fire)

    # Horizontal fire gauntlet - shorter
    for i in range(5):
        objects.append(Block(block_size * (10 + i), HEIGHT - block_size * 7, block_size))
        if i % 2 == 0 and i > 0:
            fire = Fire(block_size * (10 + i), HEIGHT - block_size * 7 - 64, 16, 32)
            fire.on()
            objects.append(fire)

    # Descent and final sections simplified
    descent = [(19, 6), (21, 5), (22, 4), (24, 3)]
    for x, y in descent:
        objects.append(Block(block_size * x, HEIGHT - block_size * y, block_size))

    ultra_hard_jumps = [(33, 5), (37, 6), (41, 5)]
    for x, y in ultra_hard_jumps:
        objects.append(Block(block_size * x, HEIGHT - block_size * y, block_size))
        fire = Fire(block_size * x, HEIGHT - block_size * y - 64, 16, 32)
        fire.on()
        objects.append(fire)

    # Victory platform
    for i in range(5):
        objects.append(Block(block_size * (65 + i), HEIGHT - block_size * 2, block_size))

    # Level end flag
    flag_x = block_size * 68
    default_y = HEIGHT - block_size * 3 - 80
    level_end = place_flag_on_platform(objects, flag_x, 50, 80, default_y)
    objects.append(level_end)

    return objects


def show_game_over(window):
    """Display game over screen with fade-in effect"""
    # Create semi-transparent overlay for smooth transition
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))

    # Fade in effect
    for alpha in range(0, 200, 10):
        overlay.set_alpha(alpha)
        window.blit(overlay, (0, 0))
        pygame.display.update()
        pygame.time.delay(30)

    # Display game over text
    font = pygame.font.Font(None, 74)
    text = font.render("GAME OVER", True, (255, 0, 0))
    text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))

    restart_font = pygame.font.Font(None, 36)
    restart_text = restart_font.render("Press R to Restart", True, (255, 255, 255))
    restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))

    quit_text = restart_font.render("Press Q to Quit", True, (255, 255, 255))
    quit_rect = quit_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))

    # Fill with dark background
    window.fill((20, 20, 20))
    window.blit(text, text_rect)
    window.blit(restart_text, restart_rect)
    window.blit(quit_text, quit_rect)
    pygame.display.update()

    # Wait for player input
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # Restart game
                if event.key == pygame.K_q:
                    return False  # Quit game
    return False


def show_level_complete(window, level):
    """Display level completion screen with celebration effect"""
    # Create overlay for transition
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 50, 0))  # Dark green tint for success

    # Fade in effect
    for alpha in range(0, 180, 15):
        overlay.set_alpha(alpha)
        window.blit(overlay, (0, 0))
        pygame.display.update()
        pygame.time.delay(20)

    # Display completion message
    font = pygame.font.Font(None, 74)
    text = font.render(f"LEVEL {level} COMPLETE!", True, (0, 255, 0))
    text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))

    continue_font = pygame.font.Font(None, 36)
    continue_text = continue_font.render("Press ENTER to Continue", True, (255, 255, 255))
    continue_rect = continue_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))

    # Fill with dark background
    window.fill((10, 30, 10))
    window.blit(text, text_rect)
    window.blit(continue_text, continue_rect)
    pygame.display.update()

    # Wait for player input
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True  # Continue to next level
    return False


def show_victory_screen(window):
    """Display final victory screen after beating all levels"""
    # Create golden overlay for victory
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((50, 40, 0))

    # Fade in effect
    for alpha in range(0, 200, 10):
        overlay.set_alpha(alpha)
        window.blit(overlay, (0, 0))
        pygame.display.update()
        pygame.time.delay(25)

    # Display victory message
    font = pygame.font.Font(None, 90)
    text = font.render("YOU WIN!", True, (255, 215, 0))
    text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))

    subtitle_font = pygame.font.Font(None, 48)
    subtitle = subtitle_font.render("All Levels Complete!", True, (255, 255, 255))
    subtitle_rect = subtitle.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))

    restart_font = pygame.font.Font(None, 36)
    restart_text = restart_font.render("Press R to Play Again", True, (200, 200, 200))
    restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))

    # Fill with dark background
    window.fill((0, 0, 0))
    window.blit(text, text_rect)
    window.blit(subtitle, subtitle_rect)
    window.blit(restart_text, restart_rect)
    pygame.display.update()

    # Wait for player input
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # Restart from level 1
    return False


def show_level_transition(window, level):
    """Display transition screen between levels"""
    # Create overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 50))  # Dark blue

    # Fade in
    for alpha in range(0, 255, 25):
        overlay.set_alpha(alpha)
        window.blit(overlay, (0, 0))
        pygame.display.update()
        pygame.time.delay(15)

    # Display level number
    font = pygame.font.Font(None, 100)
    text = font.render(f"LEVEL {level}", True, (255, 255, 255))
    text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))

    window.fill((0, 0, 30))
    window.blit(text, text_rect)
    pygame.display.update()
    pygame.time.delay(1500)  # Show for 1.5 seconds

    # Fade out
    for alpha in range(255, 0, -25):
        overlay.set_alpha(alpha)
        window.fill((0, 0, 30))
        window.blit(text, text_rect)
        window.blit(overlay, (0, 0))
        pygame.display.update()
        pygame.time.delay(15)


def select_character(window):
    # Character list as tuples (display_name, asset_dir_name)
    character_options = [
        ("Snowl", "snowl"),
        ("Ninja Frog", "NinjaFrog"),
        ("Mask Dude", "MaskDude"),
        ("Pink Man", "PinkMan")
    ]
    idx = 0
    font = pygame.font.Font(None, 36)
    selecting = True
    clock = pygame.time.Clock()

    while selecting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    idx = (idx - 1) % len(character_options)
                if event.key == pygame.K_RIGHT:
                    idx = (idx + 1) % len(character_options)
                if event.key == pygame.K_RETURN:
                    # Return the asset directory name for the selected character
                    return character_options[idx][1]
                if event.key == pygame.K_ESCAPE:
                    return character_options[idx][1]

        # Draw selection screen
        window.fill((30, 30, 40))
        title = font.render("Select Character", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH//2, 60))
        window.blit(title, title_rect)

        # Draw slots
        slot_w = 120
        slot_h = 160
        gap = 40
        total_w = len(character_options) * slot_w + (len(character_options) - 1) * gap
        start_x = (WIDTH - total_w) // 2
        y = 140

        for i, (display_name, asset_dir) in enumerate(character_options):
            x = start_x + i * (slot_w + gap)
            rect = pygame.Rect(x, y, slot_w, slot_h)
            pygame.draw.rect(window, (80, 80, 80), rect)

            # Try to draw character idle sprite if available from the corresponding asset folder
            sprites = load_sprite_sheets("MainCharacters", asset_dir, 32, 32, True)
            sprite = sprites.get("idle_right", [None])[0]
            if sprite:
                sprite_small = pygame.transform.scale(sprite, (slot_w - 20, slot_h - 60))
                window.blit(sprite_small, (x + 10, y + 10))
            else:
                # Draw placeholder box
                pygame.draw.rect(window, (150, 150, 150), (x + 10, y + 10, slot_w - 20, slot_h - 60))

            label = font.render(display_name, True, (255, 255, 255))
            lbl_rect = label.get_rect(center=(x + slot_w//2, y + slot_h - 20))
            window.blit(label, lbl_rect)

            if i == idx:
                pygame.draw.rect(window, (255, 255, 0), rect, 4)
            else:
                pygame.draw.rect(window, (0, 0, 0), rect, 2)

        instr = font.render("Use ← → to choose, ENTER to confirm", True, (200, 200, 200))
        window.blit(instr, (WIDTH//2 - instr.get_width()//2, HEIGHT - 80))

        pygame.display.update()


def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    current_level = 1

    # Character selection before starting levels
    selected_char = select_character(window)

    # Main game loop - cycles through all levels
    while True:
        # Show level transition screen
        show_level_transition(window, current_level)

        # Create level based on current level number
        if current_level == 1:
            objects = create_level_1()
        elif current_level == 2:
            objects = create_level_2()
        elif current_level == 3:
            objects = create_level_3()
        elif current_level == 4:
            objects = create_level_4()
        elif current_level == 5:
            objects = create_level_5()
        else:
            # All 5 levels completed - show victory screen
            if show_victory_screen(window):
                current_level = 1  # Restart from beginning
                continue
            else:
                break  # Exit game

        # Initialize player at starting position (pass selected character)
        player = Player(100, 100, 50, 50, character=selected_char)
        offset_x = 0  # Camera offset for scrolling
        scroll_area_width = 200  # Scroll when player gets this close to edge

        run = True
        level_completed = False

        # Level game loop
        while run:
            clock.tick(FPS)  # Maintain consistent frame rate

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.KEYDOWN:
                    # Jump on spacebar (allow double jump)
                    if event.key == pygame.K_SPACE and player.jump_count < 2:
                        player.jump()

            # Update player physics
            player.loop(FPS)

            # Update all animated objects (fire traps)
            for obj in objects:
                if isinstance(obj, Fire):
                    obj.loop()

            # Handle player movement and check for level completion
            level_completed = handle_move(player, objects)

            # Check if player fell off the map (instant death)
            if player.rect.y > HEIGHT:
                player.health = 0

            # Check for game over condition
            if player.health <= 0:
                draw(window, background, bg_image, player, objects, offset_x, current_level)
                pygame.time.wait(1000)  # Brief pause to show death
                if show_game_over(window):
                    current_level = 1  # Restart from level 1 on death
                    break
                else:
                    pygame.quit()
                    quit()

            # Check for level completion
            if level_completed:
                draw(window, background, bg_image, player, objects, offset_x, current_level)
                pygame.time.wait(800)  # Brief celebration pause
                if show_level_complete(window, current_level):
                    current_level += 1  # Advance to next level
                    break
                else:
                    pygame.quit()
                    quit()

            # Draw everything
            draw(window, background, bg_image, player, objects, offset_x, current_level)

            # Camera scrolling - follow player horizontally
            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel

    # Clean exit
    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)