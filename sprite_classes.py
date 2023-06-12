from extra_functions import *

# Initializing pygame and setting several constants + screens #
pygame.init()

# Technically, the game uses a 320x320 resolution; however, it is scaled up
#   to 2x the resolution, at 640x640, for ease of visibility and use on
#   numerous systems. Time limitations kept further resolution options from
#   being implemented.
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 320

# These are the 3 music files used within the game; credits in game's
# credits menu in-game.
MENU_MUSIC = ["Harp (VWolfdog).ogg", 0.4]
GAME_MUSIC = ["Juhani Junkala [Retro Game Music Pack] Level 3.wav", 0.1]
BOSS_MUSIC = ["Juhani Junkala [Retro Game Music Pack] Level 2.wav", 0.1]
# Sets game screen to be created in the center of the computer monitor.
os.environ['SDL_VIDEO_CENTERED'] = "1"

# Everything is drawn onto the screen, and then upscaled 2x onto display.
screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
display = pygame.display.set_mode((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))

# Icon, caption, mouse visibility settings
pygame.display.set_icon(load_image("sword_icon.png"))
pygame.display.set_caption("Queen's Demise")
pygame.mouse.set_visible(False)

# Frames per second and game's clock
FPS = 60
clock = pygame.time.Clock()


def flip_screen(surface=screen):
    """
    Automatically scales the surface (typically the global screen)
    to the display, flips it, and ticks the clock.
    """
    pygame.transform.scale2x(surface, display)
    pygame.display.flip()
    clock.tick(FPS)


class AnimSprite(pygame.sprite.Sprite):
    """ Creates animated characters. Used for almost everything. """

    def __init__(self, position, sprite_list, animation_speed, max_speed,
                 animating=True, solid=False, repeat_animations=True):
        super().__init__()

        self.set_animations(sprite_list)
        self.animation_copy = self.anim.copy()

        # Setting the current sprite to 0, so it starts at the first image.
        self.current_sprite = 0
        self.anim_speed = animation_speed
        # How much to increase current_sprite by per frame.

        # Direction affects which set of images to animate from.
        self.direction = "d"
        self.image = self.anim[self.direction][0]

        # Several status variables. launch_dir is determined by the
        # direction of whatever hits instance. invincible is for invincibility
        # after being hit. death is to change the animation to an explosion
        # when the instance dies. inv_time is # of frames until hittable;
        # -1 or 0 means it is hittable.
        self.launch_dir = None
        self.invincible = False
        self.death = False
        self.inv_time = -1
        self.launch_stop = 0
        self.inv_time_start = round(0.3 * FPS)

        # Muted sound file to use in case a sound is not available
        self.fake_sound = load_sound("scratch_004.ogg", 0)

        # Arbitrarily large health pool to keep random things from dying.
        self.health = 500

        # Load noise that plays when hit
        self.damage_sound = load_sound("sfx_damage_hit10.ogg", 0.15)

        # boolean that determines whether to animate the image or not.
        self.is_animating = animating
        self.repeat_animations = repeat_animations

        # setting position of instance
        self.rect = self.image.get_rect()
        self.rect.center = self.true_center = list(position)
        # true_center used since rect turns all changes to int, true_center
        # will keep float values
        self.max_speed = max_speed
        self.speed = [0, 0]

        self.solid = solid
        self.fly = False
        # If the instance doesn't have a certain members (in case a derived
        # class creates it early), sets the class to default values.
        if not hasattr(self, "damage_type"):
            self.damage_type = "none"
        if not hasattr(self, "damage"):
            self.damage = 0
        if not hasattr(self, "key"):
            self.key = None
        if not hasattr(self, "affects"):
            self.affects = []
        if not hasattr(self, "is_puzzle"):
            self.is_puzzle = False
        if not hasattr(self, "is_boss"):
            self.is_boss = False

    def set_animations(self, sprite_list):
        # Creating the images for an animated sprite that flips horizontally.
        self.anim = {"d": load_animation(sprite_list),
                     "a": []}
        for image in self.anim["d"]:
            self.anim["a"] += [pygame.transform.flip(image, True, False)]

    def use(self):
        """ Used later for player's use ability. """
        pass

    def reset_anim(self):
        """ Resets self.anim, the dictionary used for self.image changes,
        back to the original dictionary set. """
        self.anim = self.animation_copy.copy()

    def has_hit(self):
        """ Used by several functions to determine what to do once the
        instance has hit another object."""
        pass

    def animate(self):
        if not self.is_animating:
            self.is_animating = True

    def set_animating(self, boolean):
        if isinstance(boolean, bool):
            self.is_animating = boolean

    def hit_by(self, other_object):
        """
        Function used to set the direction to push the character towards,
        the damage they've taken, and start their invincibility frames
        """
        if not self.invincible and other_object.damage != 0:
            self.play_damage_noise()
            self.health -= other_object.damage
            self.launch_dir = other_object.direction
            if self.damage_type != "none":
                other_object.has_hit()
            self.set_invincible(True)

    def play_damage_noise(self):
        self.damage_sound.play()

    def get_invincible(self):
        return self.invincible

    def set_invincible(self, option=None):
        default_time = self.inv_time_start
        if option is None:
            if self.invincible:
                self.invincible = False
                self.inv_time = -1
            else:
                self.invincible = True
                self.inv_time = default_time
        elif option or not option:
            self.invincible = option
            if option is True:
                self.inv_time = default_time

    def change_invincibility(self):
        self.invincible = False
        self.update_image()
        if self.health <= 0:
            self.destruct()

    def update(self):
        self.update_sprite()

        self.update_position()

        if self.inv_time > 0:
            self.inv_time -= 1

            # Draw red outline to show damage to character
            if self.death is False and self.inv_time > self.launch_stop:
                self.draw_outline()

        elif self.inv_time <= 0:
            self.change_invincibility()

    def update_position(self):
        self.rect.center = self.true_center[:]

    def update_sprite(self):
        if self.is_animating:
            self.current_sprite += self.anim_speed
            if self.current_sprite >= len(self.anim[self.direction]):
                self.current_sprite = 0
                if not self.repeat_animations:
                    self.is_animating = False
            self.update_image()

    def update_image(self):
        self.image = self.anim[self.direction][int(self.current_sprite)]

    def draw_outline(self, color="red"):
        try:
            imageOutline = pygame.mask.from_surface(self.image).outline()
            imageCopy = self.image.copy()
            pygame.draw.lines(imageCopy, get_color(color), True, imageOutline)
            self.image = imageCopy
        except Exception:
            pass

    def destruct(self):
        """ Overridden to kill() instance if needed on a class-by-class basis.
        Exists almost solely for the joke of calling it self.destruct()."""
        pass

    def move(self, target_object=None):
        pass

    def launch_away(self):
        change = [1.5, 1.5]
        own_x, own_y = self.true_center
        if self.launch_dir == "a" or self.launch_dir == "d":
            if self.launch_dir == "a":
                change[0] = -change[0]
            change[1] = 0
        if self.launch_dir == "w" or self.launch_dir == "s":
            if self.launch_dir == "w":
                change[1] = -change[1]
            change[0] = 0
        self.true_center = [own_x + change[0], own_y + change[1]]

    def chase(self, target_object):
        tar_pos = target_object.true_center
        own_pos = self.true_center
        max_vel = self.max_speed

        change = .05
        CORRECTION = .15

        # Changes direction of image to face player location
        if tar_pos[0] < own_pos[0]:
            self.set_direction("a")

        elif tar_pos[0] > own_pos[0]:
            self.set_direction("d")

        # Applies changes to instance speed, corrects if too fast
        for i in range(len(self.speed)):
            if tar_pos[i] <= own_pos[i]:
                self.speed[i] -= change
                if self.speed[i] <= -max_vel:
                    self.speed[i] += CORRECTION
                if self.speed[i] > 0:  # Doubles change if going wrong direction
                    self.speed[i] -= change
            else:
                self.speed[i] += change
                if self.speed[i] > max_vel:
                    self.speed[i] -= CORRECTION
                if self.speed[i] < 0:  # Doubles change if going wrong direction
                    self.speed[i] += change

        self.true_center = [self.true_center[0] + self.speed[0],
                            self.true_center[1] + self.speed[1]]

    def leap_at(self, target_object):
        """
        Unique movement created for slime. Leaps at the player,
        then waits for a semi-random time, and finally winds back up to
        leap at the player again.
        """

        WIND_UP = 30
        WAIT_TIME = random.randint(round(FPS / 2), FPS * 2)
        # Anywhere between a half second and 2 seconds of waiting.
        try:
            self.leap_timer -= 1
            self.wait_timer -= 1
            if self.leap_timer == self.wait_timer:  # Error prevention
                self.wait_timer += 1

        except Exception:  # Creates variables if first time through
            self.leap_timer = 0
            self.wait_timer = -1
            self.winding_up = False
            self.leaping = False
            self.waiting = True
            self.target_position = target_object.rect.center[:]
            self.change_x, self.change_y = 0, 0

        if self.wait_timer <= -1 and self.waiting:  # wind-up time start
            # Timers and booleans for managing what action to take in loop.
            self.leap_timer = WIND_UP
            self.winding_up = True
            self.waiting = False

            # Sets the target_position early so that player can dodge
            self.target_position = target_object.rect.center[:]
            dist_x = abs(self.rect.centerx - self.target_position[0])
            dist_y = abs(self.rect.centery - self.target_position[1])
            dist_total = dist_x + dist_y

            tar_x, tar_y = self.target_position
            own_x, own_y = self.rect.center
            if dist_x >= dist_y:
                if tar_x >= own_x:
                    self.set_direction("d")
                else:
                    self.set_direction("a")
            elif dist_y > dist_x:
                if tar_y >= own_y:
                    self.set_direction("s")
                else:
                    self.set_direction("w")
            if tar_x <= own_x:
                dist_x = -dist_x
            if tar_y <= own_y:
                dist_y = -dist_y

            self.change_x = 2 * self.max_speed * (dist_x / dist_total)
            self.change_y = 2 * self.max_speed * (dist_y / dist_total)

        if self.leap_timer <= 0 and self.winding_up:  # wait time start
            self.leaping = True
            self.winding_up = False
            if self.leap_sound is not None:
                self.leap_sound.play()

        if self.leaping:
            self.reset_anim()
            self.true_center[0] += self.change_x
            self.true_center[1] += self.change_y
            if self.leap_timer >= -10:
                self.true_center[1] -= 0.8
            if self.leap_timer <= -20:
                self.true_center[1] += 0.8

            self.current_sprite = 2
            # self.image = self.anim[self.direction][2]  # Stretched vertical sprite

            if self.leap_timer <= -30:
                self.waiting = True
                self.leaping = False
                self.wait_timer = WAIT_TIME

            # if self.true_center[0] >= self.target_position[0] and self.true_center[1] >= self.target_position[1]

        if self.winding_up:
            try:
                self.anim = self.squishAnim.copy()
            except Exception:
                pass

    def set_direction(self, direction):
        try:
            self.direction = direction
        except Exception:
            pass
        try:
            self.image = self.anim[self.direction][int(self.current_sprite)]
        except IndexError:
            self.current_sprite = 0
        else:
            pass


class GameMenu(object):
    def __init__(self, *status_options):
        self.options = {}
        self.text = {}
        self.render = {}

        self.x = 0
        self.y = 0
        self.font = pygame.font.Font(
            os.path.join("Fonts", "Kenney Mini Square.ttf"), 10)
        self.width = 1

        self.back_image = load_image("textbox.png")
        self.use_back_image = False

        self.highlight = get_color("green")
        self.color = get_color("black")

        self.move_sound = load_sound("sfx_menu_move2.wav", 0.3)
        self.select_sound = load_sound("sfx_menu_select2.wav", 0.3)

        i = 1

        for op in status_options:
            try:
                self.options[i] = op[1]
            except Exception:
                self.options[i] = None
            self.text[i] = str(op[0])
            self.render[i] = self.font.render(self.text[i], True, (0, 0, 0))
            if self.render[i].get_width() > self.width:
                self.width = self.render[i].get_width()
            i += 1

        self.opt_num = 1
        self.height = len(self.options) * self.font.get_height()

    def draw(self, given_screen):
        """ Draws the menu option by option. """
        for i in range(1, len(self.options) + 1):
            if self.opt_num == i:
                color = self.highlight
            else:
                color = self.color
            text = self.text[i]
            render = self.font.render(text, True, color)
            if render.get_width() > self.width:
                self.width = render.get_width()
            if self.use_back_image:
                img = pygame.transform.scale(self.back_image.copy(),
                                             (round(render.get_width() * 1.25),
                                              round(1.1 * self.font.get_height())))
                given_screen.blit(img, (self.x - 8, self.y + i * self.font.get_height()))
            given_screen.blit(render, (self.x, self.y + i * self.font.get_height()))

    def update(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                exit_game()
            if e.type == pygame.KEYUP:
                if e.key == K_s or e.key == K_DOWN:
                    self.opt_num += 1
                    self.move_sound.play()
                if e.key == K_w or e.key == K_UP:
                    self.opt_num -= 1
                    self.move_sound.play()
                if e.key == K_SPACE or e.key == K_RETURN or e.key == K_e:
                    if self.options[self.opt_num] is not None:
                        self.select_sound.play()
                        self.options[self.opt_num]()  # Run selected option
            if self.opt_num > len(self.options):
                self.opt_num = 1
            if self.opt_num < 1:
                self.opt_num = len(self.options)

    def set_pos(self, new_x, new_y):
        if str(new_x).isdigit() or isinstance(new_x, float):
            self.x = new_x
        if str(new_y).isdigit() or isinstance(new_y, float):
            self.y = new_y

    def set_font(self, font):
        self.font = font

    def set_highlight(self, color):
        if isinstance(color, tuple):
            self.highlight = color
        elif isinstance(color, str):
            try:
                self.highlight = get_color(color)
            except Exception:
                pass

    def set_color(self, color):
        if isinstance(color, tuple):
            self.color = color
        elif isinstance(color, str):
            try:
                self.color = get_color(color)
            except Exception:
                pass

    def center_at(self, new_x, new_y):
        render = self.font.render(self.text[1], True, self.color)
        render_rect = render.get_rect()
        render_rect.center = (new_x, new_y)
        self.x, self.y = render_rect.topleft

    def set_back_image(self):
        self.use_back_image = True

    def set_options(self, options):
        self.options = {}
        i = 1
        for op in options:
            try:
                self.options[i] = op[1]
            except Exception:
                self.options[i] = None
            self.text[i] = str(op[0])
            self.render[i] = self.font.render(self.text[i], True, (0, 0, 0))
            if self.render[i].get_width() > self.width:
                self.width = self.render[i].get_width()
            i += 1

        self.opt_num = 1
        self.height = len(self.options) * self.font.get_height()


class GameOptions(GameMenu):
    def __init__(self, *options):

        super().__init__(options[:])

        self.set_back_image()

        self.set_pos(tile_size(14.05), tile_size(11.25))

        self.font = pygame.font.SysFont("timesnewroman", 10)

        self.width = tile_size(2.5)

    def update(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                exit_game()
            if e.type == pygame.KEYUP:
                if e.key == K_s or e.key == K_DOWN:
                    self.opt_num += 1
                    self.move_sound.play()
                if e.key == K_w or e.key == K_UP:
                    self.opt_num -= 1
                    self.move_sound.play()
                if e.key == K_SPACE or e.key == K_RETURN or e.key == K_e:
                    if self.options[self.opt_num] is not None:
                        self.select_sound.play()
                        return self.options[self.opt_num]  # return selected option info
            if self.opt_num > len(self.options):
                self.opt_num = 1
            if self.opt_num < 1:
                self.opt_num = len(self.options)

    def draw(self, given_screen):
        for i in range(1, len(self.options) + 1):
            if self.opt_num == i:
                color = self.highlight
            else:
                color = self.color
            text = self.text[i]
            render = self.font.render(text, True, color)
            if render.get_width() > self.width:
                self.width = render.get_width()
            if self.use_back_image:
                img = pygame.transform.scale(self.back_image.copy(),
                                             (round(self.width * 1.25),
                                              round(1.1 * self.font.get_height())))
                given_screen.blit(img, (self.x - 8, self.y + i * self.font.get_height()))
            given_screen.blit(render, (self.x, self.y + i * self.font.get_height()))

    def set_option(self, option, num=None):
        if num is None:
            num = len(self.options) + 1
        try:
            self.options[num] = option[1]
        except Exception:
            self.options[num] = None
        self.text[num] = str(option[0])


class DialogueText(object):
    """
    Creates a separate loop for updates, events, drawing, etc.
    Takes the drawn screen, draws a text bubble near the bottom, and then
    draws the overall text one letter per frame.
    """

    def __init__(self, surface, name="", lines=None):
        """ Takes the base screen, the character's name, and the lines to display.
        The lines need to be in a list format, each element being one line to draw.
        Use None as an element in the list to separate each section of text.
        The max length of each line is about 52 chars, give or take."""
        if lines is None:
            lines = []
        self.name = name
        self.lines = lines

        # setting up indexes
        self.current_line = 0
        self.current_letter = 0
        self.line_number = 0
        # self.screen is drawing surface; current_text is the text to render
        self.screen = surface
        self.current_text = ["", "", ""]

        # originally used kenney font for dialogue, but was too illegible;
        # times new roman works well for size and readability
        self.font = pygame.font.SysFont("timesnewroman", 12)
        # Text colors; color used for main text, highlight for character name
        self.color = get_color("black")
        self.highlight = get_color("green")

        # Several booleans for managing input/letter adding/overall loop.
        self.cont_message = True
        self.waiting = False
        self.continue_loop = True

        # Text box image loading and positioning
        self.textbox = load_image("textbox.png")
        # yes, textbox_box isn't descriptive; no, it's not getting changed. :P
        self.textbox_box = self.textbox.get_rect()
        self.textbox_box.centerx = SCREEN_WIDTH / 2
        self.textbox_box.bottom = SCREEN_HEIGHT - 4

    def add_to_line(self):
        """ Adds one letter to the current_text list automatically. """
        if self.cont_message:  # If the message should continue, adds a letter.
            lines = self.lines
            line = lines[self.current_line]
            if line is not None:  # None used as way to separate each section
                self.current_text[self.line_number] += line[self.current_letter]
                self.current_letter += 1
                if self.current_letter > len(line) - 1:
                    self.current_letter = 0
                    self.current_line += 1
                    self.line_number += 1
                    if self.current_line > len(self.lines) - 1:  # if index > list length
                        self.cont_message = False
                        self.waiting = True
            elif line is None:
                self.waiting = True

    def draw(self, surface):
        """ Draws the textbox to the surface given, along with the name,
         and the text currently available. """
        surface.blit(self.textbox, self.textbox_box)
        surface.blit(self.font.render(self.name, True, self.highlight),
                     (self.textbox_box.left + 4, self.textbox_box.top + 2))
        for num, line in enumerate(self.current_text):
            # for each line in current_text, render it in the adjusted position.
            render = self.font.render(line, True, self.color)
            ren_rect = render.get_rect()
            ren_rect.topleft = [self.textbox_box.left + 8,
                                self.textbox_box.top + 20 + (num * 12)]
            surface.blit(render, ren_rect)

    def update(self, all_events):
        """ Updates the text, and then checks input for commands.
        e or enter key: advance to next section if current one is done.
            if text is done, the key ends the dialogue loop.
        space key: display all text instead of waiting for it to add. """
        self.add_to_line()
        for event in all_events:
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == KEYUP:
                if event.key == K_RETURN or event.key == K_e:
                    if self.waiting:
                        self.current_line += 1
                        self.current_letter = 0
                        self.line_number = 0
                        self.current_text = ["", "", ""]
                        self.waiting = False
                    if not self.cont_message:
                        self.continue_loop = not self.continue_loop

                if event.key == K_SPACE:
                    if not self.waiting and self.cont_message:
                        while self.lines[self.current_line] is not None:
                            self.current_text[self.line_number] = self.lines[self.current_line]
                            self.current_line += 1
                            self.line_number += 1
                            if self.current_line >= len(self.lines):
                                self.cont_message = not self.cont_message
                                break
                        self.waiting = True

    def loop(self):
        """ Main loop of Dialogue class. Runs updates and event checking,
        draws text, flips screen, etcetera. """
        # two copies of screen used to avoid blitting screen itself, and
        # to properly draw over prior frame.
        background = self.screen.copy()
        dialogue_screen = background.copy()

        while self.continue_loop:
            dialogue_screen.blit(background, (0, 0))
            self.update(pygame.event.get())
            self.draw(dialogue_screen)

            flip_screen(dialogue_screen)
        if not self.continue_loop:
            pass


class DeathCutscene(object):
    def __init__(self, player, ui_group):
        self.player = player
        self.heal_sound1 = load_sound("Menu2A.wav")
        self.heal_sound2 = load_sound("Item2A.wav")
        self.death_sound1 = load_sound("sfx_sounds_impact7.wav")
        self.death_sound2 = load_sound("sfx_sounds_impact3.wav")
        self.ui_group = ui_group

    def play_heal(self):
        self.heal_sound2.play()
        self.heal_sound1.play()

    def play_death(self):
        self.death_sound1.play()
        self.death_sound2.play()

    def loop(self, rooms):
        background_color = [255, 250, 250]
        cutscene_timer = 300
        potion_checked = False
        potion_succeed = False
        music_set = False
        mixer.music.pause()

        title = GameMenu(["You are dead"],
                         [""],
                         ["Continue?"])
        title.set_highlight(get_color("red"))
        title.set_back_image()
        title.set_pos(tile_size(8), tile_size(8))

        decision_options = [["Continue", "continue"], ["Exit (END GAME)", "end_game"]]

        death_decision = GameOptions(decision_options)
        for i in range(len(decision_options)):
            death_decision.set_option(decision_options[i], i + 1)
        choice = None

        while rooms.get_status("cutscene"):
            if cutscene_timer > -20:
                cutscene_timer -= 1
            screen.fill(background_color)

            events = pygame.event.get()

            self.ui_group.update()

            if cutscene_timer <= 250 and background_color[1] > 0:
                background_color[1] -= 10
                background_color[2] -= 10
                if background_color[1] <= 0:
                    background_color[1], background_color[2] = 0, 0

            if cutscene_timer <= 200 and not potion_checked:
                potion_checked = True
                if self.player.get_potions() > 0:
                    potion_succeed = True
                    self.player.potions -= 1
                    self.player.health = self.player.max_health
                    self.play_heal()
            if cutscene_timer == 100 and not potion_succeed:
                self.player.image = load_image("player_ded.png")
                self.player.rect.bottom += 12
                self.play_death()
            if cutscene_timer <= 0 and potion_succeed:
                rooms.set_status("cutscene", False)

                mixer.music.unpause()
            elif cutscene_timer <= 0 and not potion_succeed and not music_set:
                music_set = True
                set_music(MENU_MUSIC[0], MENU_MUSIC[1])

            if cutscene_timer < -15:
                choice = death_decision.update(events)

            if choice is not None:
                if choice == "continue":
                    if rooms.get_status("village_scene"):
                        self.player.true_center = tile_pos(4, 17)
                        rooms.room_num = [3, 4]
                    else:
                        self.player.true_center = tile_pos(10, 15.5)
                        rooms.room_num = [6, 7]
                    self.player.health = 12
                    self.player.set_invincible(False)

                    rooms.set_room_num()
                    rooms.set_status("cutscene", False)
                    rooms.set_status("room_transition", True)

                    set_music(GAME_MUSIC[0], GAME_MUSIC[1])

                    for ui in self.ui_group:
                        if ui.__class__.__name__ == "KeyCount":
                            self.ui_group.remove(ui)

                elif choice == "end_game":
                    exit_game()

            self.ui_group.draw(screen)

            for ui in self.ui_group:
                if ui.__class__.__name__ in ["UIIcon", "KeyCount"]:
                    ui.draw(screen)  # Draws ammo count for several equipment pieces
            screen.blit(self.player.image, self.player.rect)
            if music_set:
                title.draw(screen)
                death_decision.draw(screen)

            flip_screen()


class Enemy(AnimSprite):
    def __init__(self, position, animation_speed, max_speed, damage, health, alert_status,
                 sprites_right, sprites_left=None, sprites_up=None, sprites_down=None):

        self.explode = load_animation(["explosion0.png", "explosion1.png", "explosion2.png",
                                       "explosion3.png", "explosion4.png", "explosion5.png",
                                       "explosion6.png", "explosion7.png", "explosion8.png"])
        self.explode_sound = load_sound("sfx_exp_short_hard5.wav", 0.2)
        self.death_sound = load_sound("sfx_deathscream_robot1.wav", 0.3)

        self.animation_speed = animation_speed
        self.fly = False
        animating = True
        super(Enemy, self).__init__(
            position, sprites_right, animation_speed, max_speed, animating, repeat_animations=True)
        self.load_animation_original(sprites_left, sprites_down, sprites_up)

        self.start_position = position[:]
        self.base_image = self.anim["d"][0]
        self.health = health
        self.damage = damage
        self.death = False
        self.alert = alert_status
        self.surprise_icon = False

        self.wander_time = -1
        self.wander_direction = "d"

        self.animation_copy = self.anim.copy()
        self.hitbox = self.rect

    def reset_hitbox(self):
        pass

    def load_animation_original(self, sprites_left, sprites_down, sprites_up):
        if sprites_left is not None:
            self.anim["a"] = load_animation(sprites_left)
        if sprites_down is not None:
            self.anim["s"] = load_animation(sprites_down)
        if sprites_up is not None:
            self.anim["w"] = load_animation(sprites_up)

    def check_if_alert(self, player):
        if not self.alert:
            own_x, own_y = self.rect.center
            play_x, play_y = player.rect.center
            diff_x = abs(play_x - own_x)
            diff_y = abs(play_y - own_y)
            if (diff_x + diff_y <= tile_size(8)) or self.invincible:
                self.alert = True
                self.wander_time = 15
                # Uses wander_time to wait before targeting player

    def get_alert(self):
        return self.alert

    def update(self):
        super(Enemy, self).update()
        # self.is_animating = True

    def death_check(self):
        if self.death:
            if self.current_sprite >= 8:
                return "delete"

    def movement(self, player):
        pass

    def move(self, target_object=None):
        if target_object is not None:
            self.check_if_alert(target_object)
        if self.get_alert():
            if self.wander_time >= 0:
                self.wander_time -= 1
            elif not self.invincible and target_object is not None:
                self.movement(target_object)  # Runs individual's preferred movement
            if self.invincible:
                self.launch_away()
        else:
            self.unaware_move()
        self.update_position()

    def unaware_move(self):
        self.wander()

    def wander(self):
        orig_x, orig_y = self.start_position
        self.wander_time -= 1
        if self.wander_time <= -1:
            self.wander_time = random.randint(1, 3) * 20
            wander_changed = False
            axis_to_move = random.choice(["x", "y"])
            if axis_to_move == "x":
                if self.rect.centerx >= orig_x:
                    self.wander_direction = "a"
                    wander_changed = True
                elif self.rect.centerx < orig_x:
                    self.wander_direction = "d"
                    wander_changed = True
            else:
                if self.rect.centery >= orig_y:
                    self.wander_direction = "w"
                    wander_changed = True
                elif self.rect.centery > orig_y:
                    self.wander_direction = "s"
                    wander_changed = True
            if not wander_changed:  # if above failed to change dir:
                self.wander_direction = random.choice(["w", "d", "a", "s"])
            if self.wander_direction in self.anim.keys():
                self.direction = self.wander_direction
        if self.wander_time <= 30:  # Half second of no movement after wandering
            pass
        else:
            wander_speed = self.max_speed / 2
            DIRECTION_MOVES = {"d": [wander_speed, 0], "s": [0, wander_speed],
                               "a": [-wander_speed, 0], "w": [0, -wander_speed]}
            self.true_center[0] += DIRECTION_MOVES[self.wander_direction][0]
            self.true_center[1] += DIRECTION_MOVES[self.wander_direction][1]

    def set_dying(self):
        self.death = True
        self.explode_sound.play()
        self.death_sound.play()
        self.anim["a"] = self.anim["d"] = self.anim["w"] = self.anim["s"] = self.explode
        self.anim_speed = 20 / 60
        self.current_sprite = 0

    def run_at(self, target):
        target_pos = target.rect.center
        diff_x = abs(target_pos[0] - self.true_center[0])
        diff_y = abs(target_pos[1] - self.true_center[1])

        move_buffer = 16
        # Diagonal movement
        speed_to_use = self.max_speed
        if abs(diff_x - diff_y) <= move_buffer:  # Large buffer for diagonal movement
            speed_to_use = speed_to_use * 0.8
        # x plane movement
        if diff_x >= diff_y - move_buffer:
            if target_pos[0] <= self.true_center[0]:
                self.true_center[0] -= speed_to_use  # LEFT
                self.set_direction("a")
            else:
                self.true_center[0] += speed_to_use  # RIGHT
                self.set_direction("d")

        # y plane movement
        if diff_y >= diff_x - move_buffer:
            if target_pos[1] <= self.true_center[1]:
                self.true_center[1] -= speed_to_use  # UP
                self.set_direction("w")
            else:
                self.true_center[1] += speed_to_use  # DOWN
                self.set_direction("s")


class Bee(Enemy):
    def __init__(self, position):
        max_speed = 1.9
        animation_speed = 15 / 60
        damage = 1
        health = 8
        spritesR = ["bee1.png", "bee2.png"]
        alert_status = False
        super(Bee, self).__init__(position, animation_speed, max_speed,
                                  damage, health, alert_status, spritesR)
        self.fly = True

    def movement(self, target_object):
        self.chase(target_object)


class Eyebat(Enemy):
    def __init__(self, position):
        max_speed = 2.5
        animation_speed = 12 / 60
        damage = 2
        health = 12
        spritesR = ["eyebat0.png", "eyebat1.png", "eyebat2.png",
                    "eyebat3.png", "eyebat4.png", "eyebat5.png"]
        alert_status = False
        super().__init__(position, animation_speed, max_speed, damage,
                         health, alert_status, spritesR, spritesR, spritesR, spritesR)
        self.fly = True
        self.swap_timer_max = 30
        self.swap_timer = self.swap_timer_max

    def movement(self, target_object):
        self.chase(target_object)
        if self.swap_timer >= 0:
            self.true_center[1] += 0.2
        else:
            self.true_center[1] -= 0.2
        if self.swap_timer <= -30:
            self.swap_timer = self.swap_timer_max

    def update(self):
        self.swap_timer -= 1
        super().update()


class Slime(Enemy):
    def __init__(self, position):
        max_speed = 2
        animation_speed = 6 / 60
        health = 12
        damage = 2
        spritesR = ["slimeRight0.png", "slimeRight1.png", "slimeRight2.png", "slimeRight1.png"]
        spritesU = ["slimeUp0.png", "slimeUp1.png", "slimeUp2.png", "slimeUp1.png"]
        spritesD = ["slimeDown0.png", "slimeDown1.png", "slimeDown2.png", "slimeDown1.png"]
        alert_status = False
        super(Slime, self).__init__(position, animation_speed, max_speed, damage, health,
                                    alert_status, spritesR, None, spritesU, spritesD)

        self.squishAnim = {"w": [load_image("slimeUpSquish.png")],
                           "s": [load_image("slimeDownSquish.png")],
                           "d": [load_image("slimeRightSquish.png")]}
        self.squishAnim["a"] = [pygame.transform.flip(self.squishAnim["d"][0], True, False)]
        self.fly = False
        self.leap_sound = load_sound("power_up_02.ogg")

    def movement(self, target_object):
        self.leap_at(target_object)


class Log(Enemy):
    def __init__(self, position):
        max_speed = 1.4
        animation_speed = 4 / 60
        health = 24
        damage = 3
        spritesR = ["logRight0.png", "logRight1.png", "logRight2.png", "logRight3.png"]
        spritesU = ["logUp0.png", "logUp1.png", "logUp2.png", "logUp3.png"]
        spritesD = ["logDown0.png", "logDown1.png", "logDown2.png", "logDown3.png"]
        spritesL = ["logLeft0.png", "logLeft1.png", "logLeft2.png", "logLeft3.png"]
        alert_status = False
        super(Log, self).__init__(position, animation_speed, max_speed, damage, health, alert_status,
                                  spritesR, spritesL, spritesU, spritesD)
        self.animation_copy = self.anim.copy()
        self.anim["d"] = load_animation(["logSleep1.png", "logSleep1.png", "logSleep2.png", "logSleep3.png"])
        self.wakeAnim = load_animation(["logWake0.png", "logWake0.png", "logWake1.png", "logDown0.png", "logDown0.png"])
        self.damage_sound = load_sound("painb.wav")
        self.death_sound = load_sound("deathb.wav")

    def movement(self, target_object):
        WAKE_UP_TIME = 60
        try:
            if self.waking_up > 0:
                self.waking_up -= 1
        except Exception:
            self.waking_up = WAKE_UP_TIME
        if self.waking_up >= 0:
            pass
        if self.waking_up == WAKE_UP_TIME:
            self.anim["d"] = self.wakeAnim
            self.current_sprite = 0
            self.animation_speed += 4 / 60
        if self.waking_up == 0:
            self.anim = self.animation_copy
            self.run_at(target_object)

    def wander(self):
        self.wander_time -= 1
        if self.wander_time <= 0:
            self.wander_time = random.randint(1, 3) * 30


class Fang(Enemy):
    def __init__(self, position):
        animation_speed = 6 / FPS
        max_speed = 1.4
        alert_status = False
        spritesR = ["fang_right0.png", "fang_right1.png", "fang_right2.png", "fang_right3.png"]
        spritesU = ["fang_up0.png", "fang_up1.png", "fang_up2.png", "fang_up3.png"]
        spritesD = ["fang_down0.png", "fang_down1.png", "fang_down2.png", "fang_down3.png"]
        health = 16
        damage = 4
        super().__init__(position, animation_speed, max_speed, damage,
                         health, alert_status, spritesR, sprites_up=spritesU,
                         sprites_down=spritesD)
        self.move_timer_max = 90
        self.move_timer = self.move_timer_max
        self.direction = "d"
        self.alert = True
        self.surprise_icon = True

    def randomize_direction(self):
        DIRECTIONS = ["w", "a", "s", "d"]

        if self.direction in DIRECTIONS:
            dir_index = DIRECTIONS.index(self.direction)
            ran_index = random.choice([dir_index - 1, dir_index + 1])
            if ran_index <= 1 - len(DIRECTIONS):
                ran_index += len(DIRECTIONS)
            elif ran_index >= len(DIRECTIONS) - 1:
                ran_index -= len(DIRECTIONS)
            self.set_direction(DIRECTIONS[ran_index])
        if self.direction not in DIRECTIONS:
            # print(self.direction)
            pass

    def movement(self, player_obj):
        if self.direction == "s":  # Down
            self.true_center[1] += self.max_speed
        if self.direction == "w":  # Up
            self.true_center[1] -= self.max_speed
        if self.direction == "d":  # Right
            self.true_center[0] += self.max_speed
        if self.direction == "a":  # Left
            self.true_center[0] -= self.max_speed
        self.reset_hitbox()

    def reset_hitbox(self):
        self.rect = self.image.get_rect()
        self.rect.center = self.true_center

    def update(self):
        super().update()
        self.move_timer -= 1
        if self.move_timer <= 0:
            new_time = random.randint(round(
                self.move_timer_max / 2), self.move_timer_max)
            self.move_timer = new_time
            self.randomize_direction()

    def has_hit(self):
        self.move_timer = 0
        self.randomize_direction()


class Skeleton(Enemy):
    def __init__(self, position):
        max_speed = 1.5
        animation_speed = 8 / 60
        health = 16
        damage = 3
        sprite_list = load_sprite_sheet_format("tiny_skelly-NESW.png", [16, 18], 3, 4, [1, 0, 1, 2])
        sprites_r, sprites_u = sprite_list[1], sprite_list[0]
        sprites_d, sprites_l = sprite_list[2], sprite_list[3]
        alert_status = False
        super().__init__(position, animation_speed, max_speed, damage, health, alert_status,
                         sprites_r, sprites_l, sprites_u, sprites_d)
        self.damage_sound = load_sound("synth_laser_02.ogg")
        self.death_sound = load_sound("deathb.wav")

    def set_animations(self, sprite_list):
        self.anim = {"d": sprite_list}

    def load_animation_original(self, sprites_left, sprites_down, sprites_up):
        self.anim["w"] = sprites_up
        self.anim["s"] = sprites_down
        self.anim["a"] = sprites_left

    def movement(self, player):
        self.run_at(player)


class EnergyBlast(Enemy):
    """ Technically a projectile, but easiest way to get it into
    a group in the gameplay loop was to throw it in the Enemy group."""

    def __init__(self, position, boss_obj):
        max_speed = 1.75
        animation_speed = 8 / 60
        health = 100
        damage = 4
        alert_status = True
        sprite_list = ["dark_blast0.png", "dark_blast1.png"]

        super().__init__(position, animation_speed, max_speed, damage, health, alert_status,
                         sprite_list)
        self.BOUND_TO = boss_obj
        self.surprise_icon = True
        self.which_target = "player"

    def move(self, target_object=None):
        if self.which_target == "player":
            self.chase(target_object)
        elif self.which_target == "boss":
            self.chase(self.BOUND_TO)

    def hit_by(self, other_object):
        if other_object.damage_type == "sword" and self.which_target == "player":
            self.speed = [0, 0]
            self.play_damage_noise()
            self.which_target = "boss"
            other_object.has_hit()
            self.set_invincible(True)
        if other_object.is_boss and self.which_target == "boss":
            other_object.hit_by(self)
            self.destruct()

    def has_hit(self):
        self.destruct()

    def destruct(self):
        for group in self.groups():
            group.remove(self)
        self.kill()

    def update(self):
        super().update()
        if self.BOUND_TO.health <= 0:
            self.destruct()


class BossBase(Enemy):
    music_started = False

    def __init__(self, position, animation_speed, max_speed, damage, health,
                 sprites_r, sprites_l=None,
                 sprites_u=None, sprites_d=None, alert_status=True):
        super().__init__(position, animation_speed, max_speed, damage, health,
                         alert_status, sprites_r, sprites_l, sprites_u, sprites_d)
        if not BossBase.music_started:
            BossBase.music_started = True
            set_music(BOSS_MUSIC[0], BOSS_MUSIC[1])
        self.is_boss = True
        self.surprise_icon = True
        if not hasattr(self, "max_health"):
            self.max_health = self.health

    def destruct(self):
        set_music(GAME_MUSIC[0], GAME_MUSIC[1])
        BossBase.music_started = False
        self.kill()

    def move(self, target_object=None):
        self.movement(target_object)
        self.update_position()

    def set_animations(self, sprite_list):
        self.anim = {"w": load_animation(sprite_list),
                     "a": load_animation(sprite_list),
                     "s": load_animation(sprite_list),
                     "d": load_animation(sprite_list)}


class EyebossHead(BossBase):
    BODY_NUMBER = 0

    def __init__(self, position, sprites_r=None):
        if sprites_r is None:
            sprites_r = ["worm_head.png"]
        animation_speed = 0
        max_speed = 1.5
        damage = 3
        health = 40
        super().__init__(position, animation_speed, max_speed, damage, health,
                         sprites_r)
        self.alert_status = True
        self.move_timer_max = 120
        self.move_timer = self.move_timer_max
        self.direction = "d"
        self.max_health = health
        self.just_spawned = True
        self.boss_group = []
        self.prior_positions = []
        self.prior_directions = []
        EyebossHead.BODY_NUMBER += 1

    def update(self):
        super().update()
        self.prior_positions.append(self.true_center[:])
        self.prior_directions.append(self.direction)
        if self.just_spawned:
            self.just_spawned = False
            bind_obj = self
            position = self.true_center
            groups = self.groups()
            for i in range(14):
                self.boss_group.append(EyebossBody(position, bind_obj))
                bind_obj = self.boss_group[-1]
                position = bind_obj.true_center
                for g in groups:
                    g.add(self.boss_group[i])
        self.move_timer -= 1
        if self.health <= round(self.max_health / 2):
            self.max_speed = 1.8
        if self.move_timer <= 0:
            new_time = random.randint(round(
                self.move_timer_max / 2), self.move_timer_max)
            self.move_timer = new_time
            self.randomize_direction()

    def launch_away(self):
        pass

    def move(self, target_object=None):
        self.movement(target_object)
        self.update_position()

    def has_hit(self):
        self.move_timer = 0

    def reset_hitbox(self):
        self.rect = self.image.get_rect()
        self.rect.center = self.true_center

    def movement(self, player_obj):
        if self.direction == "s":  # Down
            self.true_center[1] += self.max_speed
        if self.direction == "w":  # Up
            self.true_center[1] -= self.max_speed
        if self.direction == "d":  # Right
            self.true_center[0] += self.max_speed
        if self.direction == "a":  # Left
            self.true_center[0] -= self.max_speed
        self.reset_hitbox()

    def set_animations(self, sprite_list):
        self.anim = {"w": [],
                     "a": [],
                     "s": [],
                     "d": load_animation(sprite_list)}
        for image in self.anim["d"]:
            self.anim["a"] += [pygame.transform.flip(image, True, False)]
            self.anim["s"] += [pygame.transform.rotate(image.copy(), 270)]
            self.anim["w"] += [pygame.transform.rotate(image.copy(), 90)]

    def randomize_direction(self):
        DIRECTIONS = ["w", "a", "s", "d"]

        if self.direction in DIRECTIONS:
            dir_index = DIRECTIONS.index(self.direction)
            ran_index = random.choice([dir_index - 1, dir_index + 1])
            if ran_index <= 1 - len(DIRECTIONS):
                ran_index += len(DIRECTIONS)
            elif ran_index >= len(DIRECTIONS) - 1:
                ran_index -= len(DIRECTIONS)
            self.set_direction(DIRECTIONS[ran_index])
        if self.direction not in DIRECTIONS:
            # print(self.direction)
            pass

    def destruct(self):
        EyebossHead.BODY_NUMBER -= 1
        if EyebossHead.BODY_NUMBER <= 0:
            set_music(GAME_MUSIC[0], GAME_MUSIC[1])
            BossBase.music_started = False
        self.kill()


# noinspection PyUnresolvedReferences
class EyebossBody(EyebossHead):
    def __init__(self, position, bind_obj=None, sprites_r=None):
        if sprites_r is None:
            sprites_r = ["worm_body.png"]
        health = 40
        super().__init__(position, sprites_r)
        self.health = health
        self.max_health = health
        self.damage = 2
        self.alert_status = True
        self.which_part = EyebossBody.BODY_NUMBER
        self.is_boss = True
        if bind_obj is not None:
            self.BOUND_TO = bind_obj
        self.just_spawned = False
        self.move_timer_max = 90
        self.move_timer = self.move_timer_max

    def move(self, target_object=None):
        if self.BOUND_TO is None:
            super().move(target_object)

    def update(self):
        bind_obj = self.BOUND_TO
        if bind_obj is not None and bind_obj.health <= 0:
            self.set_animations(["worm_head.png"])
            self.BOUND_TO = None
            super().update()
        elif bind_obj is None:
            super().update()
        else:
            BossBase.update(self)
            if len(bind_obj.prior_positions) >= 10:
                self.prior_positions.append(self.true_center[:])
                self.prior_directions.append(self.direction)
                self.true_center = bind_obj.prior_positions.pop(0)
                self.set_direction(bind_obj.prior_directions.pop(0))
            if self.invincible:
                self.draw_outline()

    def launch_away(self):
        pass

    def set_animations(self, sprite_list):
        self.anim = {"w": [],
                     "a": [],
                     "s": [],
                     "d": load_animation(sprite_list)}
        for image in self.anim["d"]:
            self.anim["a"] += [pygame.transform.flip(image, True, False)]
            self.anim["s"] += [pygame.transform.rotate(image.copy(), 270)]
            self.anim["w"] += [pygame.transform.rotate(image.copy(), 90)]


class DemonQueen(BossBase):
    def __init__(self, position):
        sprite_list = ["queen0.png", "queen1.png", "queen2.png", "queen1.png"]
        animation_speed = 6 / FPS
        max_speed = 1.5
        damage = 4
        health = 500
        super().__init__(position, animation_speed, max_speed, damage, health, sprite_list)
        attack_image = load_image("queen_attack.png")
        self.attack_anim = {"w": [attack_image],
                            "a": [attack_image],
                            "s": [attack_image],
                            "d": [attack_image]}
        self.damage_type = "all"
        self.fly = True
        self.move_timer_max = 4 * FPS
        self.move_timer = 1
        self.attack_timer_max = round(1.5 * FPS)
        self.attack_timer = self.attack_timer_max
        self.can_move = True
        self.speed = [0, 0]
        self.max_health = self.health

    def destruct(self):
        mixer.music.fadeout(2000)
        BossBase.music_started = False
        self.kill()

    def movement(self, player):
        change = 1
        if self.can_move:
            if 240 >= self.move_timer > 210:
                self.speed[0] = -change
                self.speed[1] = change

            elif 210 >= self.move_timer > 180:
                self.speed[0] = -change
                self.speed[1] = -change

            elif 180 >= self.move_timer > 150:
                self.speed[0] = change
                self.speed[1] = -change

            elif 150 >= self.move_timer > 135:
                self.speed[1] = change

            elif 90 >= self.move_timer > 60:
                self.speed[1] = -change

            elif 60 >= self.move_timer > 30:
                self.speed[0] = -change
                self.speed[1] = -change

            elif 30 >= self.move_timer > 0:
                self.speed[0] = -change
                self.speed[1] = change

            self.true_center = [self.true_center[0] + self.speed[0],
                                self.true_center[1] + self.speed[1]]

    def set_animations(self, sprite_list):
        self.anim = {"w": load_animation(sprite_list),
                     "a": load_animation(sprite_list),
                     "s": load_animation(sprite_list),
                     "d": load_animation(sprite_list)}

    def attack(self):
        for group in self.groups():
            group.add(EnergyBlast(self.rect.midleft, self))
            group.add(EnergyBlast(self.rect.midright, self))

    def update(self):
        super().update()
        if self.can_move:
            self.move_timer -= 1
            if self.move_timer <= 0:
                self.move_timer = self.move_timer_max
        self.attack_timer -= 1
        if self.attack_timer == 0:
            self.anim = self.attack_anim.copy()
            self.can_move = False
        if self.attack_timer == -30:
            self.attack()
        if self.attack_timer == -45:
            self.attack_timer = random.randint(self.attack_timer_max, self.attack_timer_max * 2)
            self.anim = self.animation_copy.copy()
            self.can_move = True


class SurpriseIcon(AnimSprite):
    def __init__(self, enemy):
        position = (0, 0)
        animation_speed = 0
        sprite_list = ["surprise.png"]
        self.life_time = round(FPS / 2)
        max_speed = 0
        super(SurpriseIcon, self).__init__(position, sprite_list, animation_speed, max_speed)
        self.bound_to = enemy
        self.update()
        self.sound = load_sound("sfx_sounds_error14.wav", 0.6)
        self.sound.play()

    def update(self):
        self.rect.center = [self.bound_to.true_center[0], self.bound_to.rect.top - self.rect.height / 2]
        self.life_time -= 1
        if self.life_time <= 0:
            self.kill()


class NormalItem(AnimSprite):
    def __init__(self, position, sprite_list, animation_speed, key=None, animating=True):
        maxSpeed = 0
        self.name = None
        self.original_position = position[:]
        position = tile_pos(position[0], position[1])
        super(NormalItem, self).__init__(position, sprite_list, animation_speed, maxSpeed, animating)
        self.direction = "d"
        self.key = key

        self.item_noise = load_sound("sfx_sounds_interaction17.wav", 0.2)

        if not hasattr(self, "is_puzzle"):
            self.is_puzzle = False

    def update(self):
        super(NormalItem, self).update()
        self.animate()

    def get_x(self):
        return self.original_position[0]

    def get_y(self):
        return self.original_position[1]

    def get_key(self):
        return self.key

    def destruct(self):
        self.item_noise.play()
        self.kill()


class HeartItem(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["heart0.png", "heart1.png", "heart2.png", "heart3.png",
                      "heart0.png", "heart0.png", "heart0.png", "heart0.png"]
        animation_speed = 15 / 60
        animating = True
        super().__init__(position, sprite_list,
                         animation_speed, key, animating)
        self.name = "heart"


class HeartContainer(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["heartContainer0.png", "heartContainer1.png", "heartContainer2.png",
                       "heartContainer3.png", "heartContainer0.png", "heartContainer0.png",
                       "heartContainer0.png", "heartContainer0.png", "heartContainer0.png",
                       "heartContainer0.png", "heartContainer0.png", "heartContainer0.png", ]
        animation_speed = 15 / 60
        animating = True
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "heart_up"


class ArrowItem(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["arrow_drop.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "arrow"


class BombItem(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["bomb_drop.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "bomb"


class FlameItem(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["flame_drop.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "flame"


class GoldItem(NormalItem):
    def __init__(self, position, key=None):
        """Creates a gold instance with a random chance of being worth
        1, 5, 20, 50, or 100 gold."""
        chance = random.randint(0, 20)
        if chance <= 8:
            amount = 1
            sprite_list = ["coin_01d.png"]
        elif chance <= 12:
            amount = 5
            sprite_list = ["coin_02d.png"]
        elif chance <= 17:
            amount = 20
            sprite_list = ["coin_03d.png"]
        elif chance <= 19:
            amount = 50
            sprite_list = ["coin_04d.png"]
        elif chance <= 20:
            amount = 100
            sprite_list = ["coin_05d.png"]
        else:
            amount = 1
            sprite_list = ["coin_01d.png"]

        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "gold"
        self.amount = amount


class SwordUpgrade(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["sword_icon.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "sword"


class BombUpgrade(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["bomb_bag.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "bomb_bag"


class BowUpgrade(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["bow_03a.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "bow"


class FlameUpgrade(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["flame_glove.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "flame_glove"


class KeyItem(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["key_01c.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "key"
        self.item_noise = load_sound("sfx_sounds_pause7_in.wav")


class BossKeyItem(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["key_01d.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "boss_key"
        self.item_noise = load_sound("sfx_sounds_pause7_in.wav")


class QueenKeyItem(NormalItem):
    def __init__(self, position, key=None):
        sprite_list = ["key_01e.png"]
        animation_speed = 0
        animating = False
        super().__init__(position, sprite_list, animation_speed, key, animating)
        self.name = "queen_key"
        self.item_noise = load_sound("sfx_sounds_pause7_in.wav")


class PlayerEquipment(AnimSprite):
    """
    Used to give player key items to use throughout gameplay.
    Derived classes are used to simplify each instance's creation.
    """
    USE_KEYS = [None]

    def __init__(self, player_obj, sprite_list, damage, damage_type, noise, max_ammo):
        animation_speed = (30 / 60)
        position = [0, 0]
        animating = False
        max_speed = 0
        super().__init__(position, sprite_list, animation_speed,
                         max_speed, animating)
        self.anim = {"d": load_animation(sprite_list),
                     "s": [], "a": [], "w": []}
        for image in self.anim["d"]:
            self.anim["a"] += [pygame.transform.flip(image, True, False)]
            self.anim["s"] += [pygame.transform.rotate(image.copy(), 270)]
            self.anim["w"] += [pygame.transform.rotate(image.copy(), 90)]
        self.BOUND_TO = player_obj

        self.rect = self.image.get_rect()

        self.use_sound = load_sound(noise, 0.3)
        self.set_center_positions()

        self.use_timer = -1

        self.damage = damage
        self.damage_type = damage_type

        self.max_ammo = max_ammo
        if self.max_ammo == -1:
            self.ammo = -1
        else:
            self.ammo = 0
        self.rect.center = self.center_positions[self.direction]

        self.is_equipped = False
        self.is_pressed = False
        self.use_key = [None]

    def set_center_positions(self):
        """ Updates the possible center positions based on the player's. """
        self.center_positions = {
            "d": [(self.BOUND_TO.rect.right + round(self.rect.width / 2)),
                  self.BOUND_TO.rect.centery],
            "s": [self.BOUND_TO.rect.centerx,
                  (self.BOUND_TO.rect.bottom + round(self.rect.height / 2))],
            "a": [(self.BOUND_TO.rect.left - round(self.rect.width / 2)),
                  self.BOUND_TO.rect.centery],
            "w": [self.BOUND_TO.rect.centerx,
                  self.BOUND_TO.rect.top - round(self.rect.height / 2)]}

    def is_using(self):
        if self.use_timer != -1:
            return True
        else:
            return False

    def get_sound(self):
        if self.enough_ammo():
            snd = self.use_sound
        elif self.no_ammo_sound is not None:
            snd = self.no_ammo_sound
        else:
            snd = self.fake_sound
        return snd

    def animate(self):
        if not self.is_animating:
            try:
                self.get_sound().stop()
            except Exception:
                pass
            self.get_sound().play()
            self.is_animating = True

    def add_ammo(self, amount_to_add):
        if self.max_ammo != -1:
            self.ammo += amount_to_add
            if self.ammo > self.max_ammo:
                self.ammo = self.max_ammo

    def get_ammo(self):
        return self.ammo

    def enough_ammo(self):
        if self.ammo > 0 or self.ammo == -1:
            boolean = True
        else:
            boolean = False
        return boolean

    def start_use(self):
        self.use_timer = 15
        self.is_pressed = True

    def end_use(self):
        self.is_pressed = False

    def is_used(self):
        if self.use_timer == 0:
            if self.enough_ammo():
                boolean = True
                if self.ammo > 0:
                    self.ammo -= 1
            else:

                boolean = False
        else:
            boolean = False
        return boolean

    def update(self):
        self.rect.center = self.BOUND_TO.rect.center
        self.set_direction(self.BOUND_TO.direction)

        if self.is_animating:
            self.current_sprite += self.anim_speed
            if self.current_sprite >= len(self.anim[self.direction]):
                self.current_sprite = 0
                self.is_animating = False
            self.image = self.anim[self.direction][int(self.current_sprite)]
        if self.use_timer >= 0:
            self.use_timer -= 1

    def set_direction(self, direction):
        self.direction = direction
        if self.current_sprite >= len(self.anim[self.direction]):
            self.current_sprite = 0
        self.image = self.anim[self.direction][int(self.current_sprite)]
        self.set_center_positions()
        self.rect = self.image.get_rect()
        self.rect.center = self.center_positions[self.direction]

    def equip_item(self):
        self.use_key = self.USE_KEYS


class Sword(PlayerEquipment):
    USE_KEYS = [K_SPACE]

    def __init__(self, player_object):
        sprite_list = ["slash0.png", "slash1.png", "slash2.png", "slash3.png",
                       "slash4.png", "slash5.png", "slash6.png"]
        damage = 4
        damage_type = "sword"
        max_ammo = -1
        super().__init__(player_object, sprite_list, damage,
                         damage_type, "toggle_003.ogg", max_ammo)


class Bow(PlayerEquipment):
    USE_KEYS = [K_j, K_b]

    def __init__(self, player_object):
        sprite_list = ["slash0.png", "bow0.png", "bow0.png", "bow0.png", "bow0.png", "bow0.png"]
        damage = 0
        damage_type = "none"
        max_ammo = 20
        super().__init__(player_object, sprite_list, damage,
                         damage_type, "sfx_damage_hit1.wav", max_ammo)
        self.anim_speed = 15 / 60
        self.no_ammo_sound = load_sound("sfx_wpn_noammo1.wav", 0.5)
        self.ammo = self.max_ammo


class HookShot(PlayerEquipment):
    """
    This class was originally going to be used in the game,
    but due to time constraints, was left out of final cut.
    """
    USE_KEYS = [K_z]

    def __init__(self, player_object):
        sprite_list = ["slash0.png", "hookshot1.png", "hookshot1.png", "hookshot1.png"]
        damage = 6
        damage_type = "hookshot"
        max_ammo = -1
        super().__init__(player_object, sprite_list, damage,
                         damage_type, "Shoot 3.wav", max_ammo)
        self.anim_speed = 10 / 60

    def is_using(self):
        return Bow.is_using(self)


class BombBag(PlayerEquipment):
    USE_KEYS = [K_k]

    def __init__(self, player_object):
        sprite_list = ["slash0.png", "place_bomb0.png", "place_bomb0.png", "place_bomb0.png", "place_bomb0.png"]
        damage = 0
        damage_type = "none"
        max_ammo = 10
        super().__init__(player_object, sprite_list, damage, damage_type,
                         "sfx_damage_hit10.ogg", max_ammo)
        self.use_sound.set_volume(0.6)
        self.no_ammo_sound = load_sound("sfx_wpn_noammo1.wav")
        self.ammo = self.max_ammo

    def start_use(self):
        self.use_timer = 3
        self.is_pressed = True

    def is_using(self):
        return Bow.is_using(self)


class FlameGlove(PlayerEquipment):
    USE_KEYS = [K_f, K_l]

    def __init__(self, player_object):
        sprite_list = ["slash0.png", "place_bomb0.png", "place_bomb0.png", "place_bomb0.png", "place_bomb0.png"]
        damage = 8
        damage_type = "fire"
        max_ammo = 10
        super().__init__(player_object, sprite_list, damage, damage_type,
                         "spell_fire_05.ogg", max_ammo)
        self.no_ammo_sound = load_sound("misc_03.ogg")
        self.ammo = self.max_ammo

    def is_using(self):
        return Bow.is_using(self)


class Projectile(AnimSprite):
    def __init__(self, sprite_list, origin_object, animation_speed,
                 max_speed, animating, damage, damage_type):
        position = list(origin_object.rect.center)[:]
        super().__init__(position[:], sprite_list, animation_speed, max_speed, animating)
        self.damage = damage
        self.damage_type = damage_type

        self.anim["a"] = []
        self.anim["s"] = []
        self.anim["w"] = []
        for image in self.anim["d"]:
            self.anim["a"] += [pygame.transform.flip(image, True, False)]
            self.anim["s"] += [pygame.transform.rotate(image.copy(), 270)]
            self.anim["w"] += [pygame.transform.rotate(image.copy(), 90)]
        self.set_direction(origin_object.direction)
        self.rect = self.image.get_rect()
        self.update_position()

    def has_hit(self):
        pass

    def move(self, target_object=None):
        pass


class FlameThrow(Projectile):
    def __init__(self, origin_object):
        animation_speed = 6 / 60
        max_speed = 0.8
        animating = True
        sprite_list = ["explosion0.png", "explosion1.png", "explosion2.png", "explosion3.png",
                       "explosion0.png", "explosion1.png", "explosion2.png", "explosion3.png"]
        damage = 4
        damage_type = "fire"
        Projectile.__init__(self, sprite_list, origin_object, animation_speed,
                            max_speed, animating, damage, damage_type)
        self.life_timer = 1.5 * FPS
        self.anim["s"] = self.anim["a"] = self.anim["w"] = self.anim["d"][:]
        self.fire_sound = load_sound("spell_fire_03.ogg", 0.3)
        self.fire_sound.play()
        self.health = 3

    def has_hit(self):
        self.health -= 1
        if self.health == 0:
            self.destruct()

    def destruct(self):
        self.kill()

    def move(self, target_object=None):
        if self.direction == "a":
            self.true_center[0] -= self.max_speed
        if self.direction == "d":
            self.true_center[0] += self.max_speed
        if self.direction == "w":
            self.true_center[1] -= self.max_speed
        if self.direction == "s":
            self.true_center[1] += self.max_speed

    def update(self):
        super().update()
        if self.fire_sound.get_num_channels() < 1:
            self.fire_sound.play()
        self.life_timer -= 1
        if self.life_timer <= 0:
            self.fire_sound.stop()
            self.kill()


class Arrow(Projectile):
    def __init__(self, origin_object):
        animation_speed = 0
        max_speed = 3
        animating = True
        sprite_list = ["arrow0.png"]
        damage = 8
        damage_type = "arrow"
        Projectile.__init__(self, sprite_list, origin_object, animation_speed,
                            max_speed, animating, damage, damage_type)
        self.health = 3

    def move(self, target_object=None):
        if self.direction == "a":
            self.true_center[0] -= self.max_speed
        if self.direction == "d":
            self.true_center[0] += self.max_speed
        if self.direction == "w":
            self.true_center[1] -= self.max_speed
        if self.direction == "s":
            self.true_center[1] += self.max_speed

    def has_hit(self):
        self.health -= 1
        if self.health == 0:
            self.destruct()

    def destruct(self):
        self.kill()


class BombPlaced(Projectile):
    def __init__(self, origin_object):
        animation_speed = 7 / FPS
        max_speed = 0
        animating = True
        sprite_list = ["bomb0.png", "bomb0.png", "bomb0.png", "bomb1.png",
                       "bomb1.png", "bomb1.png", "bomb0.png", "bomb0.png",
                       "bomb1.png", "bomb1.png", "bomb0.png", "bomb1.png",
                       "bomb0.png", "bomb1.png", "bomb0.png", "bomb1.png"]
        damage = 0
        damage_type = "none"
        Projectile.__init__(self, sprite_list, origin_object, animation_speed,
                            max_speed, animating, damage, damage_type)
        self.bomb_timer = 2.5 * FPS
        self.anim["s"] = self.anim["a"] = self.anim["w"] = self.anim["d"][:]

    def has_hit(self):
        pass

    def update(self):
        super().update()
        self.bomb_timer -= 1
        if self.bomb_timer <= 0:
            for g in self.groups():
                g.add(BombExplode(self))
            self.kill()


class BombExplode(Projectile):
    def __init__(self, origin_object):
        animation_speed = 8 / FPS
        max_speed = 0
        animating = True
        sprite_list = random.choice(["bomb_exp0.png", "bomb_exp1.png"])
        # Explosion animations, randomly selected
        damage = 12
        damage_type = "bomb"
        Projectile.__init__(self, sprite_list, origin_object, animation_speed,
                            max_speed, animating, damage, damage_type)
        self.explode_sound = load_sound("8bit_bomb_explosion.wav")
        self.explode_sound.play()

    def has_hit(self):
        pass

    def update(self):
        if self.current_sprite >= 6:
            self.kill()
        super().update()

    def set_animations(self, spritelist):
        self.anim = {"d": load_sprite_sheet_format(
            spritelist, [32, 32], 6, 1, [0, 1, 2, 3, 4, 5, 5])[0]}
        self.anim["a"] = self.anim["w"] = self.anim["s"] = self.anim["d"][:]


class UIIcon(pygame.sprite.Sprite):
    def __init__(self, icon, icon_position, get_text):
        super().__init__()
        try:
            self.font = pygame.font.Font(
                os.path.join("Fonts", "Kenney Mini Square.ttf"), 10)
        except Exception:
            self.font = pygame.font.SysFont(
                "timesnewroman", 10)

        self.image = load_image(icon)
        self.rect = self.image.get_rect()
        self.rect.topleft = icon_position
        self.get_text = get_text
        self.update()

    def update(self):
        # noinspection PyAttributeOutsideInit
        self.text = str(self.get_text())

    def draw(self, some_screen):
        render = self.font.render(self.text, True, get_color("white"), get_color("black"))
        render_rect = render.get_rect()
        render_rect.center = [self.rect.centerx, self.rect.bottom + 6]
        some_screen.blit(render, render_rect)


class KeyCount(UIIcon):
    def __init__(self):
        self.keys = 0
        get_text = self.get_keys
        super().__init__("key_01c.png", tile_pos(16, 0), get_text)
        # self.keys = 0
        self.boss_key = 0

    def draw(self, some_screen):
        super().draw(some_screen)
        if self.boss_key != 0:
            render2 = self.font.render(str(self.get_boss_keys()), True,
                                       get_color("gold"), get_color("black"))
            render2_rect = render2.get_rect()
            render2_rect.center = [self.rect.centerx + 8,
                                   self.rect.bottom + 6]
            some_screen.blit(render2, render2_rect)

    def get_keys(self):
        return self.keys

    def get_boss_keys(self):
        return self.boss_key

    def add_boss_key(self):
        self.boss_key += 1

    def remove_boss_key(self):
        self.boss_key -= 1

    def add_key(self):
        self.keys += 1

    def remove_key(self):
        self.keys -= 1
        if self.keys <= 0:
            self.keys = 0


class Player(AnimSprite):
    """ Player's class. """
    # Original sprites for character during testing
    IMAGES = {"s": load_image("zoeySprite.png"),
              "w": load_image("zoeyBack.png"),
              "a": load_image("zoeyLeft.png"),
              "d": load_image("zoeyRight.png")}
    ALL_REGIONS = ["tundra", "mountains", "tower"]

    def __init__(self):
        spr_list = load_sprite_sheet_format("Aristocrate-F-01 dark.png")
        self.IMAGES = {"s": spr_list[2],
                       "w": spr_list[0],
                       "a": spr_list[3],
                       "d": spr_list[1]}
        Player.images = self.IMAGES.copy()
        spriteList = ["zoeySprite.png"]  # Original sprite for the game, used for rect
        position = tile_pos(3, 17)
        animation_speed = 8 / 60
        maxSpeed = 2
        animating = True

        super().__init__(position, spriteList, animation_speed, maxSpeed, animating)

        self.image = self.IMAGES["s"][0]
        self.rect = self.image.get_rect()

        # Spawn point
        self.rect.center = position

        self.hitbox = self.rect.copy()
        self.hitbox.width = round(self.rect.width * 5 / 9)
        self.hitbox.height = round(self.rect.height * 7 / 10)

        self.reset_hitbox()

        self.health = 12
        self.max_health = 12
        self.potions = 3
        self.max_potions = 3

        self.speed = 2
        self.direction = "s"
        self.moving = {"s": False, "w": False, "a": False, "d": False}

        self.inv_time_start = round(1 * FPS)
        self.launch_stop = self.inv_time_start - round(0.3 * FPS)

        self.damage_sound2 = load_sound("retro_misc_02.ogg", 0.5)

        self.damage_sound3 = load_sound("retro_misc_03.ogg", 0.5)

        self.health_alarm = load_sound("sfx_alarm_loop6.wav", 0.3)
        self.heal_sound1 = load_sound("Menu2A.wav")
        self.heal_sound2 = load_sound("Item2A.wav")

        self.last_position = self.true_center[:]
        self.gold = 0
        self.max_gold = 2000
        k1, k2, k3 = KeyCount(), KeyCount(), KeyCount()
        self.region_keys = {"tundra": k1,
                            "mountains": k2,
                            "tower": k3}
        self.region = None

    def set_animations(self, sprite_list):
        # self.anim = {"s": [Player.IMAGES["s"]],
        #              "w": [Player.IMAGES["w"]],
        #              "a": [Player.IMAGES["a"]],
        #              "d": [Player.IMAGES["d"]]}
        self.anim = {"s": self.IMAGES["s"],
                     "w": self.IMAGES["w"],
                     "a": self.IMAGES["a"],
                     "d": self.IMAGES["d"]}

    def play_damage_noise(self):
        self.damage_sound.play()
        snd = random.choice([self.damage_sound2, self.damage_sound3])
        snd.play()

    def play_heal_noise(self):
        self.heal_sound2.play()
        self.heal_sound1.play()

    def reset_hitbox(self):
        """ Resets the hitbox to be in the proper position. """
        self.hitbox.center = (self.true_center[0] - 1, self.true_center[1] + 2)

    def set_direction(self, direction):
        self.direction = direction
        self.image = Player.IMAGES[direction]

    def set_move(self, direction):
        self.moving[direction] = True
        self.set_direction(direction)

    def get_potions(self):
        return self.potions

    def add_potion(self, amount=1):
        if isinstance(amount, int):
            self.potions += amount
            if self.potions > self.max_potions:
                self.potions = self.max_potions
            if self.potions < 0:
                self.potions = 0

    def get_item(self, item):
        if item.name == "heart":
            self.health += 4
            if self.health >= self.max_health:
                self.health = self.max_health
        if item.name == "heart_up":
            self.health += 4
            self.max_health += 4
        if item.name == "gold":
            self.add_gold(item.amount)
        if self.region is not None:
            if item.name == "key":
                self.region_keys[self.region].add_key()
            if item.name == "boss_key":
                self.region_keys[self.region].add_boss_key()

    def set_region(self, region_name):
        if region_name is not None:
            if region_name in self.ALL_REGIONS:
                self.region = str(region_name)
        else:
            self.region = None

    def move(self, target_object=None):
        if not self.invincible or self.inv_time < self.launch_stop:
            total_directions = 0
            for direction in self.moving.keys():
                if self.moving[direction]:
                    total_directions += 1
            if total_directions > 1:
                speed = 0.8 * self.speed  # Lowers speed if going diagonally
            else:
                speed = self.speed
            if self.moving["s"]:  # Down
                self.true_center[1] += speed
            if self.moving["w"]:  # Up
                self.true_center[1] -= speed
            if self.moving["d"]:  # Right
                self.true_center[0] += speed
            if self.moving["a"]:  # Left
                self.true_center[0] -= speed
        elif self.launch_stop <= self.inv_time:
            self.launch_away()
        self.reset_hitbox()

    def update(self):
        super(Player, self).update()
        if self.last_position == self.true_center:
            self.current_sprite = 0
        self.last_position = self.true_center[:]
        self.set_animations("test")
        if self.invincible and self.inv_time < self.launch_stop:
            self.draw_outline("white")
        self.play_health_warning()

    def play_health_warning(self):
        alarm_max = FPS * 3
        if self.health <= 4 or self.health <= round(self.max_health / 4):
            try:
                self.alarm_timer -= 1
                if self.alarm_timer <= -1:
                    self.alarm_timer = alarm_max
            except Exception:
                self.alarm_timer = alarm_max
            if self.alarm_timer == 0:
                self.health_alarm.play()

    def stop_move(self, direction):
        self.moving[direction] = False
        for direction in self.moving.keys():
            if self.moving[direction]:
                self.set_direction(direction)

    def check_room_trans(self, wall_dict):
        """
    Checks to see if the player collided with the room's transition walls.
    Returns boolean.
        """
        trans = {0: False, "down": False, "right": False,
                 "left": False, "up": False}  # trans is false? ;_;
        keys = wall_dict.keys()
        for key in keys:
            if wall_dict[key].colliderect(self.hitbox):
                trans[0] = True  # trans is true! :D
                trans[key] = True
        return trans

    def get_gold(self):
        return self.gold

    def add_gold(self, amount_add):
        if isinstance(amount_add, int) or isinstance(amount_add, float):
            self.gold += amount_add
            if self.gold >= self.max_gold:
                self.gold = self.max_gold
            if self.gold <= 0:
                self.gold = 0
