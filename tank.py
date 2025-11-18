import pygame
import math
import settings

class Tank:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.angle = 0
        self.color = color

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
        barrel_length = 35

        end_x = self.x + math.cos(rad) * barrel_length
        end_y = self.y + math.sin(rad) * barrel_length

        pygame.draw.line(
            screen,
            (255, 255, 0),
            (self.x, self.y),
            (end_x, end_y),
            6
        )
