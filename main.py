import pygame
import settings
import tank

pygame.init()
screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
clock = pygame.time.Clock()

player = tank.Tank(settings.WIDTH // 2, settings.HEIGHT // 2, (0, 255, 0))

running = True
while running:
    clock.tick(settings.FPS)

    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.update(keys)

    screen.fill((20, 20, 20))
    player.draw(screen)

    pygame.display.flip()

pygame.quit()
#hi how are you