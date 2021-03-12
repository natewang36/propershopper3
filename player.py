from collections import defaultdict
from random import randint

import pygame
import config
from enums.direction import Direction
from enums.cart_state import CartState
from render_game import render_text


class Player:
    def __init__(self, x_position, y_position, direction, player_number):
        # player ID
        self.player_number = player_number
        # which way player is facing
        self.direction = direction
        self.position = [x_position, y_position]

        # stage of walking animation, indices correspond to direction (north = 0, south = 1, east = 2, west = 3)
        self.stage = [0, 0, 0, 0]
        # iterates walking animation
        self.stage_counter = 0
        # arrays of player images in each direction
        self.north_images = []
        self.south_images = []
        self.east_images = []
        self.west_images = []

        self.curr_cart = None

        # player inventory
        self.render_inventory = False

        # shopping list
        self.render_shopping_list = False
        self.shopping_list = []
        # quantities for foods, indices correspond to indices of shopping_list list
        self.list_quant = []

        self.load_images()
        self.width = .01
        self.height = .01
        # The food that's in the player's hand.
        self.holding_food = None
        self.holding_food_image = None
        self.bought_holding_food = False

    def update_position(self, new_position):
        self.position[0] = new_position[0]
        self.position[1] = new_position[1]
        if self.curr_cart is not None:
            if self.curr_cart.being_held:
                self.curr_cart.update_position(new_position[0], new_position[1])

    def stand_still(self):
        self.stage[0] = 6
        self.stage[1] = 6
        self.stage[2] = 5
        self.stage[3] = 5

    def set_shopping_list(self, food_list):
        list_length = randint(1, 12)
        num_food_items = len(food_list)
        for i in range(list_length):
            x = randint(0, num_food_items - 1)
            self.shopping_list.append(food_list[x])
        rendering_food = []

        # setting quantities for duplicate foods
        for food in self.shopping_list:
            assert isinstance(food, object)
            if food in rendering_food:
                self.list_quant[rendering_food.index(food)] += 1
            else:
                rendering_food.append(food)
                self.list_quant.append(1)
        self.shopping_list = rendering_food

    def hold_food(self, string_food, food_image):
        self.holding_food = string_food
        self.holding_food_image = food_image

    def take_food(self):
        self.holding_food = None
        self.holding_food_image = None
        self.bought_holding_food = False

    def iterate_stage(self, direction):
        # counter mod 4 to slow down the walking animation -- there's probably a better way to do this
        if self.stage_counter % 4 == 0:
            self.stage[direction] += 1

        # looping animation back to 0
        if self.stage[direction] > 5:
            self.stage[direction] = 0

        # iterating counter
        self.stage_counter += 1

    def render_player(self, screen, camera):
        direction = self.direction
        image = None
        if direction == Direction.NORTH:

            image = self.north_images[self.stage[0]]

        elif direction == Direction.SOUTH:

            image = self.south_images[self.stage[1]]

        elif direction == Direction.EAST:
            image = self.east_images[self.stage[2]]

        elif direction == Direction.WEST:

            image = self.west_images[self.stage[3]]

        image = pygame.transform.scale(image, (config.SCALE, config.SCALE))
        rect = pygame.Rect(self.position[0] * config.SCALE - (camera.position[0] * config.SCALE),
                           self.position[1] * config.SCALE - (camera.position[1] * config.SCALE),
                           config.SCALE, config.SCALE)
        screen.blit(image, rect)

    def render_food(self, screen, camera, image):
        rect = pygame.Rect((self.position[0] - camera.position[0] + 0.35)*config.SCALE,
                           (self.position[1] - camera.position[1] + 0.5)*config.SCALE,
                           config.SCALE, config.SCALE)
        screen.blit(image, rect)

    def render(self, screen, camera, carts):
        self.render_player(screen, camera)
        if self.holding_food is not None:
            self.render_food(screen, camera, self.holding_food_image)

    def render_list(self, screen, carts):
        textbox = pygame.transform.scale(pygame.image.load("text/textboxvertical.png"),
                                         (int(430), int(460)))
        screen.blit(textbox, (int(1.6 * config.SCALE), int(.2 * config.SCALE)))
        text = render_text("Shopping List: ", True, (0, 0, 0))
        screen.blit(text, (200, 50))
        spacing = 30
        y_position = 50 + spacing

        counter = 0
        inventory = self.get_inventory(carts)
        for food in self.shopping_list:
            text = render_text(food, False, (0, 0, 0))
            screen.blit(text, (155, y_position))
            quantity = str(self.list_quant[counter])
            text = render_text(quantity, False, (0, 0, 0))
            screen.blit(text, (470, y_position))
            if food in inventory and self.list_quant[self.shopping_list.index(food)] <= inventory[food][1]:
                pygame.draw.line(screen, [255, 0, 0], (150, y_position + 7), (487, y_position + 7), width=2)
            counter += 1
            y_position += spacing

    # Currently includes both purchased and unpurchased items. We could potentially separate it for finer-grained info.
    def get_inventory(self, carts):
        inventory = defaultdict(defaultdict)

        if self.holding_food is not None:
            if self.bought_holding_food is True:
                inventory[self.holding_food]["purchased"] = 1
                inventory[self.holding_food]["unpurchased"] = 0
            else:
                inventory[self.holding_food]["purchased"] = 0
                inventory[self.holding_food]["unpurchased"] = 1
        for cart in carts:
            if cart.last_held == self:
                for food, quantity in cart.contents.items():
                    inventory[food]["unpurchased"] = 0
                    inventory[food]["purchased"] = 0
                    inventory[food]["unpurchased"] += quantity
                for food, quantity in cart.purchased_contents.items():
                    if "unpurchased" not in inventory[food]:
                        inventory[food]["unpurchased"] = 0
                    inventory[food]["purchased"] = 0
                    inventory[food]["purchased"] += quantity
        return inventory

    def render_items(self, screen, carts):
        textbox = pygame.transform.scale(pygame.image.load("text/textboxvertical.png"),
                                         (int(430), int(450)))
        screen.blit(textbox, (int(1.6 * config.SCALE), int(.2 * config.SCALE)))
        text = render_text("Inventory: ", True, (0, 0, 0))
        screen.blit(text, (230, 50))
        spacing = 30
        y_position = 50 + spacing
        inventory = self.get_inventory(carts)
        for food in inventory.keys():
            # if not food in rendered_food:
            text = render_text(food, False, (0, 0, 0))
            screen.blit(text, (155, y_position))

            unpurchased = render_text(str(inventory[food]["unpurchased"]), False, (250, 0, 0))
            purchased = render_text(str(inventory[food]["purchased"]), False, (0, 250, 0))

            screen.blit(unpurchased, (420, y_position))
            screen.blit(purchased, (460, y_position))
            y_position += spacing

    def collision(self, x_position, y_position):
        i = self.position[0]
        while i <= self.position[0] + self.width:
            j = self.position[1]
            while j <= self.position[1] + self.height:

                y_distance = abs(y_position - j)
                x_distance = abs(x_position - i)
                if y_distance < .7 and x_distance < .7:
                    return True
                j += 0.5
            i += 0.5
        return False

    def reset_cart(self):
        if self.curr_cart is not None:
            cart = self.curr_cart
            if cart.state == CartState.PURCHASED:
                cart.state = CartState.EMPTY

    def load_images(self):
        self.load_north()
        self.load_south()
        self.load_east()
        self.load_west()

    def load_north(self):
        # right now I only have images for two players
        if self.player_number == 1:
            self.north_images.append(pygame.image.load("images/sprites/north/amelia_run_back1.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/amelia_run_back2.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/amelia_run_back3.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/amelia_run_back4.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/amelia_run_back5.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/amelia_run_back6.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/amelia_stand_back.png"))
        elif self.player_number == 2:
            self.north_images.append(pygame.image.load("images/sprites/north/edward_run_back1.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/edward_run_back2.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/edward_run_back3.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/edward_run_back4.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/edward_run_back5.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/edward_run_back6.png"))
            self.north_images.append(pygame.image.load("images/sprites/north/edward_stand_back.png"))

    def load_south(self):
        if self.player_number == 1:
            self.south_images.append(pygame.image.load("images/sprites/south/amelia_run_front1.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/amelia_run_front2.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/amelia_run_front3.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/amelia_run_front4.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/amelia_run_front5.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/amelia_run_front6.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/amelia_stand_front.png"))
        elif self.player_number == 2:
            self.south_images.append(pygame.image.load("images/sprites/south/edward_run_front1.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/edward_run_front2.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/edward_run_front3.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/edward_run_front4.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/edward_run_front5.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/edward_run_front6.png"))
            self.south_images.append(pygame.image.load("images/sprites/south/edward_stand_front.png"))

    def load_east(self):
        if self.player_number == 1:
            self.east_images.append(pygame.image.load("images/sprites/east/amelia_run_right1.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/amelia_run_right2.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/amelia_run_right3.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/amelia_run_right4.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/amelia_run_right5.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/amelia_run_right6.png"))
        elif self.player_number == 2:
            self.east_images.append(pygame.image.load("images/sprites/east/edward_run_right1.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/edward_run_right2.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/edward_run_right3.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/edward_run_right4.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/edward_run_right5.png"))
            self.east_images.append(pygame.image.load("images/sprites/east/edward_run_right6.png"))

    def load_west(self):
        if self.player_number == 1:
            self.west_images.append(pygame.image.load("images/sprites/west/amelia_run_left1.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/amelia_run_left2.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/amelia_run_left3.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/amelia_run_left4.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/amelia_run_left5.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/amelia_run_left6.png"))
        elif self.player_number == 2:
            self.west_images.append(pygame.image.load("images/sprites/west/edward_run_left1.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/edward_run_left2.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/edward_run_left3.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/edward_run_left4.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/edward_run_left5.png"))
            self.west_images.append(pygame.image.load("images/sprites/west/edward_run_left6.png"))