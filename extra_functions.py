import pygame, sys
from pygame.locals import *
from pygame import mixer
import os
import random
import math

# Tile size refers to the number of pixels per "tile",
#   both width and height-wise.
TILE_SIZE = 16
pygame.init()


def exit_game():
    """
    quits pygame and uses sys.exit to end game.
    """
    pygame.quit()
    sys.exit()


def load_image(fileName):
    """ Loads image from Assets folder, and returns it."""
    image = pygame.image.load(
        os.path.join("Assets", fileName)).convert_alpha()
    return image


def load_animation(fileNames):
    """
    Loads multiple images using the load_image function,
    returns them as a list in the same order.
    """
    animation = []
    for file in fileNames:
        animation += [load_image(file)]
    return animation


def load_sound(file_name, vol=0.4):
    """
    Loads a sound from the "Assets" folder based on the file name,
    and sets the volume to 0.4 unless otherwise defined. If the file name
    is incorrect or the file is unavailable, the game loads a silent sound.
    """
    try:
        sound = mixer.Sound(os.path.join("Assets", file_name))
        sound.set_volume(vol)
    except:
        # Muted sound file to use in case a sound is not available
        sound = mixer.Sound(
            os.path.join("Assets", "scratch_004.ogg"))
        sound.set_volume(0)
    return sound


def tile_pos(tile_x, tile_y):
    """ Converts given tile to standard pixel format, returns as tuple. """
    tile_x *= TILE_SIZE
    tile_y *= TILE_SIZE
    return [tile_x, tile_y]


def tile_size(tile):
    """ Converts given dimension to standard pixel format and returns it."""
    tile *= TILE_SIZE
    return tile


def un_tile_size(position):
    """
    Converts a value from a normal position into the non-rounded
    tile position. Example: If the X position is 64, it will divide
    by 16 and return a value of 4. Also returns floats.
    """
    position = position / TILE_SIZE
    return position


def get_color(colorName="black"):
    """
    Available colors: 'red', 'black', 'white', 'green', 'purple', 'gold'
    If string sent doesn't work as a color name, black is returned instead.
    """
    ALL_COLORS = {"red": (255, 0, 0), "black": (0, 0, 0), "white": (255, 255, 255),
                  "green": (0, 140, 0), "purple": (150, 0, 140), "gold":(255, 215, 0)}
    try:
        color = ALL_COLORS[colorName]
    except Exception as e:
        # print(e)
        color = ALL_COLORS["black"]
    return color


def did_collide(firstRect, secondRect):
    """
    Checks to see if two rects collide using colliderect().
    """
    if firstRect.colliderect(secondRect):
        return True
    else:
        return False


def draw_rect_outline(base_screen, rectangle, color_name="white"):
    """ Used as a dev feature, draws white outline around a given rectangle. """
    color = get_color(color_name)
    try:
        pygame.draw.rect(base_screen, color, rectangle, 2)
    except:
        pass


def draw_boss_health(base_screen, enemy_group):
    """
    Specifically used to draw boss health for player convenience.
    """
    for enemy in enemy_group:
        if enemy.is_boss:
            text_rect = enemy.rect.copy()
            text_rect.centery -= 12
            font = pygame.font.SysFont("timesnewroman", 10)
            if enemy.health < round(enemy.max_health/3):
                color = get_color("red")
            elif enemy.health < round(enemy.max_health/1.5):
                color = get_color("gold")
            else:
                color = get_color("green")
            render = font.render(str(enemy.health), 0, color)
            base_screen.blit(render, text_rect)


def set_music(file_name, volume=0.2):
    """
    Sets music according to file name given. Several global variables with
    music file names and volumes are used to save time when using function.
    """
    mixer.music.load(
        os.path.join("Assets", file_name))
    mixer.music.set_volume(volume)
    mixer.music.play(-1, 0.0)  # first arg sets to play infinitely, 2nd starts @ 0


class DisplayText(object):
    font_def = "timesnewroman"
    size_def = 12
    color_def = (0, 0, 0)
    background_def = None
    center_pos_def = (32, 32)
    KEY_LETTERS = {K_a:"a", K_b:"b", K_c:"c", K_d:"d", K_e:"e", K_f:"f", K_g:"g",
                   K_h:"h", K_i:"i", K_j:"j", K_k:"k", K_l:"l", K_m:"m", K_n:"n",
                   K_o:"o", K_p:"p", K_q:"q", K_r:"r", K_s:"s", K_t:"t", K_u:"u",
                   K_v:"v", K_w:"w", K_x:"x", K_y:"y", K_z:"z", K_SPACE:" "}
    VALID_KEYS = list(KEY_LETTERS.keys())
    
    def __init__(self, font_name, font_size, center_position,
                 font_color, font_background=None):
        """
    This class sets up a basic font system for displaying any text given
    to it at a specified position. Set default font name (from SysFont),
    the font size (int), position, font_color, font_background image, etc.
    Ended up unused in game.
        """
        if str(font_size).isdigit():
            self.font_size = font_size
        else:
            self.font_size = 12
        try:
            self.font = pygame.font.Font(font_name, self.font_size)
        except:
            try:
                self.font = pygame.font.SysFont(font_name, self.font_size)
            except:
                self.font = pygame.font.SysFont(
                    self.font_def, self.font_size)
                print("Failed to load given font.")
        self.color = font_color
        self.background = font_background
        self.position = self.position_def = center_position
        self.options = ["Yes", "No"]

    def get_valid_keys(self):
        return self.VALID_KEYS

    def get_letter(self, key):
        try:
            letter = self.KEY_LETTERS[key]
        except:
            letter = ""
        return letter
    
    def display(self, screen, lines, position=None):
        """
        Displays all lines of text given on screen. Separated by \n.
        """
        if position is not None:
            self.position = position
        # If lines is a string, turns into list
        if isinstance(lines,str):
            lines = [lines]

        # Create list of actual lines to print
        linesToPrint = []
        for line in lines[:]:
            if """\n""" in str(line):
                new_lines = line.split("""\n""")
                for newL in new_lines:
                    linesToPrint.append(str(newL))
            else:
                linesToPrint.append(str(line))

        for lin_num in range(len(linesToPrint)):
            if self.background is None:
                text = self.font.render(linesToPrint[lin_num], True, self.color)
            else:
                text = self.font.render(
                    linesToPrint[lin_num], True, self.color, self.background)
            textRect = text.get_rect()
            textRect.center = (self.position[0],
                               self.position[1]+round(lin_num*(textRect.height+2)))
            screen.blit(text, textRect)


def load_sprite_sheet(image_name):
    """
    Converts specific spritesheet format into images for NPC animations.
    Returns 4 lists in a list, each list being Up, Right, Down, Left sprites.
    """
    SPR_SIZE = [24, 32]
    sprite_sheet = load_image(image_name)

    all_lists = [[], [], [], []]

    spr_list = [None, None, None, None]
    for vert in range(4):
        for hor in range(3):
            pos_x = SPR_SIZE[0] * hor
            pos_y = SPR_SIZE[1] * vert
            spr_list[hor] = sprite_sheet.subsurface(
                pygame.Rect((pos_x, pos_y), SPR_SIZE))

        all_lists[vert] += [spr_list[1], spr_list[0], spr_list[1], spr_list[2]]
    return all_lists


def load_sprite_sheet_format(image_name, SPR_SIZE=[24, 32],
                             column_amount=3, row_amount=4, spr_order=[1, 0, 1, 2]):
    """
    Converts spritesheets into images for animations.
            Customizable version of load_sprite_sheet.
    Returns a nested list, with row_amount lists and column_amount images
    in each list.
    spr_order refers to how the images should be packed into each list;
        ex: [1, 0, 1, 2] puts 2nd, 1st, 2nd, 3rd image as list order.
    """
    sprite_sheet = load_image(image_name)

    all_lists, spr_list = [], []
    for i in range(row_amount):
        all_lists.append([])
    for i in range(column_amount):
        spr_list.append(None)

    for vert in range(row_amount):
        for hor in range(column_amount):
            pos_x = SPR_SIZE[0] * hor
            pos_y = SPR_SIZE[1] * vert
            spr_list[hor] = sprite_sheet.subsurface(
                pygame.Rect((pos_x, pos_y), SPR_SIZE))

        for i in spr_order:
            all_lists[vert].append(spr_list[i])

    return all_lists


if __name__ == "__main__":

    print("Please don't run from this file, just run the main game file.")
