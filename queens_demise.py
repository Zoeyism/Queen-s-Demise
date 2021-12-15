import pygame
import sys
from pygame.locals import *
from pygame import mixer
import os
import random
import math

# Some assets are my own design, others are from
#   kenney.nl, a free asset website, and
#   opengameart.org, another free asset site.

from sprite_classes import *
from game_maps import *
from extra_functions import *

rooms = AllRooms()

def collision_check(sprite, coll_rects, rooms, walls, is_player=False, player=None):
    if is_player:
        old_center = sprite.hitbox.center[:]
    else:
        old_center = sprite.rect.center[:]
    try:
        old_true_center = sprite.true_center[:]
    except Exception as e:
        # print(e)
        old_true_center = old_center[:]
    if is_player:
        sprite.move()
    elif player is not None:
        sprite.move(player)

    side_coll = False
    vert_coll = False
    general_coll = False

    # CHECKING ROOM TRANSITION COLLISION
    if is_player:
        transition_dict = sprite.check_room_trans(walls)
        if transition_dict[0]:
            general_coll = True
            if transition_dict["up"]:
                rooms.set_room_num(y=1)
                sprite.true_center[1] = SCREEN_HEIGHT - round(0.5 * sprite.rect.height)
            elif transition_dict["down"]:
                rooms.set_room_num(y=-1)
                sprite.true_center[1] = round(0.5 * sprite.rect.height)
            elif transition_dict["left"]:
                rooms.set_room_num(x=-1)
                sprite.true_center[0] = SCREEN_WIDTH - round(0.5 * sprite.rect.width)
            elif transition_dict["right"]:
                rooms.set_room_num(x=1)
                sprite.true_center[0] = round(0.5 * sprite.rect.width)
            sprite.reset_hitbox()

            rooms.set_status("room_transition")
            return

    for coll_obj in coll_rects:
        if not coll_obj.solid:
            continue
        try:
            sprite.reset_hitbox()
            sprite_rect = sprite.hitbox
        except Exception as e:
            sprite_rect = sprite.rect
            # print(e)
        if not sprite.fly and sprite_rect.colliderect(coll_obj.rect):
            COLL_TOLERANCE = 10
            general_coll = True

            if abs(sprite_rect.top - coll_obj.rect.bottom) < COLL_TOLERANCE:
                if sprite_rect.centery < old_center[1]:  # Moving up
                    vert_coll = True
                    general_coll = False
            if abs(sprite_rect.bottom - coll_obj.rect.top) < COLL_TOLERANCE:
                if sprite_rect.centery > old_center[1]:  # Moving down
                    vert_coll = True
                    general_coll = False

            if abs(sprite_rect.left - coll_obj.rect.right) < COLL_TOLERANCE:
                if sprite_rect.centerx < old_center[0]:  # Moving left
                    side_coll = True
                    general_coll = False
            if abs(sprite_rect.right - coll_obj.rect.left) < COLL_TOLERANCE:
                if sprite_rect.centerx > old_center[0]:  # Moving right
                    side_coll = True
                    general_coll = False

    if side_coll or vert_coll:
        try:
            if sprite.is_boss:
                sprite.has_hit()
        except:
            pass
        if side_coll:
            sprite.rect.centerx = old_center[0]
            sprite.true_center[0] = old_true_center[0]
        if vert_coll:
            sprite.rect.centery = old_center[1]
            sprite.true_center[1] = old_true_center[1]

    if is_player:
        sprite.reset_hitbox()


class Heart(pygame.sprite.Sprite):
    """ Player's health display. Each instance is one heart. """
    total_hearts = 0

    def reset():
        Heart.total_hearts = 0

    def __init__(self, player_obj):
        super().__init__()
        self.heart_images = load_animation(("hp0.png", "hp1.png", "hp2.png",
                                           "hp3.png", "hp4.png"))
        self.image = self.heart_images[4]
        Heart.total_hearts += 1
        self.which_heart = Heart.total_hearts
        self.rect = self.image.get_rect()
        self_width, self_height = self.rect.size
        if self.total_hearts <= 5:
            self.rect.center = (
                (round(self_width / 2) + ((1 + self_width) * self.which_heart)),  # x
                round(self_height * 1.7))  # y
        elif self.total_hearts > 5:
            self.rect.center = (
                (round(self_width / 2) + ((1 + self_width) * (self.which_heart - 5))),
                round(self_height * 1.7 + self_height + 1)
            )

        self.player = player_obj

    def update(self):
        health = int(self.player.health - (4 * (self.which_heart - 1)))
        if health >= 4:
            health = 4
        elif health <= 0:
            health = 0
        self.image = self.heart_images[health]
        super().update()


class UIText(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            self.font = pygame.font.Font(
                os.path.join("Fonts", "Kenney Mini Square.ttf"), 10)
        except:
            self.font = pygame.font.SysFont(
                "timesnewroman", 10)
        self.plate_image = load_image("green_pressed1.png")
        self.text_image = self.font.render("Health", True, get_color("black"))
        size = self.text_image.get_size()
        self.image = pygame.transform.scale(self.plate_image.copy(), (size[0] + 4, size[1] - 4))
        self.rect = self.image.get_rect()
        textRect = self.text_image.get_rect()
        textRect.center = self.rect.center
        self.image.blit(self.text_image, textRect)

        self.rect.topleft = tile_pos(0.5, 0)


class UseRect(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.small = tile_size(0.25)
        self.large = tile_size(2)

        self.rect = pygame.Rect((0, 0), (self.small, self.large))
        self.direction = self.player.direction
        self.active = False
        self.image = load_image("slash0.png")

    def use_active(self):
        self.active = True
        self.update_position()

    def is_active(self):
        if self.active:
            boolean = True
        else:
            boolean = False
        return boolean

    def update_position(self):
        self.direction = self.player.direction
        if self.direction in "ad":
            self.rect.size = self.large, self.small
            if self.direction == "a":
                self.rect.right = self.player.hitbox.left
            if self.direction == "d":
                self.rect.left = self.player.hitbox.right
            self.rect.centery = self.player.hitbox.centery
        if self.direction in "ws":
            self.rect.size = self.small, self.large
            if self.direction == "w":
                self.rect.bottom = self.player.hitbox.top
            if self.direction == "s":
                self.rect.top = self.player.hitbox.bottom
            self.rect.centerx = self.player.hitbox.centerx

    def update(self):
        self.active = False


def pause_menu(rooms, base_screen):
    set_music(MENU_MUSIC[0], MENU_MUSIC[1])
    background = base_screen.copy()
    pause_screen = base_screen.copy()
    clock = pygame.time.Clock()

    # Title Settings
    menuTitle = GameMenu(["Paused"])

    menuTitle.center_at(tile_size(6), tile_size(2))
    menuTitle.set_font(pygame.font.Font(
        os.path.join("Fonts", "Kenney Mini Square.ttf"), 24))
    menuTitle.set_back_image()
    menuTitle.set_highlight(get_color("purple"))

    # Menu Settings
    menuButtons = GameMenu(["Continue", rooms.set_status_gameplay], ["Quit", exit_game])
    menuButtons.set_font(pygame.font.Font(
        os.path.join("Fonts", "Kenney Mini Square.ttf"), 16))
    menuButtons.center_at(tile_size(10), tile_size(7))
    menuButtons.set_back_image()
    menuButtons.set_color(get_color("black"))
    menuButtons.set_highlight(get_color("green"))

    rooms.set_status("pause_menu")

    menu_sound = load_sound("sfx_sounds_pause7_in.wav", 0.3)
    menu_sound.play()

    while rooms.get_status("pause_menu"):
        pause_screen.blit(background, (0, 0))
        events = pygame.event.get()

        menuTitle.draw(pause_screen)

        menuButtons.update(events)

        menuButtons.draw(pause_screen)

        flip_screen(pause_screen)
    set_music(GAME_MUSIC[0], GAME_MUSIC[1])


def controls_menu():
    # Setting up title for menu
    title = GameMenu(["Controls"])
    title.set_font(pygame.font.Font(os.path.join("Fonts", "Kenney Mini Square.ttf"), 16))
    title.set_back_image()
    title.center_at(tile_size(10), tile_size(2))
    title.set_color(get_color("purple"))
    title.set_highlight(get_color("purple"))

    control_display = GameMenu(["Movement          W A S D"],
                               ["Sword Attack       Space Bar"],
                               ["Shoot Bow           J or B"],
                               ["Drop Bomb          K"],
                               ["Throw Fireball     L or F"],
                               ["Use Potion           Q"],
                               ["Use/Activate        E"],
                               ["Pause                  P"],
                               [""],
                               ["During dialogue:"],
                               ["    Space             Skip through message"],
                               ["    E/Enter          Next message/exit"])
    control_display.set_back_image()
    control_display.set_font(pygame.font.SysFont("timesnewroman", 10))
    control_display.center_at(tile_size(10), tile_size(4))
    control_display.set_highlight(get_color("black"))

    menu_options = GameMenu(["Back  ", rooms.set_status_side_menu])
    menu_options.set_back_image()
    menu_options.center_at(tile_size(4), tile_size(16))

    menu_back1 = pygame.image.load(os.path.join("mapFiles", "[7,7].png")).convert()
    menu_back2 = pygame.image.load(os.path.join("mapFiles", "[7,7]top.png")).convert_alpha()

    rooms.set_status("side_menu", True)

    while rooms.get_status("side_menu"):
        screen.blit(menu_back1, (0, 0))
        screen.blit(menu_back2, (0, 0))

        menu_options.update(pygame.event.get())
        menu_options.draw(screen)

        title.draw(screen)

        control_display.draw(screen)

        flip_screen()


def credits_menu():
    title = GameMenu(["Credits"])
    title.set_font(pygame.font.Font(os.path.join("Fonts", "Kenney Mini Square.ttf"), 16))
    title.set_back_image()
    title.center_at(tile_size(10), tile_size(2))
    title.set_color(get_color("purple"))
    title.set_highlight(get_color("purple"))
    credits_lines = [[["                 Developed by Zoeyism            "],
                      ["Most art assets, all sound assets from"],
                      ["several free game asset websites."],
                      [""],
                      ["Kenney.nl - Many sound assets, fonts, several sprites"],
                      ["Special thanks to OpenGameArt.org users: "],
                      ["  VWolfdog - Harp Music"],
                      ["  Juhani Junkala/Subspace Audio - Retro Game Music Pack/SFX"],
                      ["  ArMM1998 - Sprites (Overworld tiles, Log enemy)"],
                      ["  Bonsaiheldin - Slime sprites"],
                      ["  Buch - Numerous Tilesets (THANK YOU)"],
                      ["  Chayed - Tilesets"],
                      ["  Deva - Sound effects"],
                      ["  diamonddmgirl and Cabbit - Character Sprites (TY!)"],
                      ["  diarandor - sprites"],
                      [""],
                      [" Full attributions and links within 'Attributions.txt' "]],
                     [["  helpcomputer - explosion sprites"],
                      ["  hilau - tilesets"],
                      ["  kyrise - item/equipment sprites"],
                      ["  Luke.RUSTLTD - Explosion SFX"],
                      ["  LUNARSIGNALS - Sprites"],
                      ["  Michel Baradari - Monster SFX"],
                      ["  MoikMellah - Statue Sprites"],
                      ["  phoenix1291 - SFX"],
                      ["  qubodup - SFX"],
                      ["  Redshrike - Tileset + Sprites"],
                      ["  rrcaseyr - Sprite"],
                      ["  rubberduck - SFX"],
                      ["  Skoam - Eyeboss Sprites"],
                      ["  ViRiX - SFX"],
                      [""],
                      [""],
                      [" Full attributions and links within 'Attributions.txt' "]]]

    credits_display = GameMenu([""])
    credits_display.set_options(credits_lines[0])

    credits_display.set_highlight(get_color("black"))
    credits_display.set_pos(tile_size(3), tile_size(4))
    credits_display.set_back_image()
    credits_display.set_font(pygame.font.SysFont("timesnewroman", 10))

    menu_options = GameOptions(["Page 1", 0])
    choices = [["Page 1", 0], ["Page 2", 1], ["Back  ", 2]]
    for i in range(3):
        menu_options.set_option(choices[i], i+1)
    menu_options.center_at(tile_size(16), tile_size(17.5))

    menu_back1 = pygame.image.load(os.path.join("mapFiles", "[7,8].png")).convert()
    menu_back2 = pygame.image.load(os.path.join("mapFiles", "[7,8]top.png")).convert_alpha()

    rooms.set_status("side_menu", True)

    while rooms.get_status("side_menu"):
        screen.blit(menu_back1, (0, 0))
        screen.blit(menu_back2, (0, 0))

        decision = menu_options.update(pygame.event.get())
        if decision is not None:
            if decision == 2:
                rooms.set_status_side_menu()
            else:
                try:
                    credits_display.set_options(credits_lines[decision])
                except:
                    pass

        menu_options.draw(screen)

        title.draw(screen)

        credits_display.draw(screen)

        flip_screen()

def gameplay():
    """
    Main gameplay loop. Sets up all instances used in gameplay, almost
    everything happens here.
    """
    rooms.set_status("gameplay")
    rooms.set_status("room_transition")

    set_music(GAME_MUSIC[0], GAME_MUSIC[1])
    # Setting up player classes, including equipment
    player = Player()
    sword = Sword(player)
    bow = Bow(player)
    bomb_bag = BombBag(player)
    glove = FlameGlove(player)

    p_use = UseRect(player)  # used as a rect to activate usable objects

    # Creating Groups
    # Player group is all player equipment and the player
    player_group = pygame.sprite.LayeredUpdates()

    # equipment group is all player equipment
    equipment_group = pygame.sprite.LayeredUpdates()
    item_group = pygame.sprite.LayeredUpdates()
    object_group = pygame.sprite.LayeredUpdates()
    ui_group = pygame.sprite.LayeredUpdates()

    # enemy group is... self-explanatory, hopefully
    enemy_group = pygame.sprite.LayeredUpdates()

    # Death group is used to remove enemies from screen after HP goes <= 0.
    # Forces dead enemies to launch away for a brief time while exploding,
    #   and then .kill() the instance when appropriate
    death_group = pygame.sprite.LayeredUpdates()

    # Projectiles separated by team
    enemy_projectiles = pygame.sprite.LayeredUpdates()
    player_projectiles = pygame.sprite.LayeredUpdates()

    player_group.add(player, sword, bow, bomb_bag, glove)
    equipment_group.add(sword, bow, bomb_bag, glove)

    # Setting up instances for UI
    health_text = UIText()

    arrow_count = UIIcon("arrow_icon.png", tile_pos(4.5, 0), bow.get_ammo)
    bomb_count = UIIcon("bomb0.png", tile_pos(5.6, 0), bomb_bag.get_ammo)
    flame_count = UIIcon("explosion2.png", tile_pos(6.7, 0), glove.get_ammo)
    gold_count = UIIcon("shield_01b.png", tile_pos(18.5, 0), player.get_gold)
    potion_count = UIIcon("potion_02a.png", tile_pos(17, 0), player.get_potions)

    ui_group.add(health_text, gold_count, potion_count)
    for i in range(3):
        ui_group.add(Heart(player))

    walls = {}
    coll_rects = pygame.sprite.LayeredUpdates()
    ending_timer = -1

    # Used during testing of game and as dev menu
    testing = False
    cheat_allowed = True
    ui_added = False
    testing_options = [["Tundra", [6, 9]],
                       ["Mountains", [9, 5]],
                       ["Boss Dungeon", [11, 8]],
                       ["Final Bosses", [14, 9]],
                       ["Cancel", "cancel"]]
    testing_room = None
    test_choices = GameOptions(["Mountains", "blah"])
    for i in range(len(testing_options)):
        test_choices.set_option(testing_options[i], i + 1)

    death_scene = DeathCutscene(player, ui_group)
    while rooms.get_status("gameplay"):
        if ending_timer > 0:
            ending_timer -= 1

        # Adds heart to UI if max_health increases
        if Heart.total_hearts * 4 < player.max_health:
            ui_group.add(Heart(player))

        if player.health <= 0:
            player.health = 0
            for dir in "wasd":
                player.stop_move(dir)
            rooms.set_status("cutscene", True)
            death_scene.loop(rooms)

        # Only activates when cheat_allowed
        if testing:
            background = screen.copy()
        while testing:
            events = pygame.event.get()
            testing_room = test_choices.update(events)

            if testing_room is not None and "cancel" not in testing_room:
                rooms.set_status("room_transition")
                if isinstance(testing_room, list) and len(testing_room) == 2:
                    rooms.room_num = testing_room
                    rooms.set_room_num()
                    bow.equip_item()
                    bomb_bag.equip_item()
                    sword.equip_item()
                    glove.equip_item()

                    if not ui_added:
                        ui_group.add(arrow_count, bomb_count, flame_count)
                        ui_added = False

                    if testing_room in [[11, 8], [14, 9]]:
                        player.set_region("tower")
                    elif testing_room in [[6, 9]]:
                        player.set_region("tundra")
                    elif testing_room in [[9, 5]]:
                        player.set_region("mountains")
                    for ui in ui_group:
                        if ui.__class__.__name__ == "KeyCount":
                            ui_group.remove(ui)
                    if player.region in player.region_keys.keys():
                        ui_group.add(player.region_keys[player.region])
                    else:
                        print("Error: Region =", player.region)
                    for i in range(2):
                        player.region_keys[player.region].add_boss_key()

                    player.add_gold(2000)
                    player.max_health = 40
                    player.health = player.max_health
                testing = False
                testing_room = None
            elif testing_room is not None and testing_room == "cancel":
                testing = False
                testing_room = None

            screen.blit(background, (0, 0))
            test_choices.draw(screen)
            flip_screen(screen)

        # Transitions rooms
        if rooms.get_status("room_transition"):

            # Clear out groups for next room
            enemy_group.empty()
            item_group.empty()
            object_group.empty()
            coll_rects.empty()
            player_projectiles.empty()
            enemy_projectiles.empty()

            # removes key display based on room change
            room_num = rooms.get_room_num()
            if room_num in [[6, 8], [8, 6], [9, 8]]:
                player.set_region(None)
                for ui in ui_group:
                    if ui.__class__.__name__ == "KeyCount":
                        # Removes all KeyCount items from
                        # ui_group when changing regions
                        ui_group.remove(ui)

            elif room_num == [6, 9]:
                # Adds specific keycount for tundra region
                ui_group.add(player.region_keys["tundra"])
                player.set_region("tundra")

            elif room_num == [8, 5]:
                ui_group.add(player.region_keys["mountains"])
                player.set_region("mountains")

            elif room_num == [10, 8]:
                ui_group.add(player.region_keys["tower"])
                player.set_region("tower")


            rooms.reset_room_info()
            rooms.build_room_initial()

            walls = room_walls(screen)
            for coll in rooms.get_room_coll():
                coll_rects.add(LoadedObjects(coll))

            skip_enemies = False
            skip_items = False
            if room_num in [[7, 10], [8, 4]]:
                if rooms.bosses_beaten[player.region]:
                    skip_enemies = True
                skip_items = True

            if not skip_enemies:
                enemies = rooms.get_room_enemies()
                for enemy in enemies:
                    try:
                        enemy_group.add(enemy[0](tile_pos(enemy[1], enemy[2])))
                    except Exception as e:
                        # print(e)
                        pass
            room_objects = rooms.get_room_objects()
            for key in room_objects.keys():
                try:
                    obj = room_objects[key]
                    try:
                        object_group.add(obj[0](tile_pos(obj[1], obj[2]), key))
                    except Exception as e2:
                        # print(e2)
                        object_group.add(obj[0](tile_pos(obj[1], obj[2])))
                except Exception as e:
                    # print(e)
                    pass
            for obj in object_group:
                coll_rects.add(obj)

            if not skip_items:
                items = rooms.get_room_items()
                for key in items.keys():
                    try:
                        item = items[key]
                        item_group.add(item[0]([item[1], item[2]], key))
                    except Exception as e:
                        # print(e)
                        pass


            rooms.set_status("room_transition", False)

        ################# CHECKING PLAYER INPUT ##################################
        any_left = False
        for enemy in enemy_group:
            any_left = True
            break

        if room_num in [[7, 10], [8, 4]]:
            if not any_left:
                rooms.bosses_beaten[player.region] = True
                if not rooms.pieces_given[player.region] and rooms.bosses_beaten[player.region]:
                    items = rooms.get_room_items()
                    #no_items = True
                    for key in items.keys():
                        no_items = False
                        allowed = {0: True,
                                   1: True}
                        for i in item_group:
                            if i.key == 0:
                                allowed[0] = False
                            if i.key == 1:
                                allowed[1] = False
                        if key in allowed.keys() and allowed[key]:
                            try:
                                item = items[key]
                                item_group.add(item[0]([item[1], item[2]], key))
                            except Exception as e:
                                # print(e)
                                pass
                    #if no_items:
                        #rooms.pieces_given["tundra"] = True

        if not pygame.display.get_active():
            # Pauses game if screen is minimized
            rooms.set_status("pause_menu")
            pause_menu(rooms, screen)

        movement_allowed = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()

            for equip in equipment_group:
                if equip.is_using():
                    movement_allowed = False

            if rooms.get_status("cutscene"):
                movement_allowed = False
                for letter in "wasd":
                    player.stop_move(letter)

            if event.type == pygame.KEYDOWN and movement_allowed:
                if event.key == K_w:  # UP
                    player.set_move("w")
                if event.key == K_s:  # DOWN
                    player.set_move("s")
                if event.key == K_a:  # LEFT
                    player.set_move("a")
                if event.key == K_d:  # RIGHT
                    player.set_move("d")
                for equip in equipment_group:
                    if event.key in equip.use_key and not equip.is_pressed:  # use equipment
                        equip.animate()
                        equip.start_use()

            if event.type == pygame.KEYUP:
                if event.key == K_a:
                    player.stop_move("a")
                if event.key == K_w:
                    player.stop_move("w")
                if event.key == K_s:
                    player.stop_move("s")
                if event.key == K_d:
                    player.stop_move("d")
                if event.key == K_p:
                    rooms.set_status("pause_menu")
                    pause_menu(rooms, screen)
                if event.key == K_e:
                    p_use.use_active()
                if event.key == K_q:
                    if player.get_potions() > 0 and player.health != player.max_health:
                        player.add_potion(-1)
                        player.health = player.max_health
                        player.play_heal_noise()

                for equip in equipment_group:
                    if event.key in equip.use_key:
                        equip.end_use()

                if cheat_allowed and event.key == K_BACKSPACE:
                    testing = True


        ################# CHECKING AND HANDLING COLLISIONS ##################################

        if movement_allowed:
            collision_check(player, coll_rects, rooms, walls, True)

        if bow.is_used():
            player_projectiles.add(Arrow(bow))

        if bomb_bag.is_used():
            player_projectiles.add(BombPlaced(bomb_bag))

        if glove.is_used():
            player_projectiles.add(FlameThrow(glove))

        for proj in player_projectiles:
            proj.move()
            for obj in object_group:
                if did_collide(obj.rect, proj.rect):
                    obj.hit_by(proj)
            for coll in coll_rects:
                if did_collide(coll.rect, proj.rect):
                    if coll.solid or coll.damage != 0:
                        coll.hit_by(proj)
            if proj.__class__.__name__ == "BombPlaced":
                if sword.is_using() and did_collide(sword.rect, proj.rect):
                    proj.bomb_timer = 1

        for proj in enemy_projectiles:
            proj.move()
            if did_collide(player.hitbox, proj.rect):
                player.hit_by(proj)

        any_left = False

        for enemy in enemy_group:
            any_left = True
            if not enemy.get_invincible():
                if sword.is_using():
                    if did_collide(sword.rect, enemy.rect):
                        enemy.hit_by(sword)
                for proj in player_projectiles:
                    if did_collide(proj.rect, enemy.rect):
                        enemy.hit_by(proj)
                if enemy.__class__.__name__ == "EnergyBlast":
                    for maybe_boss in enemy_group:
                        if maybe_boss.is_boss and did_collide(maybe_boss.rect, enemy.rect):
                            enemy.hit_by(maybe_boss)

            if enemy.health <= 0:
                enemy_group.remove(enemy)
                death_group.add(enemy)
                enemy.set_dying()

            if not player.get_invincible():
                if did_collide(player.hitbox, enemy.rect):
                    player.hit_by(enemy)
            collision_check(enemy, coll_rects, rooms, walls, False, player)

            if enemy.get_alert() and not enemy.surprise_icon:
                enemy.surprise_icon = True
                ui_group.add(SurpriseIcon(enemy))

        for item in item_group:
            if item.rect.colliderect(player.hitbox) or (
                    item.rect.colliderect(sword.rect) and sword.is_using()):
                player.get_item(item)
                stop_player = False
                ### item drop actions ###
                if item.name == "arrow":
                    bow.add_ammo(5)
                if item.name == "bomb":
                    bomb_bag.add_ammo(3)
                if item.name == "flame":
                    glove.add_ammo(3)

                ### equipment pickup actions ###
                text = None
                if item.name == "sword":
                    sword.equip_item()
                    text = DialogueText(screen, name="", lines=["You got the sword!",
                                                                "Press Spacebar to swing it!"])
                    stop_player = True

                if item.name == "flame_glove":
                    glove.equip_item()
                    text = DialogueText(screen, name="", lines=["You got the flame glove!",
                                                                "Press F or L to launch a fireball!"])
                    ui_group.add(flame_count)
                    stop_player = True

                if item.name == "bomb_bag":
                    bomb_bag.equip_item()
                    text = DialogueText(screen, name="", lines=["You got the bomb bag! Press K to drop a bomb!",
                                                                "If you hit it with your sword, it will explode",
                                                                "immediately. (Bombs can't hit you!)"])
                    ui_group.add(bomb_count)
                    stop_player = True

                if item.name == "bow":
                    bow.equip_item()
                    text = DialogueText(screen, name="", lines=["You got the bow!",
                                                                "Press J or B to fire an arrow!"])
                    ui_group.add(arrow_count)
                    stop_player = True

                if item.name == "queen_key":
                    player.region_keys["tower"].add_boss_key()
                    if player.region_keys["tower"].get_boss_keys() <= 1:
                        text = DialogueText(screen, name="", lines=["You got a... blue key?",
                                                                    "You're not sure what it's for, but it's probably",
                                                                    "what the Mayor was looking for."])
                    else:
                        text = DialogueText(screen, name="", lines=["You got a key to the Queen's Tower!"])
                    stop_player = True

                if item.name == "heart_up":
                    text = DialogueText(screen, name="",
                                        lines=["You got a heart container!",
                                               "Your health has increased by one full heart!"])
                    stop_player = True
                if stop_player:
                    for dir in "wasd":
                        player.stop_move(dir)
                if text is not None:
                    text.loop()
                rooms.remove_item(item)
                item_group.remove(item)
                item.destruct()

        player_group.update()
        enemy_group.update()

        for obj in object_group:
            collision_check(obj, coll_rects, rooms, walls, False, player)
            if obj.rect.colliderect(sword.rect) and sword.is_using():
                obj.hit_by(sword)
            if (p_use.is_active() and did_collide(p_use.rect, obj.rect)):
                try:
                    obj.use()
                except Exception as e:
                    to_do = "nothing"
                    item_to_add = None
                    try:
                        to_do = obj.use(rooms, player)
                    except:
                        pass
                    if to_do == "gold":
                        player.add_gold(1000)
                    elif to_do == "remove_soldiers":
                        # Removes 2 soldiers blocking path to queen's tower
                        rooms.room_objects[8][7].pop(3)
                        rooms.room_objects[8][7].pop(4)
                    elif to_do == "heart_up":
                        item_to_add = HeartContainer
                    elif to_do == "potion":
                        player.add_potion()
                    elif to_do == "potion_up":
                        player.max_potions += 1
                        player.add_potion()
                    elif to_do == "arrow":
                        item_to_add = ArrowItem
                    elif to_do == "bomb":
                        item_to_add = BombItem
                    elif to_do == "flame":
                        item_to_add = FlameItem
                    elif to_do == "bow":
                        item_to_add = BowUpgrade
                    if item_to_add is not None:
                        player_pos = list(player.rect.center[:])
                        for i in range(len(player_pos)):
                            player_pos[i] /= tile_size(1)
                        item_group.add(item_to_add(player_pos, 17))

                if obj.is_puzzle:
                    if player.region in Player.ALL_REGIONS:
                        if obj.affects == "key":
                            if player.region_keys[player.region].get_keys() > 0:
                                player.region_keys[player.region].remove_key()
                                rooms.remove_object(obj)
                                obj.destruct()
                        if obj.affects == "boss_key":
                            if player.region_keys[player.region].get_boss_keys() > 0:
                                player.region_keys[player.region].remove_boss_key()
                                rooms.remove_object(obj)
                                obj.destruct()

                p_use.update()
            if obj.is_puzzle:
                if obj.affects == "sprite":
                    status = obj.get_status()
                    if isinstance(status, int):
                        PuzzleObjects.all_sprite = status
                if obj.affects == "enemies":
                    if not any_left:
                        obj.set_sprite(1)
                    else:
                        obj.set_sprite(0)

        for enemy in death_group:
            # enemy.launch_away()
            enemy.update()
            if enemy.is_boss:
                if enemy.__class__.__name__ == "DemonQueen":
                    ending_timer = 1.5 * FPS
            maybe_dead = enemy.death_check()
            if maybe_dead == "delete":
                death_group.remove(enemy)
                death_spot = (enemy.rect.centerx/16, enemy.rect.centery/16)
                enemy.kill()
                if random.randint(1, 3) != 3:  # chance of dropping an item
                    item_list = [HeartItem, BombItem, ArrowItem, FlameItem, GoldItem, GoldItem, GoldItem]
                    # Adds extra item drops if ammo or health drop below certain amounts
                    eq_lst = [bow, bomb_bag, glove]
                    eq_drop = [ArrowItem, BombItem, FlameItem]
                    for i in range(len(eq_lst)):
                        if eq_lst[i].get_ammo() <= 5:
                            for num in range(3):
                                item_list.append(eq_drop[i])
                    if player.health <= round(player.max_health/5):
                        for num in range(3):
                            item_list.append(HeartItem)
                    item_to_add = random.choice(item_list)
                    item_group.add(item_to_add(death_spot))

        ################# CLEARING AND REDRAWING SCREEN ##################################
        # Drawing floor of screen
        rooms.redraw_room(screen)

        object_group.update()
        object_group.draw(screen)

        # Drawing player and enemies
        player_group.draw(screen)
        enemy_group.draw(screen)

        # Drawing anything above player/enemies
        rooms.redraw_room_top(screen)

        # Drawing UI and items, then any exploding enemies.
        item_group.update()
        item_group.draw(screen)

        player_projectiles.update()
        player_projectiles.draw(screen)

        enemy_projectiles.update()
        enemy_projectiles.draw(screen)

        ui_group.update()
        ui_group.draw(screen)
        for ui in ui_group:
            if ui.__class__.__name__ in ["UIIcon", "KeyCount"]:
                ui.draw(screen)  # Draws ammo count for several equipment pieces

        death_group.draw(screen)

        draw_boss_health(screen, enemy_group)


        # Scaling up game screen due to low resolution
        if not rooms.get_status("room_transition"):
            flip_screen()

        if rooms.get_status("intro") and rooms.room_num == [3, 4]:
            intro_dialogue = DialogueText(screen, "", AllRooms.INTRO_LINES)
            intro_dialogue.loop()
            rooms.set_status("intro", False)

        if not rooms.get_status("room_transition") and rooms.get_status("village_scene") and rooms.room_num == [6, 7]:
            village_dialogue = DialogueText(screen, "Soldier", AllRooms.VILLAGE_LINES)
            village_dialogue.loop()
            rooms.set_status("village_scene", False)

        if not rooms.get_status("room_transition") and rooms.get_status("queen_dialogue") and rooms.room_num == [13, 10]:
            queen_dialogue = DialogueText(screen, "The Demon Queen Velverosa",
                                          AllRooms.QUEEN_LINES)
            queen_dialogue.loop()
            rooms.set_status("queen_dialogue", False)

        if ending_timer == 0:
            rooms.set_status("ending")

        if rooms.get_status("ending"):
            # This is the ending cutscene for the game. Was intended to be far more complex,
            # but it's 1AM and I had forgotten to do it until the last minute.
            background = screen.copy()

            set_music(MENU_MUSIC[0], MENU_MUSIC[1])

            ending_dialogue = DialogueText(screen, "",
                                           ["As the Demon Queen falls, you know that you've",
                                            "saved countless lives. The trials and tribulations",
                                            "that you have faced were well worth it.",
                                            None,
                                            "For now, though, you head back to the village",
                                            "to get some well-earned rest."])
            ending_dialogue.loop()

            final_action = None
            ending_title = GameMenu(["        Queen's Demise        "],
                                    ["Developed by Zoeyism"])
            ending_title.set_back_image()
            ending_title.set_highlight(get_color("purple"))
            ending_title.set_font(pygame.font.Font(os.path.join("Fonts", "Kenney Pixel Square.ttf"), 16))
            ending_title.set_pos(tile_size(3), tile_size(3))

            option = GameOptions(["End Game", "end"])
            option.set_option(["End Game", "end"], 1)

            while final_action is None:
                final_action = option.update(pygame.event.get())
                if final_action is not None and final_action == "end":
                    exit_game()

                screen.blit(background, (0, 0))
                ending_title.draw(screen)
                option.draw(screen)

                flip_screen()
    Heart.reset()  # Resets the number of hearts in the UI, allows loading back in without issues


def main():
    # Setting music and how often to repeat key presses
    set_music(MENU_MUSIC[0], MENU_MUSIC[1])
    pygame.key.set_repeat(round(100 / FPS))

    # Setting main menu title
    title = GameMenu(["Queen's Demise"])
    title.set_font(pygame.font.Font(
        os.path.join("Fonts", "Kenney Mini Square.ttf"), 16))
    title.set_back_image()
    title.center_at(tile_size(10), tile_size(2))
    title.set_color(get_color("purple"))
    title.set_highlight(get_color("purple"))

    # Setting up actual menu options
    menu = GameMenu(["Start Game", gameplay], ["Controls", controls_menu],
                    ["Credits", credits_menu], ["Quit Game", exit_game])

    menu.set_back_image()
    menu.center_at(tile_size(9.5), tile_size(13.5))
    rooms.set_status("start_menu")
    menu_back1 = pygame.image.load(os.path.join("mapFiles", "[6,7].png")).convert()
    menu_back2 = pygame.image.load(os.path.join("mapFiles", "[6,7]top.png")).convert_alpha()

    while rooms.get_status("start_menu"):
        screen.blit(menu_back1, (0, 0))
        screen.blit(menu_back2, (0, 0))
        menu.update(pygame.event.get())
        menu.draw(screen)

        title.draw(screen)

        flip_screen()

    pygame.quit()


if __name__ == "__main__":
    """ Queen's Demise! Hope you enjoy it <3 """
    main()
