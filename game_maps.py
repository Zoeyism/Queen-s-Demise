from sprite_classes import *


class WorldObjects(AnimSprite):
    """ Base class for any object in the world that can be interacted with. """
    def __init__(self, position, sprite_list,
                 animation_speed, solid=False, animating=True):
        maxSpeed = 0
        super(WorldObjects, self).__init__(
            position, sprite_list, animation_speed, maxSpeed, animating)
        self.direction = "d"
        self.solid = solid
        self.damage_by = []
        self.puzzle_item = False

    def hit_by(self, other_object):
        pass

    def is_puzzle(self):
        return self.puzzle_item

    def update(self):
        self.update_sprite()

        if self.health <= 0:
            self.destruct()

    def destruct(self):
        pass


class TutorialImages(AnimSprite):
    def __init__(self, position, sprite_list):
        animation_speed = 0
        max_speed = 0
        animating = False
        solid = False
        super().__init__(position, sprite_list, animation_speed, max_speed, animating,
                         solid)

    def hit_by(self, other_object):
        pass


class TutorialWasd(TutorialImages):
    def __init__(self, position, key=None):
        sprite_list = ["wasd.png"]
        super().__init__(position, sprite_list)
        self.key = key


class TutorialSpace(TutorialImages):
    def __init__(self, position, key=None):
        sprite_list = ["space.png"]
        super().__init__(position, sprite_list)
        self.key = key


class LoadedObjects(AnimSprite):
    """
    Converts a rect into an undrawn AnimSprite instance for collision usage.
    """
    def __init__(self, rect):
        maxSpeed = 0
        animation_speed = 0
        animating = False
        solid = True

        # Only created to make sure the AnimSprite init goes through.
        spriteList = ["bush.png"]
        position = [0, 0]  # overwritten momentarily

        AnimSprite.__init__(self, position, spriteList, maxSpeed, animation_speed, animating, solid)
        self.rect = rect
        self.true_center = self.rect.center

    def hit_by(self, other_object):
        try:
            other_object.has_hit()
        except Exception:
            pass


class BreakableItems(WorldObjects):
    """
    Base class for any object that can be destroyed by the player.
    """
    def __init__(self, position, sprite_list, animation_speed, damage_types,
                 health=1, solid=False, death_anim=None):
        super(BreakableItems, self).__init__(
            position, sprite_list, animation_speed, solid)
        self.damage_by = self.damage_by + list(damage_types)

        self.health = health
        self.hit_sound = load_sound("sfx_sounds_impact3.wav", 0.2)
        self.death_anim = death_anim

    def hit_by(self, other_object):
        try:
            damage_check = other_object.damage_type
        except Exception:
            damage_check = "none"
        if damage_check in self.damage_by and not self.invincible:
            try:
                self.health -= other_object.damage
            except Exception:
                self.health -= 1
            try:
                self.hit_sound.play()
            except Exception:
                pass
            other_object.has_hit()
            self.set_invincible(True)

    def destruct(self):
        if self.death_anim is not None:
            if not isinstance(self.death_anim, bool):
                for group in self.groups()[:]:
                    group.add(self.death_anim(self.rect.center))
        self.kill()


class TemporaryAnimation(AnimSprite):
    def __init__(self, position, sprite_list, animation_speed,
                 max_speed, animating=True):
        super().__init__(position, sprite_list, animation_speed, max_speed,
                         animating=animating, repeat_animations=False)
        self.true_center = position

    def update(self):
        self.rect.center = self.true_center
        self.update_sprite()
        if not self.is_animating:
            for g in self.groups():
                self.remove(g)
            self.kill()


class TemporaryExplosion(TemporaryAnimation):
    """ Used during ending cutscene as visual explosions in same vein as
    those of enemies when they explode."""
    def __init__(self, position):
        sprite_list = ["explosion0.png", "explosion1.png", "explosion2.png",
                       "explosion3.png", "explosion4.png", "explosion5.png",
                       "explosion6.png", "explosion7.png", "explosion8.png"]
        animation_speed = 20 / FPS
        max_speed = 0
        animating = True

        super().__init__(position, sprite_list, animation_speed, max_speed, animating)

        self.solid = False
        self.explode_sound = load_sound("sfx_exp_short_hard5.wav", 0.2)
        self.explode_sound.play()
        self.direction = "d"


class PuzzleObjects(BreakableItems):
    all_sprite = 0
    enemy_sprite = 0

    def __init__(self, position, sprite_list, animation_speed, damage_types,
                 health=1, solid=False, death_anim=False, key=None):
        super().__init__(position, sprite_list, animation_speed, damage_types,
                         health, solid, death_anim)
        self.max_health = health
        self.puzzle_item = True
        self.one_hit = False
        self.affects = "none"
        self.key = key
        self.pass_through = []

    def draw_outline(self, color="red"):
        pass

    def update(self):
        super().update()
        if self.inv_time > 0:
            self.inv_time -= 1

        elif self.inv_time <= 0:
            if not self.one_hit:
                self.change_invincibility()

    def get_key(self):
        return self.key

    def destruct(self):
        pass

    def get_status(self):
        pass

    def hit_by(self, other_object):
        try:
            damage_check = other_object.damage_type
        except Exception:
            damage_check = "none"
        if damage_check in self.damage_by and not self.invincible:
            try:
                self.health -= other_object.damage
            except Exception:
                self.health -= 1
            try:
                self.hit_sound.play()
            except Exception:
                pass
            self.set_invincible(True)
        if damage_check not in self.pass_through and self.solid:
            other_object.has_hit()


class ArrowSwitch(PuzzleObjects):
    def __init__(self, position):
        sprite_list = ["gem_01c.png", "gem_01d.png"]
        animation_speed = 0
        damage_types = ["arrow", "sword", "bomb"]
        health = 1
        super().__init__(position, sprite_list, animation_speed,
                         damage_types, health)
        self.one_hit = False
        self.affects = "sprite"
        self.inv_time_start = (1.5 * FPS)

    def update(self):
        super().update()
        if self.health <= 0:
            self.health = self.max_health
            self.current_sprite += 1
            if self.current_sprite >= len(self.anim["d"]):
                self.current_sprite = 0
            PuzzleObjects.all_sprite = self.current_sprite
        self.update_image()
        if self.current_sprite != PuzzleObjects.all_sprite:
            self.current_sprite = PuzzleObjects.all_sprite

    def get_status(self):
        return self.current_sprite

    def hit_by(self, other_object):
        super().hit_by(other_object)
        try:
            if other_object.damage_type == "arrow":
                other_object.has_hit()
        except Exception:
            pass


class StatueRed(PuzzleObjects):
    def __init__(self, position):
        sprite_list = ["statue2.png", "statue1.png"]
        animation_speed = 0
        damage_types = ["none"]
        health = 500
        super().__init__(position, sprite_list, animation_speed, damage_types, health)

    def update(self):
        super().update()
        if self.current_sprite != self.all_sprite:
            self.current_sprite = self.all_sprite
        if self.current_sprite == 0:
            self.solid = False
        else:
            self.solid = True


class StatueBlue(PuzzleObjects):
    def __init__(self, position):
        sprite_list = ["statue0.png", "statue2.png"]
        animation_speed = 0
        damage_types = ["none"]
        health = 500
        super().__init__(position, sprite_list, animation_speed, damage_types, health)

    def update(self):
        super().update()
        if self.current_sprite != self.all_sprite:
            self.current_sprite = self.all_sprite
        if self.current_sprite == 1:
            self.solid = False
        else:
            self.solid = True


class LockBlock(PuzzleObjects):
    def __init__(self, position, key=None):
        sprite_list = ["lockblock.png"]
        animation_speed = 0
        damage_types = ["none"]
        health = 500
        super().__init__(position, sprite_list, animation_speed,
                         damage_types, health, key=key)
        self.one_hit = False
        self.affects = "key"
        self.solid = True
        self.damage_sound = load_sound("sfx_movement_dooropen4.wav", 0.8)
        self.pass_through = ["arrow", "fire"]

    def destruct(self):
        self.play_damage_noise()
        self.kill()


class RockBlock(PuzzleObjects):
    def __init__(self, position, key):
        sprite_list = ["rockblock.png"]
        animation_speed = 0
        damage_types = ["none"]
        health = 500
        super().__init__(position, sprite_list, animation_speed,
                         damage_types, health, key=key)
        self.one_hit = False
        self.affects = "none"
        self.solid = True
        self.damage_sound = load_sound("sfx_movement_dooropen4.wav", 0.8)
        self.pass_through = ["arrow", "fire"]

    def destruct(self):
        pass


class GlockBlock(PuzzleObjects):
    def __init__(self, position, key=None):
        sprite_list = ["glockblock.png"]
        animation_speed = 0
        damage_types = ["none"]
        health = 500
        super().__init__(position, sprite_list, animation_speed,
                         damage_types, health, key=key)
        self.one_hit = False
        self.affects = "boss_key"
        self.solid = True
        self.damage_sound = load_sound("sfx_movement_dooropen4.wav", 0.8)
        self.pass_through = ["arrow", "fire"]

    def destruct(self):
        self.play_damage_noise()
        self.kill()


class EnemyBlock(PuzzleObjects):

    def __init__(self, position, key=None):
        sprite_list = ["rockblock.png", "slash0.png"]
        animation_speed = 0
        damage_types = ["none"]
        health = 500
        super().__init__(position, sprite_list, animation_speed, damage_types,
                         health, solid=True, key=key)
        self.one_hit = False
        self.affects = "enemies"
        self.damage_sound = load_sound("sfx_movement_dooropen4.wav", 0.8)
        self.pass_through = ["arrow", "fire"]

    def set_sprite(self, sprite_num):
        if self.enemy_sprite != sprite_num:
            self.current_sprite = sprite_num
            self.enemy_sprite = sprite_num

    def update(self):
        super().update()
        self.current_sprite = self.enemy_sprite
        if self.current_sprite == 0:
            self.solid = True
        else:
            self.solid = False


class IceBlock(PuzzleObjects):
    def __init__(self, position):
        sprite_list = ["ice_block.png"]
        damage_types = ["fire"]
        health = 1
        solid = True
        animation_speed = 0
        super().__init__(position, sprite_list, animation_speed, damage_types,
                         health, solid, key=None)
        self.hit_sound = load_sound("sfx_sound_neutral11.wav")

    def destruct(self):
        BreakableItems.destruct(self)


class BombBlock(PuzzleObjects):
    def __init__(self, position):
        sprite_list = ["cracked_rock.png"]
        damage_types = ["bomb"]
        health = 1
        solid = True
        animation_speed = 0
        super().__init__(position, sprite_list, animation_speed, damage_types,
                         health, solid, key=None)
        self.hit_sound = load_sound("sfx_sounds_impact7.wav")

    def destruct(self):
        BreakableItems.destruct(self)


class BushShred(TemporaryAnimation):
    def __init__(self, position):
        sprite_list = ["bush_shred0.png", "bush_shred1.png", "bush_shred2.png", "bush_shred3.png"]
        animation_speed = 15/60
        max_speed = 0
        super().__init__(position, sprite_list, animation_speed, max_speed)


class GrassBush(BreakableItems):
    def __init__(self, position):
        spriteList = ["bush.png"]
        damageTypes = ["sword", "bomb"]
        health = 1
        solid = True
        animation_speed = 0
        BreakableItems.__init__(self, position, spriteList, animation_speed,
                                damageTypes, health, solid, BushShred)
        self.hit_sound = load_sound("rustle16.ogg", 0.6)


class NPCBase(WorldObjects):
    RANDOM_LINES = [None]

    def __init__(self, position, sprite_name, m_type="stationary"):
        all_lists = load_sprite_sheet_format(sprite_name)
        animation_speed = 8/60

        super().__init__(position, all_lists, animation_speed,
                         solid=True)
        self.repeat_animations = True
        self.max_speed = 1.5
        self.start_position = self.true_center[:]
        self.wander_time = 0
        self.type = m_type
        self.rand_timer = 0
        self.last_position = self.true_center[:]
        self.name = ""
        self.lines = [None]
        self.RANDOM = self.RANDOM_LINES[:]
        self.direction = random.choice("wasd")

    def set_animations(self, sprite_list):
        self.anim = {"w": sprite_list[0],
                     "d": sprite_list[1],
                     "s": sprite_list[2],
                     "a": sprite_list[3]}

    def wander(self):
        # Copied wander method from Enemy class
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

    def move(self, target_object=None):
        if self.type == "stationary":
            self.current_sprite = 0
            self.rand_timer -= 1
            if self.rand_timer <= -1:
                self.rand_timer = random.randint(1, 6) * FPS
            if self.rand_timer == 0:
                self.direction = random.choice("wasd")
        else:
            self.wander()
        self.update_position()
        if self.last_position == self.true_center:
            self.current_sprite = 0
        self.last_position = self.true_center[:]
        self.update_image()

    def use(self, rooms=None, player=None):
        npc_speech = DialogueText(screen, self.name, self.lines)
        npc_speech.loop()

    def randomize_lines(self):
        self.lines = random.choice(self.RANDOM)
        if not isinstance(self.lines, list) and self.lines is not None:
            self.lines = [self.lines]


class Mayor(NPCBase):
    INTRO_LINES = ["Ah, you must be the traveler that came",
                   "from the Forest, please, come in.",
                   None,
                   "I am Mayor Madeline. Welcome to our humble village,",
                   "and the last safe haven from her forces.",
                   None,
                   "... What do you mean \"Who's 'her'?\"",
                   "I mean the Demon Queen! Her Coven has ripped",
                   "the land to shreds!",
                   None,
                   "The Demon Queen has slaughtered countless",
                   "soldiers, civilians, children, and wildlife,",
                   "all in her search for power.",
                   None,
                   "We can barely hold the walls of our village,",
                   "most of my soldiers are wounded",
                   "or protecting the gates.",
                   None,
                   "I need someone like yourself to venture outside of",
                   "the village and fight back against the monsters",
                   "besieging us.",
                   None,
                   "If you're willing, I can have the soldiers let you",
                   "come and go as you please; my only request",
                   "is that you help us.",
                   None,
                   "There are two regions that are controlled by the",
                   "Queen's armies: the Mountains to the South, and",
                   "the Tundra to the North.",
                   None,
                   "My informants tell me that the Queen is hiding",
                   "something important in each of those areas.",
                   "Go there and recover whatever it is.",
                   None,
                   "And one more thing: you're going to need equipment.",
                   "Check the merchant shops in the South East",
                   "end of the village.",
                   None,
                   "Here's some gold for you to buy the Bow and arrows",
                   "you'll need. I can't spare more than that until",
                   "you prove you can handle it."]

    NOTHING_LINES = ["I'm sorry, but I have my hands full right now and I",
                     "don't have anything specific for you at the moment.",
                     "Stay safe out there, traveler."]

    FIRST_LINES = ["You're back? Good, what have you found?",
                   None,
                   "... That's a piece of the key to the Queen's Tower!",
                   "The other key piece must be in the region",
                   "that you haven't cleared yet...",
                   None,
                   "If you get that, then the Queen's Tower would be",
                   "open to you! Please, head out immediately!"]

    SECOND_LINES = ["You have both pieces! Perfect, I'll have the guards",
                    "let you through to the Queen's Tower.",
                    None,
                    "Best of luck fighting her; she didn't earn her title",
                    "without reason. Many of our best soldiers had",
                    "no chance against her.",
                    None,
                    "Even my wife, one of the fiercest fighters the land",
                    "had seen, only lasted long enough for our army to",
                    "retreat from the battle. So... Be careful."]

    def __init__(self, position):
        sprite_name = "coriander.png"
        super().__init__(position, sprite_name)
        self.name = "Mayor Madeline"
        self.lines = self.INTRO_LINES[:]
        self.ALL_LINES = {"intro": self.INTRO_LINES,
                          "nothing": self.NOTHING_LINES,
                          "first": self.FIRST_LINES,
                          "second": self.SECOND_LINES}

    def use(self, rooms=None, player=None):
        to_do = "nothing"

        if not rooms.dialogue_status[self.name]["intro"]:
            self.lines = self.ALL_LINES["intro"][:]
            rooms.dialogue_status[self.name]["intro"] = True
            to_do = "gold"

        elif (not rooms.dialogue_status[self.name]["first"] and
              player.region_keys["tower"].get_boss_keys() == 1):
            self.lines = self.ALL_LINES["first"][:]
            rooms.dialogue_status[self.name]["first"] = True

        elif (not rooms.dialogue_status[self.name]["second"] and
              player.region_keys["tower"].get_boss_keys() >= 2):
            self.lines = self.ALL_LINES["second"][:]
            rooms.dialogue_status[self.name]["second"] = True
            to_do = "remove_soldiers"

        else:
            self.lines = self.ALL_LINES["nothing"][:]
            to_do = "nothing"

        super().use()

        return to_do


class Shopkeeper(NPCBase):
    INTRO_LINES = ["This is the default shopkeeper intro."]
    QUESTION_LINES = ["This is the section where the shopkeeper lists",
                      "their wares or rambles on."]
    INVENTORY = [["Potion", "potion"], ["Potion Bottle", "potion_up"],
                 ["Cancel", "cancel"]]
    # ["Arrows", "arrow"], ["Bombs", "bomb"], ["Fire Refill", "flame"],
    # ["Heart Container", "heart_up"]]
    BUY_LINE_SPLIT = ["OK, so the ",
                      " is going to cost ",
                      " gold. Do you want it?"]
    BUY_SUCCESS = ["Excellent choice, you won't regret it!"]
    BUY_FAIL = ["Exc- hey, you don't have enough gold!"]
    CANCEL = ["OK, come back again!"]

    def __init__(self, position, sprite_name, character_name):
        super().__init__(position, sprite_name)
        self.name = character_name
        self.lines = self.INTRO_LINES[:]
        self.set_direction("s")

    def set_lines(self, lines_to_set):
        try:
            self.lines = lines_to_set[:]
        except Exception:
            pass

    def use(self, rooms=None, player=None):
        inventory = self.INVENTORY[:]
        for item in inventory[:]:
            if item[1] in rooms.QUANTITY[self.name].keys():
                if rooms.QUANTITY[self.name][item[1]] == 0:
                    inventory.remove(item)

        select_item = GameOptions(inventory)
        for i in range(0, len(inventory)):
            select_item.set_option(inventory[i], i+1)

        buy_options = [["Buy?", True], ["Cancel", False]]
        buy_question = GameOptions(["Buy?", True])
        for i in range(0, 2):
            buy_question.set_option(buy_options[i], i+1)

        status = {"intro": False, "which_item": False, "ask_to_buy": False,
                  "last_lines": False}
        status_order = ["intro", "which_item", "ask_to_buy", "last_lines"]
        current_status = 0

        item = {"key": "none", "info_name": "none", "cost": 0}
        continue_loop = True
        npc_speech = DialogueText(screen.copy(), self.name, self.lines)
        background = npc_speech.screen
        dialogue_screen = background.copy()
        to_do = None

        while continue_loop:
            if current_status >= len(status_order):
                current_status = len(status_order) - 1
            dialogue_screen.blit(background, (0, 0))
            npc_speech.draw(dialogue_screen)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    exit_game()

            if not npc_speech.waiting or npc_speech.cont_message:
                npc_speech.update(events)
            else:

                if status_order[current_status] == "intro":
                    npc_speech.update(events)
                    if not status["intro"] and not npc_speech.continue_loop:
                        status["intro"] = True
                        npc_speech = DialogueText(screen, self.name, self.QUESTION_LINES)
                        current_status += 1

                elif status_order[current_status] == "which_item":
                    answer = select_item.update(events)
                    if answer is not None and answer != "cancel":
                        npc_speech.waiting = False
                        for inv in inventory:
                            if inv[1] == answer:
                                item["key"] = inv[0]
                                item["info_name"] = inv[1]
                        line = [self.BUY_LINE_SPLIT[0] + str(item["key"]) + self.BUY_LINE_SPLIT[1]]
                        if item["info_name"] in rooms.COSTS.keys():
                            item["cost"] = rooms.COSTS[item["info_name"]]
                            line.append(str(item["cost"]))
                            line[-1] += self.BUY_LINE_SPLIT[2]
                        npc_speech = DialogueText(dialogue_screen, self.name, line)
                        status["which_item"] = True
                        current_status += 1
                        events = []

                    elif answer == "cancel":
                        npc_speech = DialogueText(dialogue_screen, self.name, self.CANCEL)
                        status["which_item"] = True
                        status["ask_to_buy"] = True
                        current_status = 3
                    select_item.draw(dialogue_screen)

                elif status_order[current_status] == "ask_to_buy":
                    answer = buy_question.update(events)
                    if answer is not None:
                        npc_speech.waiting = False

                        if answer:
                            if player.get_gold() >= item["cost"]:
                                if rooms.QUANTITY[self.name][item["info_name"]] != 0:
                                    player.add_gold(-item["cost"])
                                    npc_speech = DialogueText(screen, self.name, self.BUY_SUCCESS)
                                    to_do = item["info_name"]

                                    if rooms.QUANTITY[self.name][item["info_name"]] > 0:
                                        rooms.QUANTITY[self.name][item["info_name"]] -= 1
                                else:
                                    npc_speech = DialogueText(screen, self.name,
                                                              ["Oops, we're all out of that!"])
                            else:
                                npc_speech = DialogueText(screen, self.name, self.BUY_FAIL)

                        elif not answer:
                            npc_speech = DialogueText(screen, self.name, self.CANCEL)
                        status["ask_to_buy"] = True
                        current_status += 1
                    buy_question.draw(dialogue_screen)

            if status_order[current_status] == "last_lines":
                if not npc_speech.continue_loop:
                    continue_loop = False
                else:
                    npc_speech.update(events)
            flip_screen(dialogue_screen)
        return to_do


class BowNPC(Shopkeeper):
    INTRO_LINES = ["Welcome to Bow's Quiver, if you can't guess what",
                   "we sell, then good luck in life."]
    QUESTION_LINES = ["Want to buy something? You're gonna need a",
                      "bow and arrows if you want to get anywhere."]
    INVENTORY = [["Bow", "bow"], ["Arrows (5)", "arrow"], ["Bomb Refill (3)", "bomb"],
                 ["Fire Refill (3)", "flame"], ["Cancel", "cancel"]]

    def __init__(self, position):
        sprite_name = "moon walking.png"
        character_name = "Bow"
        super().__init__(position, sprite_name, character_name)


class Witch(Shopkeeper):
    INTRO_LINES = ["Hello there, welcome to Alicia's Potions!"]
    QUESTION_LINES = ["Want to buy something? All hand-made from",
                      "locally sourced ingredients."]
    INVENTORY = [["Potion", "potion"], ["Potion Bottle", "potion_up"],
                 ["Heart Container", "heart_up"], ["Cancel", "cancel"]]

    def __init__(self, position):
        sprite_name = "Mage-F-01 dark.png"
        super().__init__(position, sprite_name, "wander")
        self.name = "Alicia"


class Soldier(NPCBase):
    RANDOM_LINES = ["Don't cause any trouble.",
                    ["We guard the gate here to protect",
                     "the village from the Queen's forces."],
                    ["The Queen's monsters attack constantly,",
                     "and the gate is always a hotspot."],
                    ["It's a dangerous job, and there are",
                     "fewer guards every day..."],
                    ["If you need items, go to the merchants' shops.",
                     "They always have interesting finds."],
                    "Need something? I'm on lunch, sorry.",
                    ["I wish I had a bomb bag,",
                     "I could use one of those."]]

    def __init__(self, position):
        sprite_name = "soldier.png"
        super().__init__(position, sprite_name)
        self.name = "Soldier"

    def use(self, room=None, player=None):
        self.randomize_lines()
        super().use()


class OfficeSoldier(Soldier):
    RANDOM_LINES = ["This is the mayor's office, cause her no trouble.",
                    "The mayor is very busy, make it quick.",
                    ["Ah, so you're the traveler that people are",
                     "talking about. Stay safe out there."],
                    "The mayor has kept the village safe for many years."]


class OldLadyBase(NPCBase):
    RANDOM_LINES = ["Please, friend, spare a coin for a starving lady?",
                    "Can't move... Need food...",
                    ["This war has gone on for so long..."],
                    "My grandchild would be 24 if not for the war.",
                    "I barely survived fighting in that war..."]

    def __init__(self, position, sprite_name):
        super().__init__(position, sprite_name)
        self.name = "Old Lady"
        self.randomize_lines()

    def use(self, room=None, player=None):
        self.randomize_lines()
        super().use()


class OldLady1(OldLadyBase):
    def __init__(self, position):
        sprite_name = "Townfolk-Old-F-001 light.png"
        super().__init__(position, sprite_name)


class OldLady2(OldLadyBase):
    def __init__(self, position):
        sprite_name = "Townfolk-Old-F-001 dark.png"
        super().__init__(position, sprite_name)


class OldManBase(NPCBase):
    RANDOM_LINES = [["Please, friend, spare a coin for a starving man?"],
                    ["This war has gone on for so long..."]]

    def __init__(self, position, sprite_name):
        super().__init__(position, sprite_name)
        self.name = "Old Man"
        self.randomize_lines()

    def use(self, room=None, player=None):
        self.randomize_lines()
        super().use()


class OldMan1(OldManBase):
    def __init__(self, position):
        self.RANDOM = self.RANDOM_LINES[:]
        self.RANDOM.append(["I lost my husband early on in the war;",
                            "I miss him every day."])
        sprite_name = "Townfolk-Old-M-001 dark.png"
        super().__init__(position, sprite_name)


class OldMan2(OldManBase):
    def __init__(self, position):
        self.RANDOM = self.RANDOM_LINES[:]
        self.RANDOM.append(["My partner had been sick for a few days,",
                            "but they're recovering after I bought them",
                            "a potion. You might want to get some from a shop."])
        sprite_name = "Townfolk-Old-M-001 light.png"
        super().__init__(position, sprite_name)


class OldMan3(OldManBase):

    def __init__(self, position):
        self.RANDOM = self.RANDOM_LINES[:]
        self.RANDOM.append(["My wife can't fight anymore, but",
                            "she still teaches the new soldier recruits."])
        sprite_name = "Townfolk-Old-M-002 dark.png"
        super().__init__(position, sprite_name)


class OldMan4(OldManBase):
    def __init__(self, position):
        self.RANDOM = self.RANDOM_LINES[:]
        self.RANDOM.append(["Be careful outside of the village,",
                            "There's too many monsters to relax out there."])
        sprite_name = "Townfolk-Old-M-002 light.png"
        super().__init__(position, sprite_name)


class AllRooms(object):
    # Shop cost Constants
    COSTS = {"bow": 500, "potion": 50, "potion_up": 100,
             "arrow": 50, "flame": 100, "bomb": 100, "heart_up": 500}
    QUANTITY = {"Bow": {"bow": 1, "arrow": -1, "bomb": -1, "flame": -1, "cancel": -1},
                "Alicia": {"potion": -1, "potion_up": 2, "heart_up": 1, "cancel": -1}}
    INTRO_LINES = ["... You awaken in a forest, alone.",
                   "The outline of village walls to the Northeast",
                   "is barely visible through the trees.",
                   None,
                   "Without anywhere else to go,",
                   "you head towards the path."]
    VILLAGE_LINES = ["Wh- what the? Who are you?",
                     "I haven't seen anyone come out of that",
                     "forest in years. If you can survive that...",
                     None,
                     "Then you need to meet the mayor.",
                     "Directly East of here is the Mayor's Office.",
                     "She'll be expecting you."]

    QUEEN_LINES = ["Ah, so you are the traveler that my spies",
                   "have spoken of. You've done well to make",
                   "it this far.",
                   None,
                   "Unfortunately, this is where your story",
                   "ends. Best of luck in your next life."]

    # status is used for while loops in game sections
    status = {"pause_menu": False, "start_menu": True, "side_menu": False,
              "gameplay": False, "cutscene": False, "room_transition": False,
              "intro": True, "village_scene": True, "ending": False,
              "queen_dialogue": True}

    def __init__(self):
        self.extension = ".png"
        self.room_num = [3, 4]
        self.set_room_num()
        self.reset_room_info()

        self.QUANTITY = AllRooms.QUANTITY.copy()

        self.ALL_ITEMS = {
            3: {4: {0: [SwordUpgrade, 12, 14]}},
            4: {7: {0: [HeartContainer, 11.5, 5.5]},
                8: {0: [HeartContainer, 2.5, 2.5]}
                },
            6: {11: {0: [KeyItem, 4.5, 4], 1: [HeartContainer, 10, 6.5]}},
            7: {10: {0: [QueenKeyItem, 10.5, 10.5], 1: [HeartContainer, 9.5, 10.5]},
                11: {0: [KeyItem, 5, 11]},
                12: {0: [FlameUpgrade, 4, 15], 1: [KeyItem, 18.5, 3]
                     }
                },
            8: {4: {0: [QueenKeyItem, 10.5, 10.5], 1: [HeartContainer, 9.5, 10.5]},
                10: {0: [BossKeyItem, 18, 17.5]}},
            9: {4: {0: [KeyItem, 2, 3], 1: [BossKeyItem, 9.5, 12.5]},
                5: {0: [BombUpgrade, 3.5, 4.5]}},
            10: {4: {0: [HeartContainer, 15, 1.5]}},
            11: {5: {0: [KeyItem, 15.5, 3.5]},
                 9: {0: [KeyItem, 16.5, 4.5]}},
            12: {8: {0: [KeyItem, 12, 4]}},
            13: {8: {0: [KeyItem, 16.5, 4.5]}}
        }
        self.room_items = {}

        B = GrassBush  # Used for ease of creating
        self.ALL_OBJECTS = {
            3: {4: {1: [B, 11.5, 11.5], 2: [B, 12.5, 11.5], 3: [TutorialWasd, 7.5, 17.5],
                    4: [TutorialSpace, 12, 12.5]}},
            4: {7: {0: [BombBlock, 12.5, 11.5]},
                8: {0: [StatueRed, 7.5, 3.5], 1: [StatueRed, 7.5, 2.5],
                    2: [StatueBlue, 5.5, 3.5], 3: [StatueBlue, 5.5, 2.5],
                    4: [ArrowSwitch, 2.5, 3.5], 5: [ArrowSwitch, 16.5, 2.5]}},
            6: {7: {0: [Soldier, 4.5, 12], 1: [Soldier, 4.5, 7], 2: [OldLady1, 6, 4],
                    3: [OldLady2, 13, 7], 4: [OldMan2, 14, 12]},
                8: {0: [Soldier, 8.5, 6], 1: [Soldier, 11.5, 6], 4: [Soldier, 7.5, 16.5],
                    2: [Soldier, 3.5, 12], 3: [Soldier, 16.5, 12], 5: [Soldier, 12.5, 16.5]},
                9: {0: [ArrowSwitch, 11, 14.5], 4: [ArrowSwitch, 18, 9.5],
                    1: [StatueBlue, 4, 12.5], 2: [StatueBlue, 5, 12.5],
                    6: [StatueRed, 12, 9], 7: [StatueRed, 12, 10], 8: [StatueRed, 12, 11]},
                10: {0: [ArrowSwitch, 8.1, 13], 1: [StatueBlue, 5.5, 16], 2: [StatueBlue, 5.5, 17],
                     3: [StatueBlue, 5.5, 18], 4: [StatueRed, 10.5, 16], 5: [StatueRed, 10.5, 17],
                     6: [StatueRed, 10.5, 18], 7: [StatueRed, 17, 7], 8: [StatueRed, 18, 7],
                     9: [StatueBlue, 16, 14], 10: [StatueBlue, 17, 14], 11: [StatueBlue, 18, 14],
                     12: [RockBlock, 8, 15], 13: [RockBlock, 10.5, 12.5], 14: [RockBlock, 10.5, 13.5]},
                11: {0: [LockBlock, 13.5, 11.5]}
                },
            7: {8: {0: [Mayor, 10.5, 5], 1: [OfficeSoldier, 7, 13.5], 2: [OfficeSoldier, 13, 13.5],
                    3: [OfficeSoldier, 7, 17], 4: [OfficeSoldier, 13, 17]},
                7: {0: [OfficeSoldier, 7.5, 2.5], 1: [OfficeSoldier, 12.5, 2.5], 2: [OldMan3, 16, 6],
                    3: [OldMan4, 4, 7], 4: [OldLady2, 6, 15], 5: [OldMan1, 17, 13]},
                10: {0: [EnemyBlock, 0.5, 11.5], 1: [EnemyBlock, 0.5, 12.5], 2: [EnemyBlock, 0.5, 13.5],
                     3: [EnemyBlock, 19.5, 10.5], 4: [EnemyBlock, 19.5, 11.5]},
                11: {0: [ArrowSwitch, 13, 6], 1: [RockBlock, 11.5, 8.5], 2: [RockBlock, 11.5, 9.5],
                     3: [RockBlock, 13, 4.5], 4: [StatueBlue, 16, 14.5], 5: [StatueBlue, 17, 14.5],
                     6: [IceBlock, 13, 8.5], 7: [IceBlock, 13, 9.5],
                     9: [StatueRed, 7.5, 16.5], 10: [StatueRed, 7.5, 17.5], 13: [RockBlock, 13, 14.5],
                     11: [RockBlock, 18.5, 16.5], 12: [LockBlock, 18.5, 17.5]},
                12: {0: [IceBlock, 3, 11], 1: [IceBlock, 4, 11], 2: [IceBlock, 5, 11],
                     3: [IceBlock, 4, 5], 4: [IceBlock, 4, 6], 5: [IceBlock, 10, 14],
                     6: [IceBlock, 9, 14], 7: [LockBlock, 17, 19.2], 8: [RockBlock, 18, 19.2],
                     9: [RockBlock, 16, 6], 10: [StatueBlue, 13, 6], 11: [ArrowSwitch, 16, 3]}
                },
            8: {4: {0: [EnemyBlock, 8.5, 1.5], 1: [EnemyBlock, 9.5, 1.5], 2: [EnemyBlock, 10.5, 1.5],
                    3: [EnemyBlock, 11.5, 1.5], 4: [EnemyBlock, 19.5, 8.5], 5: [EnemyBlock, 19.5, 9.5],
                    6: [EnemyBlock, 19.5, 10.5], 7: [EnemyBlock, 19.5, 11.5]},
                5: {0: [ArrowSwitch, 14.5, 6.5], 1: [ArrowSwitch, 17, 11.5],
                    2: [StatueRed, 2, 9], 3: [StatueRed, 3, 9],
                    4: [StatueBlue, 14, 17.5], 5: [StatueBlue, 14, 18.5], 6: [StatueBlue, 14, 16.5]},
                6: {0: [Soldier, 7.5, 13.5], 1: [Soldier, 12.5, 13.5], 2: [Soldier, 16.5, 16.5],
                    3: [Soldier, 13.5, 9.5], 4: [Soldier, 6.5, 9.5], 5: [Soldier, 6.5, 6.5],
                    6: [Soldier, 13.5, 6.5], 7: [Soldier, 15.5, 4.5], 8: [Soldier, 3.5, 5.5]},
                7: {0: [Witch, 2.5, 5], 1: [BowNPC, 17.5, 5],
                    2: [Soldier, 8.5, 2], 3: [Soldier, 9.5, 2], 4: [Soldier, 10.5, 2],
                    5: [Soldier, 11.5, 2], 6: [OldLady2, 5.5, 16.5], 7: [OldMan3, 15.5, 13.5]},
                8: {0: [Soldier, 16.5, 7.5], 1: [Soldier, 16.5, 13.5], 2: [Soldier, 11.5, 7.5],
                    3: [Soldier, 5.5, 9.5], 4: [Soldier, 5.5, 13.5], 5: [Soldier, 8.5, 7.5]},
                10: {0: [GlockBlock, 1, 11], 1: [RockBlock, 6.5, 17], 2: [ArrowSwitch, 10.5, 17.5],
                     3: [RockBlock, 14.5, 17], 4: [RockBlock, 14.5, 18], 5: [RockBlock, 6.5, 18],
                     6: [StatueBlue, 13.5, 13], 7: [StatueBlue, 13.5, 14], 14: [StatueRed, 16, 15.5],
                     8: [ArrowSwitch, 17, 9.5], 9: [StatueBlue, 17, 10.5], 10: [RockBlock, 17, 11.5],
                     11: [StatueRed, 2, 15.5], 12: [StatueRed, 3, 15.5], 13: [StatueRed, 17, 15.5]}
                },
            9: {4: {0: [GlockBlock, 3, 13], 1: [LockBlock, 18.5, 4], 2: [RockBlock, 18.5, 2.5]},
                5: {0: [BombBlock, 6.5, 15.5], 1: [BombBlock, 6.5, 16.5], 2: [BombBlock, 6.5, 17.5],
                    3: [BombBlock, 8.2, 10], 4: [BombBlock, 9.8, 10]},
                8: {0: [Soldier, 8.5, 7.5], 1: [Soldier, 8.5, 13.5], 2: [Soldier, 3.5, 7.5],
                    3: [Soldier, 3.5, 13.5]}},
            10: {5: {0: [RockBlock, 10, 10.5], 1: [RockBlock, 11, 10.5], 2: [ArrowSwitch, 10.5, 12.5],
                     4: [StatueRed, 10, 8.5], 5: [StatueRed, 11, 8.5], 3: [ArrowSwitch, 18.2, 6.5],
                     6: [StatueRed, 16.5, 2.5], 7: [StatueRed, 16.5, 3.5], 8: [StatueBlue, 14, 6.5],
                     9: [StatueBlue, 15, 6.5], 10: [StatueBlue, 12.5, 2.5], 11: [StatueBlue, 12.5, 3.5]},
                 8: {0: [GlockBlock, 9.5, 10], 1: [GlockBlock, 13.5, 10]}},
            11: {4: {0: [EnemyBlock, 0.5, 16.5], 1: [EnemyBlock, 0.5, 17.5], 2: [EnemyBlock, 0.5, 18.5]},
                 5: {0: [BombBlock, 9, 13], 1: [BombBlock, 10, 13], 2: [BombBlock, 18, 15], 3: [BombBlock, 17, 15],
                     4: [BombBlock, 15, 11], 5: [BombBlock, 16, 11], 6: [BombBlock, 18, 7], 7: [BombBlock, 17, 7]},
                 8: {0: [RockBlock, 18.5, 8.5], 1: [RockBlock, 18.5, 11.5], 2: [LockBlock, 18.5, 10]},
                 9: {0: [EnemyBlock, 15.5, 9.5], 1: [EnemyBlock, 16.5, 9.5], 2: [EnemyBlock, 17.5, 9.5]}},
            12: {8: {3: [EnemyBlock, 14.5, 4], 0: [RockBlock, 18.5, 8.5], 1: [RockBlock, 18.5, 11.5],
                     2: [LockBlock, 18.5, 10]}},
            13: {8: {0: [ArrowSwitch, 3.2, 17.5], 1: [IceBlock, 3, 15.5], 2: [IceBlock, 4, 15.5],
                     3: [BombBlock, 3, 12.5], 4: [BombBlock, 4, 12.5], 5: [ArrowSwitch, 11.2, 4.5],
                     6: [StatueBlue, 5.5, 4], 7: [StatueBlue, 5.5, 5], 8: [StatueRed, 10, 6.5],
                     9: [StatueBlue, 10, 10.5], 10: [EnemyBlock, 15.5, 6.5], 11: [EnemyBlock, 16.5, 6.5],
                     12: [EnemyBlock, 17.5, 6.5], 13: [ArrowSwitch, 7.2, 11.5], 14: [LockBlock, 18.5, 10],
                     15: [RockBlock, 18.5, 8.5], 16: [RockBlock, 18.5, 11.5]}},
            14: {9: {0: [EnemyBlock, 12.5, 19.5], 1: [EnemyBlock, 13.5, 19.5], 2: [EnemyBlock, 14.5, 19.5],
                     3: [EnemyBlock, 0.5, 9], 4: [EnemyBlock, 0.5, 10], 5: [EnemyBlock, 0.5, 11]}}
        }
        self.room_objects = {}

        self.ALL_ENEMIES = {
            2: {5: [[Log, 3, 5], [Bee, 15, 4], [Slime, 4, 16]],
                6: [[Bee, 3, 3], [Slime, 4, 10], [Slime, 14, 7]]
                },
            3: {4: [[]],
                5: [[Bee, 18, 18], [Bee, 2, 2], [Bee, 19, 5]],
                6: [[Slime, 6, 6], [Slime, 8, 6]]
                },
            4: {5: [[Log, 5, 5], [Slime, 8, 8]],
                6: [[Bee, 8, 8], [Bee, 12, 8], [Bee, 8, 12], [Bee, 12, 12]],
                7: [[Slime, 6, 16], [Log, 12, 14]],
                8: [[Slime, 10, 8], [Bee, 15, 5]]
                },
            6: {9: [[Skeleton, 3, 7], [Skeleton, 8, 4]],
                10: [[Eyebat, 14, 10], [Eyebat, 2, 9], [Eyebat, 8, 7]],
                11: [[Eyebat, 4, 4], [Eyebat, 10, 13], [Skeleton, 3, 15],
                     [Skeleton, 2, 10], [Skeleton, 2, 9], [Slime, 2, 17]]},
            7: {10: [[EyebossHead, 5, 5]],
                12: [[Eyebat, 13, 15], [Skeleton, 17, 11], [Skeleton, 13, 3],
                     [Slime, 15, 12], [Eyebat, 13, 10]]},
            8: {4: [[EyebossHead, 3, 16]],
                5: [[Skeleton, 4, 13], [Fang, 9, 15]],
                10: [[Skeleton, 3, 4], [Eyebat, 3, 8], [Skeleton, 11, 4],
                     [Eyebat, 11, 5], [Skeleton, 4, 9]],
                11: [[Slime, 5, 13], [Slime, 3, 11], [Eyebat, 5, 6],
                     [Eyebat, 6, 4], [Eyebat, 9, 3], [Skeleton, 12, 3],
                     [Skeleton, 12, 4], [Skeleton, 17, 7], [Slime, 11, 15]]},
            9: {4: [[Skeleton, 12, 4], [Skeleton, 16, 7], [Slime, 11, 11],
                    [Log, 6, 3], [Eyebat, 15, 9], [Eyebat, 5, 17], [Eyebat, 8, 17]],
                5: [[Eyebat, 3.5, 7.5], [Skeleton, 8, 16], [Skeleton, 8, 9],
                    [Eyebat, 7, 4], [Skeleton, 13, 4], [Fang, 9, 5]]},
            10: {4: [[Bee, 6, 7], [Eyebat, 9, 8]],
                 5: [[Slime, 12, 17], [Bee, 8, 16]]},
            11: {4: [[Eyebat, 7, 7], [Fang, 4, 7], [Skeleton, 8, 9], [Slime, 10, 15],
                     [Eyebat, 17, 13], [Eyebat, 17, 8], [Fang, 16, 3], [Log, 5, 5],
                     [Eyebat, 13, 15], [Skeleton, 17, 11], [Skeleton, 13, 3], [Bee, 10, 10]],
                 5: [[Eyebat, 7, 7], [Fang, 4, 7], [Skeleton, 8, 9], [Slime, 10, 15],
                     [Eyebat, 17, 13], [Eyebat, 17, 8], [Fang, 16, 3]],
                 8: [[Skeleton, 12, 4.5], [Eyebat, 8, 7], [Slime, 14, 13]],
                 9: [[Slime, 4, 5], [Skeleton, 8, 7], [Log, 8, 5], [Eyebat, 12, 5], [Bee, 12, 7],
                     [Skeleton, 16, 14], [Skeleton, 14, 15]]},
            12: {8: [[Slime, 5, 5], [Skeleton, 8, 6], [Eyebat, 8, 12], [Eyebat, 4, 16],
                     [Bee, 6, 16], [Skeleton, 15, 15], [Skeleton, 14, 13], [Log, 16.5, 10.5]]},
            13: {8: [[Fang, 8, 12], [Skeleton, 10, 14], [Skeleton, 13, 15], [Skeleton, 14, 13],
                     [Log, 15.5, 15.5], [Log, 15.5, 14.5]],
                 10: [[DemonQueen, 10, 4.5]]},
            14: {9: [[EyebossHead, 5, 5]]}
            }

        self.dialogue_status = {"Mayor Madeline": {"intro": False,
                                                   "first": False,
                                                   "second": False,
                                                   "nothing": False},
                                }
        self.key_pieces = 0
        self.pieces_given = {"tundra": False,
                             "mountains": False}
        self.bosses_beaten = {"tundra": False,
                              "mountains": False}

    def set_status(self, new_status, boolean=True):
        print("TEST: Status: " + new_status + "; Changing to: " + str(boolean))
        success = False
        for s in self.status:
            if s == new_status:
                self.status[new_status] = boolean
                success = True
        if not success:
            self.status[new_status] = boolean

    def set_status_gameplay(self):
        self.set_status("gameplay", True)
        self.set_status("pause_menu", False)

    def set_status_start_menu(self):
        for sta in self.status.keys():
            self.set_status(sta, False)
        self.set_status("start_menu", True)

    def set_status_side_menu(self, boolean=False):
        self.set_status("side_menu", boolean)

    def get_status(self, status_call):
        try:
            return self.status[status_call]
        except Exception:
            return False

    def get_room_num(self):
        return self.room_num

    def reset_room_info(self):
        self.background = pygame.image.load(
            os.path.join("mapFiles", self.room_name+self.extension)).convert_alpha()
        self.coll_image = pygame.image.load(
            os.path.join("mapFiles", (self.room_name+"coll"+self.extension))).convert_alpha()
        try:
            self.top = pygame.image.load(
                os.path.join("mapFiles", (self.room_name+"top"+self.extension))).convert_alpha()
        except Exception:  # If no top image for the room, replaced with a transparent image
            fake_top = pygame.Surface(
                (self.background.get_size()), pygame.SRCALPHA)  # surface w/alpha
            fake_top.fill((255, 255, 255, 0))
            self.top = fake_top
        self.current_room = self.room_call()

    def set_room_num(self, x=0, y=0):
        self.room_num[0] += x
        self.room_num[1] += y
        self.room_name = "["+str(self.room_num[0])+","+str(self.room_num[1])+"]"

    def get_current_room(self):
        return self.current_room
    
    def room_call(self, room_num=None):
        if room_num is None:
            room_num = self.room_num
        try:
            target_room = {"number": room_num,
                           "objects": [None],
                           "floor": [None],
                           "background": self.background}
        except Exception:
            target_room = self.current_room[:]
        return target_room
    
    def get_background(self):
        return self.background

    def build_room_initial(self):
        room_dict = self.get_current_room()

        self.background = room_dict["background"]

    def redraw_room(self, base_screen):
        base_screen.blit(self.background, (0, 0))

        return base_screen

    def redraw_room_top(self, base_screen):
        base_screen.blit(self.top, (0, 0))
        return base_screen

    def get_room_coll(self):
        coll_mask = pygame.mask.from_surface(self.coll_image)
        masks = coll_mask.connected_components()
        rect_list = []
        for m in masks:
            rect_list += coll_mask.get_bounding_rects()
        return rect_list

    def get_room_items(self):
        """
                All items in each room are stored in a nested dictionary. It stores
                the name of the item's class, and the position it needs to spawn at.
                Original dictionary kept separate from player's items.
        """
        room_x, room_y = self.room_num
        try:
            items_to_add = self.room_items[room_x][room_y].copy()
        except KeyError:
            try:
                items_to_add = self.ALL_ITEMS[room_x][room_y]
            except KeyError:
                items_to_add = {}

            try:
                self.room_items[room_x][room_y] = items_to_add.copy()
            except KeyError:
                try:
                    self.room_items[room_x].setdefault(room_y, items_to_add.copy())
                except KeyError:
                    self.room_items.setdefault(room_x, {room_y: items_to_add.copy()})

        return items_to_add

    def remove_item(self, item_obj):
        try:
            self.room_items[self.room_num[0]][self.room_num[1]].pop(item_obj.get_key())
        except Exception:
            # print (e)
            pass

    def remove_object(self, item_obj):
        try:
            self.room_objects[self.room_num[0]][self.room_num[1]].pop(item_obj.get_key())
        except Exception:
            # print(e)
            pass

    def get_room_objects(self):
        """
        All objects (and NPCs) in each room are stored in a nested dictionary. It stores
        the name of the object's class, and the position it needs to spawn at.
        They respawn, unchanged, each time the room is loaded.
        """
        room_x, room_y = self.room_num
        try:
            items_to_add = self.room_objects[room_x][room_y].copy()
        except KeyError:
            try:
                items_to_add = self.ALL_OBJECTS[room_x][room_y]
            except KeyError:
                items_to_add = {}

            try:
                self.room_objects[room_x][room_y] = items_to_add.copy()
            except KeyError:
                try:
                    self.room_objects[room_x].setdefault(room_y, items_to_add.copy())
                except KeyError:
                    self.room_objects.setdefault(room_x, {room_y: items_to_add.copy()})
        return items_to_add

    def get_room_enemies(self):
        """
        All enemies are stored in a nested dictionary; it stores the
        name of the enemy's class and the enemy's x and y tile positions.
        """
        try:
            enemiesToAdd = self.ALL_ENEMIES[self.room_num[0]][self.room_num[1]]
        except Exception:
            enemiesToAdd = [[]]
            # print(e)
        return enemiesToAdd


def room_walls(base_screen):
    """
    Takes the base_screen that you're walking around in, then creates 4 rects
    at each end of the screen of thickness 2. Returns them in a list.
    These rects are used to detect when to transition from room to room.
    """
    scr_x, scr_y = base_screen.get_size()
    room_walls_dict = dict()
    room_walls_dict["left"] = pygame.Rect(0, 0, 2, scr_y)
    room_walls_dict["up"] = pygame.Rect(0, 0, scr_x, 2)
    room_walls_dict["down"] = pygame.Rect(0, scr_y - 2, scr_x, 2)
    room_walls_dict["right"] = pygame.Rect(scr_x - 2, 0, 2, scr_y)
    return room_walls_dict


if __name__ == "__main__":
    print("Yeah, don't run this directly. Run the game.")
