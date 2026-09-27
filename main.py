import sys
import pygame

# Инициализация Pygame
pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cookie Run: Kingdom - Battle Python Edition")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 20)
font_big = pygame.font.SysFont("arial", 32)

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
PURPLE = (155, 89, 182)
GOLD = (241, 196, 15)
PINK = (255, 150, 200)
YELLOW = (255, 230, 100)

# --- ГЕРОИ ---
HERO_DATA = [
    {
        "name": "Pure Vanilla",
        "role": "Лекарь / Щит",
        "color": (255, 240, 150),
        "file": "pure_vanilla.png",
    },
    {
        "name": "Shadow Milk",
        "role": "Обманщик / Урон",
        "color": (100, 100, 150),
        "file": "shadow_milk.png",
    },
    {
        "name": "Eternal Sugar",
        "role": "Маг / ДПС",
        "color": (255, 150, 200),
        "file": "eternal_sugar.png",
    },
    {
        "name": "White Lily",
        "role": "Природа / АОЕ",
        "color": (240, 240, 240),
        "file": "white_lily.png",
    },
    {
        "name": "Hollyberry",
        "role": "Танк",
        "color": (231, 76, 60),
        "file": "hollyberry.png",
    },  # Она последняя в списке, значит на поле будет правее всех (ближе к боссу)
]


class Hero:

    def __init__(self, index, data):
        self.index = index
        self.name = data["name"]
        self.role = data["role"]
        self.max_hp = 150
        self.hp = 150

        # Если это Hollyberry (последний индекс 4), ставим её ближе к врагам справа
        if self.name == "Hollyberry":
            self.x = 420
        else:
            self.x = 100 + index * 70

        self.y = 380
        self.cooldown_max = 7.0
        self.cooldown_timer = 0.0

        try:
            self.image = pygame.image.load(data["file"]).convert_alpha()
            self.image = pygame.transform.scale(self.image, (60, 60))
        except:
            self.image = pygame.Surface((60, 60))
            self.image.fill(data["color"])

    def update(self, dt):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer < 0:
                self.cooldown_timer = 0.0

    def use_skill(self, enemies, heroes, game_effects):
        if self.hp <= 0:
            return False
        if self.cooldown_timer > 0:
            return False

        self.cooldown_timer = self.cooldown_max

        # Способности и их эффекты
        if self.name == "Pure Vanilla":
            for h in heroes:
                if h.hp > 0:
                    h.hp = h.max_hp
            game_effects["screen_flash"] = (YELLOW, 1.0)

        elif self.name == "Hollyberry":
            self.max_hp += 30
            self.hp = min(self.max_hp, self.hp + 30)
            game_effects["shield_timer"] = 3.0

        elif self.name == "Shadow Milk":
            for e in enemies:
                e.hp -= 40
                e.effect_color = BLUE
                e.effect_timer = 1.0

        elif self.name == "Eternal Sugar":
            if enemies:
                enemies[0].hp -= 70
                enemies[0].effect_color = PINK
                enemies[0].effect_timer = 1.0

        elif self.name == "White Lily":
            for e in enemies:
                e.hp -= 30
            game_effects["lily_blocks"] = 2.0

        return True

    def draw(self, surface):
        if self.hp <= 0:
            return
        surface.blit(self.image, (self.x - 30, self.y - 30))
        pygame.draw.rect(
            surface, RED, (self.x - 30, self.y - 45, 60, 6), border_radius=3
        )
        hp_w = max(0, int(60 * (self.hp / self.max_hp)))
        pygame.draw.rect(
            surface,
            GREEN,
            (self.x - 30, self.y - 45, hp_w, 6),
            border_radius=3,
        )


class Enemy:

    def __init__(self, x, hp, name="Монстр-торт", is_boss=False):
        self.name = name
        self.x = x
        self.y = 380
        self.max_hp = hp
        self.hp = hp
        self.is_boss = is_boss
        self.size = 90 if is_boss else 50
        self.damage = 15 if is_boss else 8
        self.attack_cooldown = 1.5
        self.attack_timer = self.attack_cooldown
        self.effect_color = None
        self.effect_timer = 0.0

    def update(self, dt, heroes, shield_active):
        if self.effect_timer > 0:
            self.effect_timer -= dt
            if self.effect_timer <= 0:
                self.effect_color = None

        if self.attack_timer > 0:
            self.attack_timer -= dt
        else:
            self.attack_timer = self.attack_cooldown
            current_damage = (
                self.damage // 2 if shield_active else self.damage
            )
            living_heroes = [h for h in heroes if h.hp > 0]
            for h in living_heroes:
                h.hp -= current_damage
                if h.hp < 0:
                    h.hp = 0

    def draw(self, surface):
        base_color = (
            self.effect_color
            if self.effect_color
            else ((139, 69, 19) if not self.is_boss else (180, 0, 0))
        )
        pygame.draw.rect(
            surface,
            base_color,
            (
                self.x - self.size // 2,
                self.y - self.size // 2,
                self.size,
                self.size,
            ),
            border_radius=8,
        )
        bar_w = self.size
        pygame.draw.rect(
            surface,
            RED,
            (self.x - bar_w // 2, self.y - self.size // 2 - 12, bar_w, 6),
            border_radius=3,
        )
        hp_w = max(0, int(bar_w * (self.hp / self.max_hp)))
        pygame.draw.rect(
            surface,
            GREEN,
            (self.x - bar_w // 2, self.y - self.size // 2 - 12, hp_w, 6),
            border_radius=3,
        )


class Game:

    def __init__(self):
        self.state = "MENU"
        self.stage = 1
        self.heroes = [Hero(i, data) for i, data in enumerate(HERO_DATA)]
        self.enemies = []
        self.effects = {
            "screen_flash": (None, 0.0),
            "shield_timer": 0.0,
            "lily_blocks": 0.0,
        }
        self.spawn_stage(1)

    def spawn_stage(self, stage_num):
        self.stage = stage_num
        self.enemies.clear()
        for h in self.heroes:
            h.max_hp = 150
            h.hp = 150
            h.cooldown_timer = 0.0

        self.effects = {
            "screen_flash": (None, 0.0),
            "shield_timer": 0.0,
            "lily_blocks": 0.0,
        }

        if stage_num == 1:
            self.enemies = [Enemy(700, 150, "Леденцовый Волк")]
        elif stage_num == 2:
            self.enemies = [
                Enemy(640, 180, "Желейный Медведь"),
                Enemy(740, 180, "Желейный Медведь"),
            ]
        elif stage_num == 3:
            self.enemies = [
                Enemy(720, 600, "Король Темного Торта (БОСС)", is_boss=True)
            ]

    def run(self):
        while True:
            dt = clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                if self.state == "MENU":
                    if 250 <= mx <= 650:
                        if 200 <= my <= 260:
                            self.spawn_stage(1)
                            self.state = "BATTLE"
                        elif 280 <= my <= 340:
                            self.spawn_stage(2)
                            self.state = "BATTLE"
                        elif 360 <= my <= 420:
                            self.spawn_stage(3)
                            self.state = "BATTLE"

                elif self.state in ["VICTORY", "DEFEAT"]:
                    if 350 <= mx <= 550 and 450 <= my <= 510:
                        self.state = "MENU"

                elif self.state == "BATTLE":
                    for i, h in enumerate(self.heroes):
                        hx = 150 + i * 120
                        hy = 520
                        if hx <= mx <= hx + 80 and hy <= my <= hy + 60:
                            h.use_skill(self.enemies, self.heroes, self.effects)

            if event.type == pygame.KEYDOWN and self.state == "BATTLE":
                key_map = {
                    pygame.K_1: 0,
                    pygame.K_2: 1,
                    pygame.K_3: 2,
                    pygame.K_4: 3,
                    pygame.K_5: 4,
                }
                if event.key in key_map:
                    idx = key_map[event.key]
                    self.heroes[idx].use_skill(
                        self.enemies, self.heroes, self.effects
                    )

    def update(self, dt):
        if self.state != "BATTLE":
            return

        if self.effects["screen_flash"][1] > 0:
            color, t = self.effects["screen_flash"]
            self.effects["screen_flash"] = (color, t - dt)

        if self.effects["shield_timer"] > 0:
            self.effects["shield_timer"] -= dt

        if self.effects["lily_blocks"] > 0:
            self.effects["lily_blocks"] -= dt

        for h in self.heroes:
            h.update(dt)

        shield_active = self.effects["shield_timer"] > 0
        for e in self.enemies:
            e.update(dt, self.heroes, shield_active)

        self.enemies = [e for e in self.enemies if e.hp > 0]

        if len(self.enemies) == 0:
            self.state = "VICTORY"

        if all(h.hp <= 0 for h in self.heroes):
            self.state = "DEFEAT"

    def draw(self):
        screen.fill((40, 30, 60))

        if self.state == "MENU":
            title = font_big.render("5V5 PYTHON", True, GOLD)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

            pygame.draw.rect(
                screen, (70, 50, 90), (250, 200, 400, 60), border_radius=10
            )
            t1 = font.render("1 рівень", True, WHITE)
            screen.blit(t1, (270, 218))

            pygame.draw.rect(
                screen, (70, 50, 90), (250, 280, 400, 60), border_radius=10
            )
            t2 = font.render("2 рівень", True, WHITE)
            screen.blit(t2, (270, 298))

            pygame.draw.rect(
                screen, (90, 30, 30), (250, 360, 400, 60), border_radius=10
            )
            t3 = font.render("3 рівень: Темна цитадель", True, (255, 100, 100))
            screen.blit(t3, (270, 378))

        elif self.state == "BATTLE":
            pygame.draw.rect(screen, (50, 40, 70), (0, 300, WIDTH, 200))

            stage_txt = font.render(f"Рівень: {self.stage} / 3", True, GOLD)
            screen.blit(stage_txt, (20, 20))

            for h in self.heroes:
                h.draw(screen)

            for e in self.enemies:
                e.draw(screen)

            # Зеленые блоки от White Lily рядом с врагами
            if self.effects["lily_blocks"] > 0:
                for e in self.enemies:
                    pygame.draw.rect(
                        screen,
                        (46, 204, 113),
                        (e.x - 40, e.y + 30, 20, 20),
                        border_radius=4,
                    )
                    pygame.draw.rect(
                        screen,
                        (39, 174, 96),
                        (e.x + 20, e.y + 30, 20, 20),
                        border_radius=4,
                    )

            # Щит Hollyberry прямо перед ней (ближе к боссу)
            if self.effects["shield_timer"] > 0:
                shield_surf = pygame.Surface((30, 100), pygame.SRCALPHA)
                shield_surf.fill((52, 152, 219, 120))
                screen.blit(shield_surf, (470, 330))

            pygame.draw.rect(screen, (20, 15, 30), (0, 500, WIDTH, 100))
            for i, h in enumerate(self.heroes):
                hx = 150 + i * 120
                hy = 515

                box_color = (
                    (50, 50, 50)
                    if h.hp <= 0
                    else (
                        (80, 80, 80) if h.cooldown_timer > 0 else (100, 180, 100)
                    )
                )
                pygame.draw.rect(
                    screen, box_color, (hx, hy, 70, 70), border_radius=8
                )
                screen.blit(
                    pygame.transform.scale(h.image, (50, 50)), (hx + 10, hy + 10)
                )

                if h.hp <= 0:
                    dead_overlay = pygame.Surface((70, 70), pygame.SRCALPHA)
                    dead_overlay.fill((0, 0, 0, 200))
                    screen.blit(dead_overlay, (hx, hy))
                    dead_txt = font.render("☠", True, RED)
                    screen.blit(
                        dead_txt, (hx + 35 - dead_txt.get_width() // 2, hy + 25)
                    )
                elif h.cooldown_timer > 0:
                    overlay = pygame.Surface((70, 70), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    screen.blit(overlay, (hx, hy))

                    cd_text = font.render(
                        f"{h.cooldown_timer:.1f}s", True, WHITE
                    )
                    screen.blit(
                        cd_text, (hx + 35 - cd_text.get_width() // 2, hy + 25)
                    )

                name_lbl = font.render(h.name.split()[0], True, WHITE)
                screen.blit(
                    name_lbl, (hx + 35 - name_lbl.get_width() // 2, hy + 75)
                )

            # Вспышка экрана
            flash_color, flash_t = self.effects["screen_flash"]
            if flash_t > 0 and flash_color:
                flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash_surf.fill((*flash_color, 80))
                screen.blit(flash_surf, (0, 0))

        elif self.state in ["VICTORY", "DEFEAT"]:
            text = (
                "ПЕРЕМОГА!" if self.state == "VICTORY" else "ПОРАЗКА..."
            )
            color = GREEN if self.state == "VICTORY" else RED
            res_surf = font_big.render(text, True, color)
            screen.blit(
                res_surf, (WIDTH // 2 - res_surf.get_width() // 2, 200)
            )

            pygame.draw.rect(
                screen, (70, 70, 90), (350, 450, 200, 60), border_radius=10
            )
            btn_txt = font.render("В меню", True, WHITE)
            screen.blit(
                btn_txt,
                (
                    450 - btn_txt.get_width() // 2,
                    480 - btn_txt.get_height() // 2,
                ),
            )

        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()
