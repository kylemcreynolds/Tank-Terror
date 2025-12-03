import pygame
import math
import random
import settings


class Tank:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.angle = 0
        self.color = color
        self.barrel_length = settings.TANK_SIZE

    def get_rect(self, x=None, y=None):
        if x is None:
            x = self.x
        if y is None:
            y = self.y
        size = settings.TANK_SIZE
        return pygame.Rect(int(x - size / 2), int(y - size / 2), size, size)

    def update(self, keys, walls):
        # Rotate tank
        if keys[pygame.K_LEFT]:
            self.angle -= settings.ROTATION_SPEED
        if keys[pygame.K_RIGHT]:
            self.angle += settings.ROTATION_SPEED

        rad = math.radians(self.angle)

        dx = 0
        dy = 0
        # Move forward
        if keys[pygame.K_UP]:
            dx += math.cos(rad) * settings.TANK_SPEED
            dy += math.sin(rad) * settings.TANK_SPEED

        # Move backward
        if keys[pygame.K_DOWN]:
            dx -= math.cos(rad) * settings.TANK_SPEED
            dy -= math.sin(rad) * settings.TANK_SPEED

        # Attempt move in x then y to allow sliding along walls
        new_x = self.x + dx
        rect_x = self.get_rect(new_x, self.y)
        coll_x = any(rect_x.colliderect(w) for w in walls)
        if not coll_x and 0 < new_x < settings.WIDTH:
            self.x = new_x

        new_y = self.y + dy
        rect_y = self.get_rect(self.x, new_y)
        coll_y = any(rect_y.colliderect(w) for w in walls)
        if not coll_y and 0 < new_y < settings.HEIGHT:
            self.y = new_y

    def draw(self, screen):
        # Draw tank body
        pygame.draw.rect(
            screen,
            self.color,
            self.get_rect()
        )

        # Draw barrel
        rad = math.radians(self.angle)

        end_x = self.x + math.cos(rad) * self.barrel_length
        end_y = self.y + math.sin(rad) * self.barrel_length

        pygame.draw.line(
            screen,
            (255, 255, 0),
            (int(self.x), int(self.y)),
            (int(end_x), int(end_y)),
            6
        )

    def fire(self, speed=4, owner='player'):
        """Return a Bullet fired from the tank's barrel tip."""
        rad = math.radians(self.angle)
        end_x = self.x + math.cos(rad) * self.barrel_length
        end_y = self.y + math.sin(rad) * self.barrel_length
        return Bullet(end_x, end_y, self.angle, speed=speed, owner=owner)


class Bullet:
    def __init__(self, x, y, angle, color=(255, 200, 0), speed=12, radius=4, owner=None):
        self.x = float(x)
        self.y = float(y)
        self.angle = angle
        rad = math.radians(angle)
        self.vx = math.cos(rad) * speed
        self.vy = math.sin(rad) * speed
        self.color = color
        self.radius = radius
        self.age_frames = 0
        self.max_age = int(settings.FPS * settings.BULLET_LIFETIME)
        self.owner = owner

    def update(self, walls=None):
        """Move bullet; if walls provided, bounce off wall rectangles instead of destroying the bullet.
        """
        # advance
        prev_x = self.x
        prev_y = self.y
        self.x += self.vx
        self.y += self.vy
        self.age_frames += 1

        # if walls given, check collision and reflect velocity accordingly
        if walls:
            # construct a small rect for the moving bullet
            br = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)
            for w in walls:
                if br.colliderect(w):
                    # determine from which side we collided by comparing previous center
                    px = prev_x
                    py = prev_y
                    collided_x = False
                    collided_y = False
                    # If previous x was left of wall and now inside or right -> hit left side => reflect vx
                    if px < w.left and self.x >= w.left:
                        collided_x = True
                    if px > w.right and self.x <= w.right:
                        collided_x = True
                    # Y sides
                    if py < w.top and self.y >= w.top:
                        collided_y = True
                    if py > w.bottom and self.y <= w.bottom:
                        collided_y = True

                    # If we couldn't determine side (corner or fast bullet), try overlap amounts
                    if not (collided_x or collided_y):
                        # compute overlaps
                        overlap_x = min(self.x + self.radius - w.left, w.right - (self.x - self.radius))
                        overlap_y = min(self.y + self.radius - w.top, w.bottom - (self.y - self.radius))
                        if overlap_x < overlap_y:
                            collided_x = True
                        else:
                            collided_y = True

                    if collided_x:
                        self.vx = -self.vx
                    if collided_y:
                        self.vy = -self.vy

                    # revert to previous position and step out in reflected direction to prevent sticking
                    self.x = prev_x
                    self.y = prev_y
                    # step out multiple times with reflected velocity to ensure clearance
                    for _ in range(10):
                        self.x += self.vx
                        self.y += self.vy
                        br = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)
                        if not br.colliderect(w):
                            break

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def off_screen(self):
        return (
            self.x < -self.radius
            or self.x > settings.WIDTH + self.radius
            or self.y < -self.radius
            or self.y > settings.HEIGHT + self.radius
        )

    def collides_with_rect(self, rect):
        return rect.collidepoint(int(self.x), int(self.y))

    def expired(self):
        return self.age_frames >= self.max_age


class EnemyTank(Tank):
    def __init__(self, x, y, color=(200, 30, 30)):
        super().__init__(x, y, color)
        self.fire_cooldown = random.randint(0, settings.ENEMY_FIRE_COOLDOWN)

    def update_ai(self, target, walls, path=None):
        """Update AI. If a path is provided (list of (x,y) pixel centers), follow it.
        Returns a Bullet when firing, otherwise None.
        """
        # If we have a path, follow next waypoint
        if path:
            # ensure path contains pixel centers; follow first waypoint
            wx, wy = path[0]
            dx = wx - self.x
            dy = wy - self.y
            dist = math.hypot(dx, dy)
            desired = math.degrees(math.atan2(dy, dx))

            # rotate toward waypoint
            diff = (desired - self.angle + 180) % 360 - 180
            if diff > 0:
                self.angle += min(diff, settings.ENEMY_ROTATION_SPEED)
            else:
                self.angle += max(diff, -settings.ENEMY_ROTATION_SPEED)

            # move toward waypoint
            if dist > 4:
                rad = math.radians(self.angle)
                dx_move = math.cos(rad) * settings.ENEMY_SPEED
                dy_move = math.sin(rad) * settings.ENEMY_SPEED

                # collision like player
                new_x = self.x + dx_move
                rect_x = self.get_rect(new_x, self.y)
                coll_x = any(rect_x.colliderect(w) for w in walls)
                if not coll_x:
                    self.x = new_x

                new_y = self.y + dy_move
                rect_y = self.get_rect(self.x, new_y)
                coll_y = any(rect_y.colliderect(w) for w in walls)
                if not coll_y:
                    self.y = new_y
            else:
                # reached waypoint; pop it from path (caller should do this)
                pass

        else:
            # fallback: aim directly at player (less effective in mazes)
            dx = target.x - self.x
            dy = target.y - self.y
            desired = math.degrees(math.atan2(dy, dx))
            diff = (desired - self.angle + 180) % 360 - 180
            if diff > 0:
                self.angle += min(diff, settings.ENEMY_ROTATION_SPEED)
            else:
                self.angle += max(diff, -settings.ENEMY_ROTATION_SPEED)

            rad = math.radians(self.angle)
            dx_move = math.cos(rad) * settings.ENEMY_SPEED
            dy_move = math.sin(rad) * settings.ENEMY_SPEED

            new_x = self.x + dx_move
            rect_x = self.get_rect(new_x, self.y)
            coll_x = any(rect_x.colliderect(w) for w in walls)
            if not coll_x:
                self.x = new_x

            new_y = self.y + dy_move
            rect_y = self.get_rect(self.x, new_y)
            coll_y = any(rect_y.colliderect(w) for w in walls)
            if not coll_y:
                self.y = new_y

        # handle firing cooldown unchanged
        self.fire_cooldown -= 1
        if self.fire_cooldown <= 0:
            self.fire_cooldown = settings.ENEMY_FIRE_COOLDOWN
            return self.fire(speed=3, owner='enemy')
        return None
