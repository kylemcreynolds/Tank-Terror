import pygame
import random
import math
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
    # Make early levels easier by removing some random walls (creating loops/openings)
    # level_index is 1-based for players, use lvl0 (0-based) for scaling

    # Treat incoming level_index as 1-based for player; convert to 0-based for internal scaling/themes
    lvl0 = max(level_index - 1, 0)

    # Make early levels easier by removing some random walls (creating loops/openings)
    # lvl0 is 0-based for scaling
    max_removals = max((cols * rows) // 50 - lvl0 * 2, 0)
    removed = 0
    attempts = 0
    while removed < max_removals and attempts < max_removals * 10 + 100:
        attempts += 1
        rx = random.randint(1, cols - 2)
        ry = random.randint(1, rows - 2)
        if grid[ry][rx] == 1:
            # don't remove border walls
            if (rx, ry) in (start, exit_cell):
                continue
            grid[ry][rx] = 0
            # add rect to walls removal by rebuilding walls list later
            removed += 1

    # Rebuild wall rects based on potentially modified grid
    walls = []
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] == 1:
                rect = pygame.Rect(x * settings.CELL_SIZE, y * settings.CELL_SIZE, settings.CELL_SIZE, settings.CELL_SIZE)
                walls.append(rect)

    # Get theme for this level (use first theme for level 1, etc.; clamp if out of range)
    theme_idx = min(lvl0, len(settings.LEVEL_THEMES) - 1)
    theme = settings.LEVEL_THEMES[theme_idx]

    return walls, start_pos, exit_rect, grid, theme


def cell_from_pos(grid, px, py):
    """Convert pixel position to grid cell (clamped)."""
    cx = int(px // settings.CELL_SIZE)
    cy = int(py // settings.CELL_SIZE)
    return max(0, min(cx, len(grid[0]) - 1)), max(0, min(cy, len(grid) - 1))


def astar(grid, start_cell, goal_cell):
    """Simple A* on the maze grid. Returns list of pixel centers or None."""
    sx, sy = start_cell
    gx, gy = goal_cell
    if grid[sy][sx] == 1 or grid[gy][gx] == 1:
        return None
    import heapq
    openh = [(abs(gx - sx) + abs(gy - sy), start_cell)]
    came_from = {}
    gscore = {start_cell: 0}
    while openh:
        _, current = heapq.heappop(openh)
        if current == goal_cell:
            # rebuild path
            path = []
            node = current
            while node in came_from:
                path.append(node)
                node = came_from[node]
            path.append(start_cell)
            path.reverse()
            return [(c[0] * settings.CELL_SIZE + settings.CELL_SIZE // 2, c[1] * settings.CELL_SIZE + settings.CELL_SIZE // 2) for c in path]
        cx, cy = current
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < len(grid[0]) and 0 <= ny < len(grid)):
                continue
            if grid[ny][nx] == 1:
                continue
            neigh = (nx, ny)
            tentative = gscore[current] + 1
            if tentative < gscore.get(neigh, 1e9):
                came_from[neigh] = current
                gscore[neigh] = tentative
                f = tentative + abs(gx - nx) + abs(gy - ny)
                heapq.heappush(openh, (f, neigh))
    return None


def update_bullets(bullets, walls, enemies, player, start_pos, is_enemy=False):
    """Update bullets, handle bouncing, expiration and hits.
    is_enemy distinguishes enemy bullets (they only hit player) from player bullets (they hit enemies and can hit player).
    """
    for b in bullets[:]:
        b.update(walls)
        if b.expired() or b.off_screen():
            try:
                bullets.remove(b)
            except ValueError:
                pass
            continue

        if is_enemy:
            # enemy bullets only hurt the player
            if b.collides_with_rect(player.get_rect()):
                try:
                    bullets.remove(b)
                except ValueError:
                    pass
                player.x, player.y = start_pos
                player.angle = 0
                return 'player_hit'
        else:
            # player bullets can hit player (friendly fire)
            if b.owner == 'player' and b.collides_with_rect(player.get_rect()):
                try:
                    bullets.remove(b)
                except ValueError:
                    pass
                player.x, player.y = start_pos
                player.angle = 0
                return 'player_hit'

            # check enemies
            for e in enemies[:]:
                if b.collides_with_rect(e.get_rect()):
                    try:
                        enemies.remove(e)
                    except ValueError:
                        pass
                    try:
                        bullets.remove(b)
                    except ValueError:
                        pass
                    break


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

    # Start at level 1 for players (levels 1..MAX_LEVELS)
    level = 1
    lives = settings.PLAYER_LIVES
    won = False

    walls, start_pos, exit_rect, grid, theme = build_level(level)
    bg_color, wall_color, exit_color = theme
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
                    # fire slower player bullet (default owner set by Tank.fire)
                    player_bullets.append(player.fire())

        if not game_over:
            player.update(keys, walls)

            # enemies update

            # compute player cell once
            player_cell = cell_from_pos(grid, player.x, player.y)

            for e in enemies[:]:
                # recompute path every so often or if empty
                if not hasattr(e, 'path') or e.path is None:
                    e.path = None
                    e._path_timer = 0
                if not hasattr(e, '_path_timer'):
                    e._path_timer = 0

                # recompute path every N frames (lower for easier levels)
                recompute_every = max(20 - level * 2, 8)
                if e._path_timer <= 0 or not e.path:
                    start_cell = cell_from_pos(grid, e.x, e.y)
                    p = astar(grid, start_cell, player_cell)
                    e.path = p
                    e._path_timer = recompute_every

                # if path exists and has waypoints, pop reached waypoints here so enemy.update_ai can aim for first waypoint
                if e.path:
                    # remove waypoints that are very close
                    while e.path and math.hypot(e.path[0][0] - e.x, e.path[0][1] - e.y) < 6:
                        e.path.pop(0)

                # pass path to enemy AI
                b = e.update_ai(player, walls, path=e.path)
                e._path_timer -= 1
                if b:
                    enemy_bullets.append(b)

            # update bullets
            res = update_bullets(player_bullets, walls, enemies, player, start_pos, is_enemy=False)
            if res == 'player_hit':
                lives -= 1
                if lives <= 0:
                    game_over = True

            res = update_bullets(enemy_bullets, walls, enemies, player, start_pos, is_enemy=True)
            if res == 'player_hit':
                lives -= 1
                if lives <= 0:
                    game_over = True

            # check player reaching exit
            if player.get_rect().colliderect(exit_rect):
                # reached final level? (level is 1-based)
                if level >= settings.MAX_LEVELS:
                    won = True
                    game_over = True
                else:
                    level += 1
                    walls, start_pos, exit_rect, grid, theme = build_level(level)
                    bg_color, wall_color, exit_color = theme
                    player.x, player.y = start_pos
                    player.angle = 0
                    enemies = spawn_enemies(settings.ENEMY_BASE_COUNT + level, walls, start_pos, exit_rect)
                    player_bullets = []
                    enemy_bullets = []

        # draw
        screen.fill(bg_color)

        # walls
        for w in walls:
            pygame.draw.rect(screen, wall_color, w)

        # exit
        pygame.draw.rect(screen, exit_color, exit_rect)

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
