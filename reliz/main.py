import pygame
import random
import math
import time

pygame.init()

pygame.mixer.init()

# Завантаження музичного файлу
pygame.mixer.music.load("background.wav")

# Відтворення музики у циклі
pygame.mixer.music.play(-1) 

width = 1980
height = 1080
clock = pygame.time.Clock()

window = pygame.display.set_mode((width, height))
pygame.display.set_caption('Cube adventure')

yellow = (255, 247, 0)
white = (255, 255, 255)
green = (0, 255, 0)
brown = (139, 69, 19)
red = (255, 0, 0)
orange = (255, 165, 0)
dark_gray = (50, 50, 50)
light_gray = (170, 170, 170)
black = (0, 0, 0)
player_speed = 5
player_size = 50
reload_time = 1.5
shot_delay = 0.5

font = pygame.font.SysFont(None, 36)

background_image = pygame.image.load("background.jpg")
background_image = pygame.transform.scale(background_image, (width, height))

shop_image = pygame.image.load("Shop.png")
shop_image = pygame.transform.scale(shop_image, (300, 200))

points = 0
inside_shop = False

class Tree:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.trunk_color = brown
        self.foliage_color = green

    def draw(self, surface):
        pygame.draw.rect(surface, self.trunk_color, (self.rect.x + 15, self.rect.y + 40, 20, 60))
        pygame.draw.rect(surface, self.foliage_color, (self.rect.x, self.rect.y, 50, 50))

class HeroObject:
    def __init__(self, x, y, health, damage):
        self.rect = pygame.Rect(x, y, player_size, player_size)
        self.health = health
        self.damage = damage
        self.speed = 5
        self.color = green
        self.bullets = []
        self.ammo_count = 30
        self.last_shot_time = 0
        self.is_reloading = False
        self.has_magic_scroll = False  # Чи куплено магічний сувій
        self.magic_charge_start = None  # Час початку зарядки магії

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

    def move(self, dx, dy, obstacles):
        new_x = self.rect.x + dx
        new_y = self.rect.y + dy
        temp_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)
        if not any(temp_rect.colliderect(obstacle.rect) for obstacle in obstacles):
            self.rect.x = new_x
            self.rect.y = new_y

    def shoot(self, target_x, target_y):
        current_time = time.time()

        # Магічна атака: 6 снарядів після 5 секунд зарядки
        if self.has_magic_scroll and pygame.mouse.get_pressed()[0]:
            if self.magic_charge_start is None:  # Початок зарядки
                self.magic_charge_start = current_time
            elif current_time - self.magic_charge_start >= 5:  # Зарядка завершена
                self.magic_charge_start = None  # Скидання зарядки
                self.magic_attack(target_x, target_y)
                return
        else:
            self.magic_charge_start = None  # Скидання, якщо кнопка відпущена

        # Звичайна атака
        if self.ammo_count > 0 and not self.is_reloading and current_time - self.last_shot_time >= shot_delay:
            bullet = Bullet(self.rect.centerx, self.rect.centery, target_x, target_y)
            self.bullets.append(bullet)
            self.ammo_count -= 1
            self.last_shot_time = current_time
        elif self.ammo_count == 0:
            print("Out of ammo! Press R to reload.")

    def magic_attack(self, target_x, target_y):
        """Виконує магічну атаку 6-ма снарядами."""
        print("Magic Scroll Activated!")
        for angle_offset in [-30, -15, 0, 15, 30, 45]:  # Кути для розльоту снарядів
            angle = math.atan2(target_y - self.rect.centery, target_x - self.rect.centerx) + math.radians(angle_offset)
            speed_x = 5 * math.cos(angle)
            speed_y = 5 * math.sin(angle)
            bullet = Bullet(self.rect.centerx, self.rect.centery, self.rect.centerx + speed_x * 10, self.rect.centery + speed_y * 10)
            bullet.color = orange  # Інший колір для магічних снарядів
            self.bullets.append(bullet)

    def update_bullets(self, enemies, trees):
        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.is_off_screen(width, height):
                self.bullets.remove(bullet)
            else:
                for tree in trees:
                    if bullet.rect.colliderect(tree.rect):
                        self.bullets.remove(bullet)
                        break
                for enemy in enemies:
                    if bullet.rect.colliderect(enemy.rect):
                        enemy.take_damage(self.damage)
                        self.bullets.remove(bullet)
                        break

    def reload(self):
        if not self.is_reloading:
            self.is_reloading = True
            pygame.time.set_timer(pygame.USEREVENT, int(reload_time * 1000))

    def finish_reloading(self):
        self.ammo_count = 30
        self.is_reloading = False
        pygame.time.set_timer(pygame.USEREVENT, 0)


class EnemyObject:
    def __init__(self, x, y, width, height, color, health):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.health = health
        self.speed = 2
        self.bullets = []
        self.last_shot_time = 0
        self.shot_delay = 1

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

    def move_towards_player(self, player, obstacles, enemies):
        dx = player.rect.x - self.rect.x
        dy = player.rect.y - self.rect.y
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if dist > 0:
            dx = (dx / dist) * self.speed
            dy = (dy / dist) * self.speed

            new_x = self.rect.x + dx
            new_y = self.rect.y + dy
            temp_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)

            if not any(temp_rect.colliderect(obstacle.rect) for obstacle in obstacles):
                if not any(temp_rect.colliderect(enemy.rect) for enemy in enemies if enemy != self):
                    self.rect.x += dx
                    self.rect.y += dy

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            print("Enemy defeated")
            global points
            points += 10  # Додаємо 10 поінтів за вбивство ворога

    def shoot(self, player):
        current_time = time.time()
        if current_time - self.last_shot_time >= self.shot_delay:
            bullet = Bullet(self.rect.centerx, self.rect.centery, player.rect.centerx, player.rect.centery)
            self.bullets.append(bullet)
            self.last_shot_time = current_time

    def update_bullets(self, player, trees):
        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.is_off_screen(width, height):
                self.bullets.remove(bullet)
            else:
                for tree in trees:
                    if bullet.rect.colliderect(tree.rect):
                        self.bullets.remove(bullet)
                        break
                if bullet.rect.colliderect(player.rect):
                    player.health -= 10
                    self.bullets.remove(bullet)

class Bullet:
    def __init__(self, x, y, target_x, target_y):
        self.rect = pygame.Rect(x, y, 10, 10)
        self.color = yellow
        angle = math.atan2(target_y - y, target_x - x)
        self.speed_x = 5 * math.cos(angle)
        self.speed_y = 5 * math.sin(angle)

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

    def is_off_screen(self, width, height):
        return not (0 <= self.rect.x <= width and 0 <= self.rect.y <= height)

points = 0

# Глобальний код магазину як окремої локації
SHOP_LOCATION = "shop"


class Shop:
    def __init__(self):
        self.items = [
            {"name": "Potion", "price": 10, "description": "Відновлює 50 здоров'я"},
            {"name": "Sword", "price": 50, "description": "Підвищує вашу атаку"},
            {"name": "Armor", "price": 30, "description": "Збільшує вашу броню"},
            {"name": "Boots", "price": 20, "description": "Збільшує швидкість руху"},
            {"name": "Shield", "price": 40, "description": "Зменшує отриману шкоду"},
            {"name": "Helmet", "price": 25, "description": "Підвищує захист голови"},
            {"name": "Ring", "price": 15, "description": "Додає +5 до атаки"},
            {"name": "Bow", "price": 60, "description": "Дозволяє стріляти на великій відстані"},
            {"name": "Magic Scroll", "price": 70, "description": "Викликає магічний шквал"}
        ]
        self.font = pygame.font.SysFont(None, 24)
        self.item_rects = []  # Прямокутники для предметів
        self.selected_item = None  # Вибраний предмет
        self.state = "main"  # "main" або "item"
        self.generate_item_rects()

    def generate_item_rects(self):
        """Розташування предметів у вигляді сітки 3x3"""
        padding = 20
        item_size = 100
        start_x = (width - (3 * item_size + 2 * padding)) // 2
        start_y = (height - (3 * item_size + 2 * padding)) // 2

        self.item_rects = [
            pygame.Rect(start_x + (i % 3) * (item_size + padding), 
                        start_y + (i // 3) * (item_size + padding), 
                        item_size, item_size)
            for i in range(len(self.items))
        ]

    def draw_main(self, surface, mouse_pos):
        """Малює головне меню магазину"""
        surface.fill((200, 200, 200))
        for i, item_rect in enumerate(self.item_rects):
            pygame.draw.rect(surface, dark_gray, item_rect)

            # Відображення назви предмета
            item_name = self.items[i]["name"]
            name_label = self.font.render(item_name, True, black)
            surface.blit(
                name_label, 
                (item_rect.x + (item_rect.width - name_label.get_width()) // 2, item_rect.y + 5)
            )

            # Якщо курсор наведено, підсвітити предмет
            if item_rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, light_gray, item_rect, 3)

        # Текст для виходу
        exit_text = self.font.render("Натисніть 'E' для виходу", True, black)
        surface.blit(exit_text, (width // 2 - exit_text.get_width() // 2, height - 50))

    def draw_item(self, surface):
        """Малює меню обраного предмета"""
        surface.fill((200, 200, 200))

        # Відображення інформації про предмет
        if self.selected_item is not None:
            item = self.items[self.selected_item]
            title = self.font.render(item["name"], True, black)
            description = self.font.render(item["description"], True, black)
            price = self.font.render(f"Ціна: {item['price']} coins", True, black)

            surface.blit(title, (width // 2 - title.get_width() // 2, height // 2 - 50))
            surface.blit(description, (width // 2 - description.get_width() // 2, height // 2))
            surface.blit(price, (width // 2 - price.get_width() // 2, height // 2 + 50))

            buy_text = self.font.render("Натисніть 'Q' щоб купити", True, black)
            surface.blit(buy_text, (width // 2 - buy_text.get_width() // 2, height // 2 + 100))

        # Текст для повернення
        back_text = self.font.render("Натисніть 'E' щоб повернутися", True, black)
        surface.blit(back_text, (width // 2 - back_text.get_width() // 2, height - 50))

    def handle_click(self, player, mouse_pos):
        global points
        if self.state == "main":
            for i, item_rect in enumerate(self.item_rects):
                if item_rect.collidepoint(mouse_pos):
                    self.selected_item = i
                    self.state = "item"  # Перехід до меню предмета
                    return
        elif self.state == "item":
            if self.selected_item is not None:
                item = self.items[self.selected_item]
                if points >= item["price"]:
                    points -= item["price"]
                    print(f"Ви купили {item['name']} за {item['price']} coins!")
                    if item["name"] == "Magic Scroll":
                        player.has_magic_scroll = True  # Активуємо магічний сувій
                    # Інші предмети
                    elif item["name"] == "Potion":
                        player.health += 50
                    elif item["name"] == "Sword":
                        player.damage += 10
                    elif item["name"] == "Armor":
                        player.health += 20
                    elif item["name"] == "Boots":
                        player.speed += 2
                    elif item["name"] == "Shield":
                        player.health += 30
                    elif item["name"] == "Helmet":
                        player.health += 10
                    elif item["name"] == "Ring":
                        player.damage += 5
                    elif item["name"] == "Bow":
                        player.damage += 15
                else:
                    print("Недостатньо очок для покупки!")

    def handle_key(self, key):
        if key == pygame.K_e:
            if self.state == "item":
                self.state = "main"
                self.selected_item = None
                return "exit"
            elif self.state == "main":
                return "exit"
        elif key == pygame.K_q and self.state == "item":
            return "buy"
        return None

def safe_spawn(player, trees):
    safe_distance = 60
    for _ in range(100):
        player.rect.x = random.randint(0, width - player_size)
        player.rect.y = random.randint(0, height - player_size)
        if all(math.hypot(player.rect.centerx - tree.rect.centerx, player.rect.centery - tree.rect.centery) > safe_distance for tree in trees):
            break

def generate_trees():
    trees = []
    for i in range(50):
        x = random.randint(0, width - 50)
        y = random.randint(0, height - 100)
        trees.append(Tree(x, y, 50, 100))
    return trees

def generate_enemies(trees):
    enemies = []
    for i in range(15):
        while True:
            x = random.randint(0, width - 50)
            y = random.randint(0, height - 50)
            new_enemy = EnemyObject(x, y, 50, 50, red, 50)
            if not any(new_enemy.rect.colliderect(tree.rect) for tree in trees):
                enemies.append(new_enemy)
                break
    return enemies

def generate_shop():
    chance = random.random()
    if chance < 0.3:
        return Shop()  
    return None


player = HeroObject(width // 2, height // 2, 100, 10)

current_location = (0, 0)

world_map = {}

initial_trees = generate_trees()
world_map[current_location] = {
    'trees': initial_trees,
    'enemies': generate_enemies(initial_trees),
    'shop': generate_shop()
}

def load_location(location):
    """Завантаження локації на основі її координат."""
    if location not in world_map:
        shop = generate_shop()
        if shop:  # Якщо магазин генерується, створюємо тільки магазин
            world_map[location] = {
                'trees': [],
                'enemies': [],
                'shop': shop
            }
        else:  # Якщо магазину немає, генеруємо стандартну локацію
            trees = generate_trees()
            enemies = generate_enemies(trees)
            world_map[location] = {
                'trees': trees,
                'enemies': enemies,
                'shop': None
            }
    return world_map[location]

def display_hud(surface, ammo, points, health):
    ammo_text = font.render(f"Ammo: {ammo}", True, white)
    points_text = font.render(f"Points: {points}", True, white)
    health_text = font.render(f"Health: {health}", True, white)
    surface.blit(ammo_text, (width - 150, 10))
    surface.blit(points_text, (width - 150, 50))
    surface.blit(health_text, (width - 150, 90))

def game_over_screen():
    window.fill((0, 0, 0))
    game_over_text = font.render("Game Over", True, white)
    restart_text = font.render("Press 'R' to Restart", True, white)
    quit_text = font.render("Press 'Q' to Quit", True, white)

    window.blit(game_over_text, (width // 2 - game_over_text.get_width() // 2, height // 2 - 100))
    window.blit(restart_text, (width // 2 - restart_text.get_width() // 2, height // 2))
    window.blit(quit_text, (width // 2 - quit_text.get_width() // 2, height // 2 + 50))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main_game_loop()
                    waiting = False
                if event.key == pygame.K_q:
                    pygame.quit()
                    exit()
# Оголосимо глобальний магазин
shop = Shop()

def main_game_loop():
    global run, current_location, points, player, inside_shop
    run = True
    points = 50  # Початкове значення
    inside_shop = False
    player = HeroObject(width // 2, height // 2, 100, 10)

    # Завантаження початкової локації
    initial_trees = generate_trees()
    world_map[current_location] = {
        'trees': initial_trees,
        'enemies': generate_enemies(initial_trees),
        'shop': generate_shop()
    }

    while run:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.USEREVENT:
                player.finish_reloading()
            if event.type == pygame.MOUSEBUTTONDOWN and inside_shop:
                shop.handle_click(player, mouse_pos)
            if event.type == pygame.KEYDOWN and inside_shop:
                action = shop.handle_key(event.key)
                if action == "exit":
                    inside_shop = False

        if player.health <= 0:
            game_over_screen()
            return

        dx, dy = 0, 0
        keys = pygame.key.get_pressed()

        # Відображення магазину
        if inside_shop:
            if shop.state == "main":
                shop.draw_main(window, mouse_pos)
            elif shop.state == "item":
                shop.draw_item(window)

            # Оновлення екрану
            pygame.display.flip()
            clock.tick(60)
            continue

        # Основна гра
        # Рух гравця
        if keys[pygame.K_a]: dx = -player.speed
        if keys[pygame.K_d]: dx = player.speed
        if keys[pygame.K_w]: dy = -player.speed
        if keys[pygame.K_s]: dy = player.speed

        # Стрільба
        if pygame.mouse.get_pressed()[0]:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            player.shoot(mouse_x, mouse_y)

        # Перезарядка
        if keys[pygame.K_r] and not player.is_reloading:
            player.reload()

        # Перевірка переходів між локаціями
        if player.rect.x < 0:  # Ліва межа
            current_location = (current_location[0] - 1, current_location[1])
            player.rect.x = width - player_size
            location_data = load_location(current_location)
            safe_spawn(player, location_data['trees'])
        elif player.rect.x + player_size > width:  # Права межа
            current_location = (current_location[0] + 1, current_location[1])
            player.rect.x = 0
            location_data = load_location(current_location)
            safe_spawn(player, location_data['trees'])
        elif player.rect.y < 0:  # Верхня межа
            current_location = (current_location[0], current_location[1] - 1)
            player.rect.y = height - player_size
            location_data = load_location(current_location)
            safe_spawn(player, location_data['trees'])
        elif player.rect.y + player_size > height:  # Нижня межа
            current_location = (current_location[0], current_location[1] + 1)
            player.rect.y = 0
            location_data = load_location(current_location)
            safe_spawn(player, location_data['trees'])

        # Завантаження об'єктів для поточної локації
        location_data = load_location(current_location)
        trees = location_data['trees']
        enemies = location_data['enemies']
        shop_location = location_data['shop']

        # Рух і взаємодія з об'єктами
        player.move(dx, dy, trees)
        player.update_bullets(enemies, trees)

        for enemy in enemies:
            if enemy.health > 0:
                enemy.move_towards_player(player, trees, enemies)  # Рух до гравця
                enemy.shoot(player)  # Атакує гравця
                enemy.update_bullets(player, trees)  # Оновлює кулі

        # Малювання об'єктів
        if background_image:
            window.blit(background_image, (0, 0))
        else:
            window.fill((0, 0, 0))  # Якщо фон не завантажено

        # Малювання магазину
        if shop_location:
            shop_rect = pygame.Rect(width // 2 - 150, height // 2 - 100, 300, 200)
            window.blit(shop_image, (shop_rect.x, shop_rect.y))

            # Вхід у магазин
            if player.rect.colliderect(shop_rect):
                shop_text = font.render("Press 'E' to Enter Shop", True, white)
                window.blit(shop_text, (shop_rect.x + 20, shop_rect.y - 30))
                if keys[pygame.K_e]:
                    inside_shop = True

        # Малювання дерев, ворогів і гравця
        for tree in trees:
            tree.draw(window)
        for enemy in enemies:
            if enemy.health > 0:
                enemy.draw(window)
        for bullet in player.bullets:
            bullet.draw(window)
        for enemy in enemies:
            for bullet in enemy.bullets:
                bullet.draw(window)

        player.draw(window)

        # Відображення HUD
        display_hud(window, player.ammo_count, points, player.health)

        # Оновлення екрану
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
main_game_loop()