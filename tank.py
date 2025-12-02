import pygame
import math
import settings

class Tank:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.angle = 0
        self.color = color
        self.barrel_length = 35

    def update(self, keys):
        # Rotate tank
        if keys[pygame.K_LEFT]:
            self.angle -= settings.ROTATION_SPEED
        if keys[pygame.K_RIGHT]:
            self.angle += settings.ROTATION_SPEED

        rad = math.radians(self.angle)

        # Move forward
        if keys[pygame.K_UP]:
            self.x += math.cos(rad) * settings.TANK_SPEED
            self.y += math.sin(rad) * settings.TANK_SPEED

        # Move backward
        if keys[pygame.K_DOWN]:
            self.x -= math.cos(rad) * settings.TANK_SPEED
            self.y -= math.sin(rad) * settings.TANK_SPEED

    def draw(self, screen):
        # Draw tank body
        pygame.draw.rect(
            screen,
            self.color,
            pygame.Rect(
                self.x - settings.TANK_SIZE / 2,
                self.y - settings.TANK_SIZE / 2,
                settings.TANK_SIZE,
                settings.TANK_SIZE
            )
        )

        # Draw barrel
        rad = math.radians(self.angle)

        end_x = self.x + math.cos(rad) * self.barrel_length
        end_y = self.y + math.sin(rad) * self.barrel_length

        pygame.draw.line(
            screen,
            (255, 255, 0),
            (self.x, self.y),
            (end_x, end_y),
            6
        )

    def fire(self):
        """Return a Bullet fired from the tank's barrel tip."""
        rad = math.radians(self.angle)
        end_x = self.x + math.cos(rad) * self.barrel_length
        end_y = self.y + math.sin(rad) * self.barrel_length
        return Bullet(end_x, end_y, self.angle)


class Bullet:
    def __init__(self, x, y, angle, color=(255, 200, 0), speed=12, radius=4):
        self.x = float(x)
        self.y = float(y)
        self.angle = angle
        rad = math.radians(angle)
        self.vx = math.cos(rad) * speed
        self.vy = math.sin(rad) * speed
        self.color = color
        self.radius = radius

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def off_screen(self):
        return (
            self.x < -self.radius
            or self.x > settings.WIDTH + self.radius
            or self.y < -self.radius
            or self.y > settings.HEIGHT + self.radius
        )
