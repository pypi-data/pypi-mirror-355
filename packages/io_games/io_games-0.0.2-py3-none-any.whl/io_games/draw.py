import pygame

pygame.init()
class init():
    def __init__(self, typeShape):
        self.typeShape = typeShape

    def getType(self):
        return self.typeShape

class rect(init):
    def __init__(self, window, color, rect, outline=0):
        self.rect = rect
        pygame.draw.rect(window, color, self.rect, outline)

    def getSize(self):
        return self.rect.get_size()

class circle(init):
    def __init__(self, window, color, rect, outline=0):
        self.rect = rect
        pygame.draw.circle(window, color, self.rect, outline)

    def getSize(self):
        return self.rect.get_size()

class triangle(init):
    def __init__(self, window, color, rect, outline=0):
        self.rect = rect
        pygame.draw.triangle(window, color, self.rect, outline)

    def getSize(self):
        return self.rect.get_size()
