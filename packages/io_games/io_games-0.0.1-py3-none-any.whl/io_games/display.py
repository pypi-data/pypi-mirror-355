import pygame
import sys

class Create():
    """"This class create window."""
    def __init__(self, width: int, height: int):
        pygame.init()
        self.width = width
        self.height = height
        self.window = pygame.display.set_mode((width, height))
        clock = pygame.time.Clock()

    def set_caption(title: str):
        pygame.display.set_caption(title)

    def set_icon(obj: str):
        pygame.display.set_icon(obj)

    def close():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    
