import pygame
import random
import settings
import tank
import sys


def build_level(level_index):
    """Return walls list, start_pos, exit_rect for a level index.
    Use a recursive backtracker to produce a perfect maze (guaranteed path).
    """
    # compute grid size in cells (one grid cell == settings.CELL_SIZE pixels)
    cols = settings.WIDTH // settings.CELL_SIZE
    rows = settings.HEIGHT // settings.CELL_SIZE

    # make sure we have odd dimensions so passages sit on odd indices
    if cols % 2 == 0:
        cols -= 1
    if rows % 2 == 0:
        rows -= 1

    # Initialize everything as wall (1)
    grid = [[1 for _ in range(cols)] for __ in range(rows)]

    # Carve passages on odd coordinates
    for y in range(1, rows, 2):
        for x in range(1, cols, 2):
            grid[y][x] = 0

    # Recursive backtracker on the odd-cell coordinates
    start = (1, 1)
    stack = [start]
    visited = {start}

    directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]
    while stack:
        cx, cy = stack[-1]
        neighbors = []
        for dx, dy in directions:
            nx = cx + dx
            ny = cy + dy
            if 1 <= nx < cols - 1 and 1 <= ny < rows - 1 and (nx, ny) not in visited:
                neighbors.append((nx, ny))

        if neighbors:
            nx, ny = random.choice(neighbors)
            # remove wall between
            wall_x = (cx + nx) // 2
            wall_y = (cy + ny) // 2
            grid[wall_y][wall_x] = 0
            visited.add((nx, ny))
            stack.append((nx, ny))
        else:
            stack.pop()

    # Ensure exit is open
    exit_cell = (cols - 2, rows - 2)
    grid[exit_cell[1]][exit_cell[0]] = 0

    # Build wall rects
    walls = []
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] == 1:
                rect = pygame.Rect(x * settings.CELL_SIZE, y * settings.CELL_SIZE, settings.CELL_SIZE, settings.CELL_SIZE)
                walls.append(rect)

    exit_rect = pygame.Rect(exit_cell[0] * settings.CELL_SIZE, exit_cell[1] * settings.CELL_SIZE, settings.CELL_SIZE, settings.CELL_SIZE)
    start_pos = (start[0] * settings.CELL_SIZE + settings.CELL_SIZE // 2, start[1] * settings.CELL_SIZE + settings.CELL_SIZE // 2)
    return walls, start_pos, exit_rect


def spawn_enemies(count, walls, start_pos, exit_rect):
    enemies = []
    cols = settings.WIDTH // settings.CELL_SIZE
    rows = settings.HEIGHT // settings.CELL_SIZE
    attempts = 0
    while len(enemies) < count and attempts < 500:
        attempts += 1
        cx = random.randint(1, cols - 2)
        cy = random.randint(1, rows - 2)
        pos = (cx * settings.CELL_SIZE + settings.CELL_SIZE // 2, cy * settings.CELL_SIZE + settings.CELL_SIZE // 2)
        rect = pygame.Rect(pos[0] - settings.TANK_SIZE // 2, pos[1] - settings.TANK_SIZE // 2, settings.TANK_SIZE, settings.TANK_SIZE)
        # don't spawn inside walls or too close to start/exit
        if any(rect.colliderect(w) for w in walls):
            continue
        if rect.colliderect(pygame.Rect(start_pos[0] - 3 * settings.CELL_SIZE, start_pos[1] - 3 * settings.CELL_SIZE, 6 * settings.CELL_SIZE, 6 * settings.CELL_SIZE)):
            continue
        if rect.colliderect(exit_rect.inflate(3 * settings.CELL_SIZE, 3 * settings.CELL_SIZE)):
            continue
        enemies.append(tank.EnemyTank(pos[0], pos[1]))
    return enemies


def main():
    pygame.init()
    screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    clock = pygame.time.Clock()

    level = 0
    lives = settings.PLAYER_LIVES

    walls, start_pos, exit_rect = build_level(level)
    player = tank.Tank(start_pos[0], start_pos[1], (0, 200, 0))
    player_bullets = []
    enemy_bullets = []
    enemies = spawn_enemies(settings.ENEMY_BASE_COUNT + level, walls, start_pos, exit_rect)

    font = pygame.font.Font(None, 28)

    running = True
    game_over = False
    while running:
        clock.tick(settings.FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_SPACE:
                    player_bullets.append(player.fire())

        if not game_over:
            player.update(keys, walls)

            # enemies update
            for e in enemies[:]:
                b = e.update_ai(player, walls)
                if b:
                    enemy_bullets.append(b)

            # update bullets
            for b in player_bullets[:]:
                b.update()
                if b.off_screen():
                    player_bullets.remove(b)
                    continue
                # bullet hits wall
                if any(b.collides_with_rect(w) for w in walls):
                    player_bullets.remove(b)
                    continue
                # hit enemy
                hit = None
                for e in enemies:
                    if b.collides_with_rect(e.get_rect()):
                        hit = e
                        break
                if hit:
                    try:
                        enemies.remove(hit)
                    except ValueError:
                        pass
                    if b in player_bullets:
                        player_bullets.remove(b)

            for b in enemy_bullets[:]:
                b.update()
                if b.off_screen():
                    enemy_bullets.remove(b)
                    continue
                if any(b.collides_with_rect(w) for w in walls):
                    enemy_bullets.remove(b)
                    continue
                # hit player
                if b.collides_with_rect(player.get_rect()):
                    enemy_bullets.remove(b)
                    lives -= 1
                    # respawn player at start
                    player.x, player.y = start_pos
                    player.angle = 0
                    if lives <= 0:
                        game_over = True

            # check player reaching exit
            if player.get_rect().colliderect(exit_rect):
                level += 1
                walls, start_pos, exit_rect = build_level(level)
                player.x, player.y = start_pos
                player.angle = 0
                enemies = spawn_enemies(settings.ENEMY_BASE_COUNT + level, walls, start_pos, exit_rect)
                player_bullets = []
                enemy_bullets = []

        # draw
        screen.fill((20, 20, 20))

        # walls
        for w in walls:
            pygame.draw.rect(screen, settings.WALL_COLOR, w)

        # exit
        pygame.draw.rect(screen, settings.EXIT_COLOR, exit_rect)

        # draw entities
        player.draw(screen)
        for e in enemies:
            e.draw(screen)

        for b in player_bullets:
            b.draw(screen)
        for b in enemy_bullets:
            b.draw(screen)

        # HUD
        hud = font.render(f"Level: {level}  Lives: {lives}  Enemies: {len(enemies)}", True, (220, 220, 220))
        screen.blit(hud, (10, 10))

        if game_over:
            go = font.render("GAME OVER - Press ESC to quit", True, (255, 80, 80))
            screen.blit(go, (settings.WIDTH // 2 - 150, settings.HEIGHT // 2))

        pygame.display.flip()

        # allow escape to quit quickly
        if keys[pygame.K_ESCAPE]:
            running = False

    pygame.quit()


if __name__ == '__main__':
    main()
