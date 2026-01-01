import pygame
import numpy as np
import random

# Initialize pygame
pygame.init()

# Screen setup
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Hover Tank")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Constants
TANK_SIZE = int(SCREEN_HEIGHT * 0.015)  # 5% of screen height
PROJECTILE_RADIUS = int(SCREEN_HEIGHT * 0.003)
ENEMY_RADIUS = int(SCREEN_HEIGHT * 0.008)
CONTROL_AREA_HEIGHT = int(SCREEN_HEIGHT * 0.35)
MAX_TANK_SPEED = 4.2
FRICTION = 0.98  # Friction coefficient
PROJECTILE_SPEED = 7
ENEMY_THRUST = 0.08
ENEMY_FRICTION = 0.95
SPAWN_RATE = 60  # Frames between enemy spawns
FPS = 60

# Clock
clock = pygame.time.Clock()

# Fonts
font = pygame.font.Font(None, int(SCREEN_HEIGHT * 0.05))

# Classes
class Tank:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vx = 0
        self.vy = 0

    def update(self, force_x, force_y):
        self.vx += force_x*0.5
        self.vy += force_y*0.5
        self.vx *= FRICTION
        self.vy *= FRICTION
        speed = np.sqrt(self.vx**2 + self.vy**2)
        if speed > MAX_TANK_SPEED:
            self.vx = self.vx / speed * MAX_TANK_SPEED
            self.vy = self.vy / speed * MAX_TANK_SPEED
        self.x += self.vx
        self.y += self.vy
        self.x = np.clip(self.x, 0, SCREEN_WIDTH)
        self.y = np.clip(self.y, 0, SCREEN_HEIGHT)

    def draw(self):
        pygame.draw.rect(screen, WHITE, (self.x - TANK_SIZE // 2, self.y - TANK_SIZE // 2, TANK_SIZE, TANK_SIZE))


class Projectile:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), PROJECTILE_RADIUS)


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0

    def update(self, tank_x, tank_y, tank_vx, tank_vy, score):
        dx = tank_x - self.x
        dy = tank_y - self.y
        dist = np.sqrt(dx**2 + dy**2)
        if dist > 0:
            dx /= dist
            dy /= dist
        # Predictive aiming
        target_x = tank_x + tank_vx * 30
        target_y = tank_y + tank_vy * 30
        dx_target = target_x - self.x
        dy_target = target_y - self.y
        dist_target = np.sqrt(dx_target**2 + dy_target**2)
        if dist_target > 0:
            dx_target /= dist_target
            dy_target /= dist_target
        self.vx += dx_target * ENEMY_THRUST * (1 + score / 100)
        self.vy += dy_target * ENEMY_THRUST * (1 + score / 100)
        self.vx *= ENEMY_FRICTION
        self.vy *= ENEMY_FRICTION
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), ENEMY_RADIUS)

# Game loop
def main():
    running = True
    tank = Tank()
    projectiles = []
    enemies = []
    score = 0
    frame_counter = 0

    # Dictionary to track touch points
    touch_points = {}

    while running:
        screen.fill(BLACK)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

            # Handle multi-touch events
            if event.type == pygame.FINGERDOWN:
                touch_id = event.finger_id
                x = event.x * SCREEN_WIDTH
                y = event.y * SCREEN_HEIGHT
                touch_points[touch_id] = (x, y)

            if event.type == pygame.FINGERUP:
                touch_id = event.finger_id
                if touch_id in touch_points:
                    del touch_points[touch_id]

            if event.type == pygame.FINGERMOTION:
                touch_id = event.finger_id
                x = event.x * SCREEN_WIDTH
                y = event.y * SCREEN_HEIGHT
                if touch_id in touch_points:
                    touch_points[touch_id] = (x, y)

        # Process touch points
        force_x, force_y = 0, 0
        aim_dx, aim_dy = 0, 0
        for touch_id, (x, y) in touch_points.items():
            if x > SCREEN_WIDTH // 2:  # Movement control (right side)
                cx, cy = SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.82
                dx, dy = x - cx, y - cy
                dist = np.sqrt(dx**2 + dy**2)
                if dist > CONTROL_AREA_HEIGHT // 2:
                    dx = dx / dist * CONTROL_AREA_HEIGHT // 2
                    dy = dy / dist * CONTROL_AREA_HEIGHT // 2
                force_x, force_y = dx / 100, dy / 100
            else:  # Weapon control (left side)
                cx, cy = SCREEN_WIDTH * 0.25, SCREEN_HEIGHT * 0.82
                dx, dy = x - cx, y - cy
                dist = np.sqrt(dx**2 + dy**2)
                if dist > CONTROL_AREA_HEIGHT // 2:
                    dx = dx / dist * CONTROL_AREA_HEIGHT // 2
                    dy = dy / dist * CONTROL_AREA_HEIGHT // 2
                aim_dx, aim_dy = dx, dy

        # Update tank
        tank.update(force_x, force_y)

        # Fire projectiles
        if aim_dx != 0 or aim_dy != 0:
            if frame_counter % (FPS // 5) == 0:  # Fire rate: 2 shots per second
                proj_vx = aim_dx / np.sqrt(aim_dx**2 + aim_dy**2) * PROJECTILE_SPEED + tank.vx
                proj_vy = aim_dy / np.sqrt(aim_dx**2 + aim_dy**2) * PROJECTILE_SPEED + tank.vy
                projectiles.append(Projectile(tank.x, tank.y, proj_vx, proj_vy))

        # Update projectiles
        for projectile in projectiles[:]:
            projectile.update()
            if not (0 <= projectile.x <= SCREEN_WIDTH and 0 <= projectile.y <= SCREEN_HEIGHT):
                projectiles.remove(projectile)

        # Update enemies
        for enemy in enemies[:]:
            enemy.update(tank.x, tank.y, tank.vx, tank.vy, score)
            if np.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2) < TANK_SIZE // 2 + ENEMY_RADIUS:
                running = False  # Game over

        # Collision detection
        for i in range(len(enemies) - 1, -1, -1):  # Iterate backwards over enemies
            for j in range(len(projectiles) - 1, -1, -1):  # Iterate backwards over projectiles
                enemy = enemies[i]
                projectile = projectiles[j]

                if np.sqrt((projectile.x - enemy.x)**2 + (projectile.y - enemy.y)**2) < PROJECTILE_RADIUS + ENEMY_RADIUS:
            # Remove the projectile and enemy
                    del projectiles[j]  # Remove by index to avoid shifting
                    del enemies[i]      # Remove by index to avoid shifting
                    score += 1
                    break  # Stop checking other projectiles for this enemy

        # Spawn enemies
        frame_counter += 1
        if frame_counter % SPAWN_RATE == 0:
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                x, y = random.randint(0, SCREEN_WIDTH), 0
            elif side == "bottom":
                x, y = random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT
            elif side == "left":
                x, y = 0, random.randint(0, SCREEN_HEIGHT)
            else:
                x, y = SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT)
            enemies.append(Enemy(x, y))

        # Draw everything
        tank.draw()
        for projectile in projectiles:
            projectile.draw()
        for enemy in enemies:
            enemy.draw()

        # Draw score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Draw the horizontal line
        #pygame.draw.line(screen, WHITE, (0, SCREEN_HEIGHT*0.65), (SCREEN_WIDTH, SCREEN_HEIGHT*0.65), 5)
        #Draw the vertical line
        #pygame.draw.line(screen, WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT*0.65), (SCREEN_WIDTH//2, SCREEN_HEIGHT), 5)
        
        # Draw rigjt circle
        pygame.draw.circle(screen, WHITE, (SCREEN_WIDTH*0.75, SCREEN_HEIGHT*0.75), (SCREEN_WIDTH*0.25), 2)
        #Draw left circle
        pygame.draw.circle(screen, WHITE, (SCREEN_WIDTH*0.25, SCREEN_HEIGHT*0.75), (SCREEN_WIDTH*0.25), 2)
        
        #Draw move center triangles
        pygame.draw.polygon(screen, BLUE, [(SCREEN_WIDTH*0.75-20, SCREEN_HEIGHT*0.75), (SCREEN_WIDTH*0.75+20, SCREEN_HEIGHT*0.75), (SCREEN_WIDTH*0.75, SCREEN_HEIGHT*0.75-43)])
        #Draw weapon center triangles
        pygame.draw.polygon(screen, RED, [(SCREEN_WIDTH*0.25-20, SCREEN_HEIGHT*0.75), (SCREEN_WIDTH*0.25+20, SCREEN_HEIGHT*0.75), (SCREEN_WIDTH*0.25, SCREEN_HEIGHT*0.75-43)])
        # Flip display
        pygame.display.flip()
        clock.tick(FPS)

    # Game over screen
    screen.fill(BLACK)
    # Draw score
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    game_over_text = font.render("GAME OVER", True, WHITE)
    restart_text = font.render("Touch to restart", True, WHITE)
    screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
    pygame.display.flip()

    # Wait for touch to restart
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.FINGERDOWN:
                waiting = False

    # Restart game
    main()


if __name__ == "__main__":
    main()