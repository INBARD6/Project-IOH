# pygame_game.py
import sys
import random
import pygame

from repository import Repository
from fighter import Fighter
from striker import Striker
from grappler import Grappler
from hybrid_champion import HybridChampion

# Optional: Ollama
try:
    from ollama_client import OllamaClient
except Exception:
    OllamaClient = None


# -----------------------------
# Config
# -----------------------------
WIDTH, HEIGHT = 1280, 720
FPS = 60

LEFT_W = 420
PADDING = 18

LIST_X = PADDING
LIST_Y = 90
LIST_W = LEFT_W - 2 * PADDING
LIST_H = HEIGHT - LIST_Y - 170

RIGHT_X = LEFT_W + PADDING
RIGHT_W = WIDTH - RIGHT_X - PADDING

TOP_PANEL_H = 260
LOG_H = 170

# Colors (more colorful but still clean)
BG = (14, 16, 22)
PANEL = (24, 28, 40)
PANEL_2 = (20, 24, 34)
BORDER = (70, 78, 105)
TEXT = (238, 240, 255)
MUTED = (165, 175, 205)
ACCENT = (120, 170, 255)
ACCENT_2 = (255, 160, 120)
GOOD = (110, 230, 170)
WARN = (255, 220, 120)
BAD = (255, 120, 140)

BTN_BG = (34, 40, 58)
BTN_HOVER = (44, 52, 78)
BTN_BORDER = (100, 115, 170)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def fighter_style_name(f: Fighter) -> str:
    if isinstance(f, HybridChampion):
        return "Hybrid"
    if isinstance(f, Striker):
        return "Striker"
    if isinstance(f, Grappler):
        return "Grappler"
    return "Fighter"


def calc_damage(attacker: Fighter, move: str) -> int:
    """
    Simple arcade damage formula based on existing stats in your classes.
    move: 'jab' | 'kick' | 'grapple'
    """
    sp = getattr(attacker, "striking_power", 50)
    gr = getattr(attacker, "grappling_skill", 50)
    kick = getattr(attacker, "kick_power", sp)
    sub = getattr(attacker, "submission_skill", gr)

    if move == "jab":
        base = 6 + int(sp * 0.10)
        return clamp(base + random.randint(-2, 4), 3, 22)

    if move == "kick":
        base = 7 + int(kick * 0.10)
        return clamp(base + random.randint(-3, 5), 4, 26)

    if move == "grapple":
        base = 6 + int((gr * 0.07) + (sub * 0.06))
        return clamp(base + random.randint(-2, 6), 4, 24)

    return 8


def choose_ai_move(f: Fighter, enemy_hp: int, my_hp: int) -> str:
    sp = getattr(f, "striking_power", 50)
    gr = getattr(f, "grappling_skill", 50)
    kick = getattr(f, "kick_power", sp)

    # If low HP -> sometimes rest or block
    if my_hp <= 25 and random.random() < 0.35:
        return "rest"
    if my_hp <= 35 and random.random() < 0.25:
        return "block"

    # Prefer strongest domain
    if gr > sp + 10 and random.random() < 0.6:
        return "grapple"
    if kick >= sp and random.random() < 0.55:
        return "kick"
    return "jab"


def hp_color(percent: float):
    # gradient-ish: green -> yellow -> red
    if percent >= 0.66:
        return GOOD
    if percent >= 0.33:
        return WARN
    return BAD


# -----------------------------
# UI Widgets
# -----------------------------
class Button:
    def __init__(self, rect, text, font, key_hint=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.key_hint = key_hint

    def draw(self, screen, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        bg = BTN_HOVER if hovered else BTN_BG
        pygame.draw.rect(screen, bg, self.rect, border_radius=12)
        pygame.draw.rect(screen, BTN_BORDER, self.rect, width=2, border_radius=12)

        label = self.font.render(self.text, True, TEXT)
        screen.blit(label, label.get_rect(center=(self.rect.centerx, self.rect.centery)))

        if self.key_hint:
            hint = self.font.render(self.key_hint, True, MUTED)
            screen.blit(hint, (self.rect.right - hint.get_width() - 10, self.rect.top + 8))

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class TextInput:
    def __init__(self, rect, font, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.placeholder = placeholder
        self.text = ""
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return "submit"
            else:
                # simple input filter
                if len(self.text) < 22 and event.unicode.isprintable():
                    self.text += event.unicode
        return None

    def draw(self, screen):
        bg = (30, 36, 52) if self.active else (26, 30, 44)
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        pygame.draw.rect(screen, BTN_BORDER, self.rect, width=2, border_radius=10)

        show = self.text if self.text else self.placeholder
        color = TEXT if self.text else MUTED
        label = self.font.render(show, True, color)
        screen.blit(label, (self.rect.x + 10, self.rect.y + 10))


def draw_panel(screen, rect, title, title_font, fill=PANEL):
    pygame.draw.rect(screen, fill, rect, border_radius=16)
    pygame.draw.rect(screen, BORDER, rect, width=2, border_radius=16)
    if title:
        t = title_font.render(title, True, TEXT)
        screen.blit(t, (rect.x + 14, rect.y + 10))


def draw_bar(screen, x, y, w, h, label, current, maximum, font):
    pct = 0.0 if maximum <= 0 else clamp(current / maximum, 0.0, 1.0)
    pygame.draw.rect(screen, (18, 20, 30), (x, y, w, h), border_radius=10)
    pygame.draw.rect(screen, BORDER, (x, y, w, h), width=2, border_radius=10)

    fill_w = int((w - 4) * pct)
    pygame.draw.rect(screen, hp_color(pct), (x + 2, y + 2, fill_w, h - 4), border_radius=10)

    txt = f"{label}: {current}/{maximum}"
    label_surf = font.render(txt, True, TEXT)
    screen.blit(label_surf, (x, y - 22))


# -----------------------------
# Game / Scenes
# -----------------------------
class UFCGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("UFC Game (Pygame)")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(None, 22)
        self.font_md = pygame.font.SysFont(None, 26)
        self.font_big = pygame.font.SysFont(None, 34)
        self.font_title = pygame.font.SysFont(None, 44)

        self.repo = Repository()
        self.fighters = self.repo.get_all_fighters()

        self.ollama = None
        if OllamaClient is not None:
            self.ollama = OllamaClient()

        self.scene = "select"  # select | create | fight
        self.log = ["Welcome! If list is empty, click 'Add Sample Fighters'."]
        self.max_log = 9

        # Selection scene state
        self.scroll = 0
        self.active_slot = "A"  # A or B
        self.fighter_a = None
        self.fighter_b = None

        # Create scene state
        self.create_name = TextInput((RIGHT_X + 30, 150, 420, 46), self.font_md, placeholder="Type fighter name...")
        self.create_weight_index = 3
        self.create_style_index = 0
        self.weight_classes = [
            "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
            "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
        ]
        self.styles = ["Striker", "Grappler", "Hybrid"]

        # Fight scene state
        self.reset_fight_runtime()

        # Buttons (Select)
        bx = RIGHT_X + RIGHT_W - 300
        by = 110
        self.btn_fight = Button((bx, by, 280, 52), "Start Fight", self.font_big, key_hint="ENTER")
        self.btn_seed = Button((bx, by + 70, 280, 46), "Add Sample Fighters", self.font_md)
        self.btn_random = Button((bx, by + 128, 280, 46), "Create Random Fighter", self.font_md)
        self.btn_create = Button((bx, by + 186, 280, 46), "Create Custom Fighter", self.font_md)
        self.btn_ai = Button((bx, by + 244, 280, 46), "AI Matchup (Ollama)", self.font_md)
        self.btn_refresh = Button((bx, by + 302, 280, 46), "Refresh Fighters", self.font_md)
        self.btn_quit = Button((bx, by + 360, 280, 46), "Quit", self.font_md, key_hint="ESC")

        # Buttons (Create)
        self.btn_create_save = Button((RIGHT_X + 30, 330, 220, 46), "Save Fighter", self.font_md)
        self.btn_create_back = Button((RIGHT_X + 270, 330, 220, 46), "Back", self.font_md)

        # Buttons (Fight)
        self.btn_fight_back = Button((RIGHT_X + RIGHT_W - 240, 92, 220, 44), "Back to Select", self.font_md)
        self.btn_fight_restart = Button((RIGHT_X + RIGHT_W - 240, 144, 220, 44), "Restart Fight", self.font_md)

        if not self.fighters:
            self.push_log("DB has no fighters yet. Click 'Add Sample Fighters'.")

    def reset_fight_runtime(self):
        self.fight_hp_a = 100
        self.fight_hp_b = 100
        self.block_a = False
        self.block_b = False
        self.turn = "A"  # A then B
        self.fight_over = False
        self.fight_winner = None
        self.fight_method = None

    def push_log(self, text: str):
        for line in str(text).splitlines():
            line = line.strip()
            if line:
                self.log.append(line)
        self.log = self.log[-self.max_log :]

    # -----------------------------
    # Data helpers
    # -----------------------------
    def refresh(self):
        self.fighters = self.repo.get_all_fighters()
        self.scroll = clamp(self.scroll, 0, max(0, len(self.fighters) - 15))

    def next_fighter_id(self) -> int:
        if not self.fighters:
            return 1
        return max(f.fighter_id for f in self.fighters) + 1

    def add_sample_fighters(self):
        base_id = self.next_fighter_id()
        sample = [
            Striker(base_id, "Alex Blaze", "Lightweight", striking_power=88, grappling_skill=42, speed=82, kick_power=77),
            Grappler(base_id + 1, "Bruno Lock", "Welterweight", striking_power=45, grappling_skill=86, submission_skill=82, takedown_defense=74),
            HybridChampion(base_id + 2, "Carter Prime", "Middleweight", striking_power=78, grappling_skill=78, speed=74, kick_power=72,
                          submission_skill=71, takedown_defense=73, versatility=88),
            Striker(base_id + 3, "Dani Storm", "Featherweight", striking_power=84, grappling_skill=48, speed=86, kick_power=80),
            Grappler(base_id + 4, "Eli Grip", "Lightweight", striking_power=42, grappling_skill=83, submission_skill=79, takedown_defense=76),
            HybridChampion(base_id + 5, "Noah Apex", "Heavyweight", striking_power=80, grappling_skill=75, speed=62, kick_power=70,
                          submission_skill=68, takedown_defense=69, versatility=84),
        ]

        added = 0
        for f in sample:
            if self.repo.add_fighter(f):
                added += 1

        self.refresh()
        self.push_log(f"Added {added} sample fighters.")

    def create_random_fighter(self):
        fid = self.next_fighter_id()
        wc = random.choice(self.weight_classes)
        base_name = random.choice(["Rogue", "Viper", "Titan", "Shadow", "Havoc", "Nova", "Blitz", "Phantom"])
        name = f"{base_name} #{fid}"
        style = random.choice(self.styles)

        if style == "Striker":
            f = Striker(fid, name, wc,
                        striking_power=random.randint(70, 95),
                        grappling_skill=random.randint(25, 55),
                        speed=random.randint(65, 95),
                        kick_power=random.randint(60, 95))
        elif style == "Grappler":
            f = Grappler(fid, name, wc,
                         striking_power=random.randint(25, 60),
                         grappling_skill=random.randint(70, 95),
                         submission_skill=random.randint(65, 95),
                         takedown_defense=random.randint(55, 90))
        else:
            f = HybridChampion(fid, name, wc,
                               striking_power=random.randint(60, 90),
                               grappling_skill=random.randint(60, 90),
                               speed=random.randint(55, 85),
                               kick_power=random.randint(55, 85),
                               submission_skill=random.randint(55, 85),
                               takedown_defense=random.randint(55, 85),
                               versatility=random.randint(70, 95))

        ok = self.repo.add_fighter(f)
        self.refresh()
        self.push_log(f"Created: {f.name} ({fighter_style_name(f)}, {wc})" if ok else "Failed to create fighter.")
        return ok

    def save_custom_fighter(self):
        name = self.create_name.text.strip()
        if not name:
            self.push_log("Name is required.")
            return False

        fid = self.next_fighter_id()
        wc = self.weight_classes[self.create_weight_index]
        style = self.styles[self.create_style_index]

        # Generate reasonable stats (you can tweak later)
        if style == "Striker":
            f = Striker(fid, name, wc,
                        striking_power=random.randint(70, 92),
                        grappling_skill=random.randint(25, 55),
                        speed=random.randint(65, 95),
                        kick_power=random.randint(60, 95))
        elif style == "Grappler":
            f = Grappler(fid, name, wc,
                         striking_power=random.randint(25, 60),
                         grappling_skill=random.randint(70, 92),
                         submission_skill=random.randint(65, 95),
                         takedown_defense=random.randint(55, 90))
        else:
            f = HybridChampion(fid, name, wc,
                               striking_power=random.randint(60, 88),
                               grappling_skill=random.randint(60, 88),
                               speed=random.randint(55, 85),
                               kick_power=random.randint(55, 85),
                               submission_skill=random.randint(55, 85),
                               takedown_defense=random.randint(55, 85),
                               versatility=random.randint(70, 95))

        ok = self.repo.add_fighter(f)
        self.refresh()
        self.push_log(f"Saved: {f.name} ({fighter_style_name(f)}, {wc})" if ok else "Failed to save fighter.")
        return ok

    # -----------------------------
    # Drawing helpers
    # -----------------------------
    def draw_header(self):
        title = self.font_title.render("UFC Game", True, TEXT)
        self.screen.blit(title, (PADDING, 22))

        hint = "TAB: switch A/B  |  ENTER: start fight  |  ESC: quit"
        h = self.font_md.render(hint, True, MUTED)
        self.screen.blit(h, (PADDING, 62))

    def draw_log_panel(self):
        rect = pygame.Rect(PADDING, HEIGHT - LOG_H - PADDING, WIDTH - 2 * PADDING, LOG_H)
        draw_panel(self.screen, rect, "Log", self.font_md, fill=PANEL_2)

        y = rect.y + 44
        for ln in self.log:
            t = self.font.render(ln[:140], True, TEXT)
            self.screen.blit(t, (rect.x + 14, y))
            y += 18

    def draw_fighter_list(self, mouse_pos):
        rect = pygame.Rect(LIST_X, LIST_Y, LIST_W, LIST_H)
        draw_panel(self.screen, rect, "Fighters (click to select)", self.font_md)

        if not self.fighters:
            msg = self.font_md.render("No fighters in DB.", True, MUTED)
            self.screen.blit(msg, (rect.x + 16, rect.y + 70))
            msg2 = self.font.render("Click 'Add Sample Fighters' or create one.", True, MUTED)
            self.screen.blit(msg2, (rect.x + 16, rect.y + 98))
            return

        visible = 15
        start = int(self.scroll)
        end = min(len(self.fighters), start + visible)

        item_h = 34
        y = rect.y + 52
        for idx in range(start, end):
            f = self.fighters[idx]
            r = pygame.Rect(rect.x + 12, y, rect.w - 24, item_h - 4)

            selected = (self.fighter_a and f.fighter_id == self.fighter_a.fighter_id) or \
                       (self.fighter_b and f.fighter_id == self.fighter_b.fighter_id)

            bg = (34, 40, 58) if selected else (28, 32, 46)
            pygame.draw.rect(self.screen, bg, r, border_radius=10)

            # hover outline
            if r.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, ACCENT, r, width=2, border_radius=10)
            else:
                pygame.draw.rect(self.screen, BTN_BORDER, r, width=1, border_radius=10)

            style = fighter_style_name(f)
            txt = f"{f.name}  |  {style}  |  {f.weight_class}  |  {f.wins}-{f.losses}-{f.draws}"
            t = self.font.render(txt[:70], True, TEXT)
            self.screen.blit(t, (r.x + 10, r.y + 8))

            y += item_h

        # scroll hint
        hint = self.font.render("Mouse wheel to scroll list", True, MUTED)
        self.screen.blit(hint, (rect.x + 16, rect.bottom - 28))

    def fighter_from_click(self, pos):
        rect = pygame.Rect(LIST_X, LIST_Y, LIST_W, LIST_H)
        if not rect.collidepoint(pos):
            return None
        if not self.fighters:
            return None

        item_h = 34
        top_y = rect.y + 52
        x, y = pos
        if y < top_y:
            return None

        row = (y - top_y) // item_h
        idx = int(self.scroll) + row
        if 0 <= idx < len(self.fighters):
            return self.fighters[idx]
        return None

    def draw_fighter_card(self, fighter, rect, title):
        draw_panel(self.screen, rect, title, self.font_md)

        if fighter is None:
            t = self.font_md.render("Not selected", True, MUTED)
            self.screen.blit(t, (rect.x + 14, rect.y + 70))
            return

        style = fighter_style_name(fighter)
        lines = [
            f"Name: {fighter.name}",
            f"Style: {style}",
            f"Weight: {fighter.weight_class}",
            f"Record: {fighter.wins}-{fighter.losses}-{fighter.draws}",
            f"Striking: {fighter.striking_power}   Grappling: {fighter.grappling_skill}",
            f"Overall: {fighter.overall_skill:.1f}",
        ]
        y = rect.y + 52
        for ln in lines:
            t = self.font.render(ln, True, TEXT)
            self.screen.blit(t, (rect.x + 14, y))
            y += 20

    # -----------------------------
    # Scenes
    # -----------------------------
    def scene_select_draw(self, mouse_pos):
        self.screen.fill(BG)
        self.draw_header()

        # Left list
        self.draw_fighter_list(mouse_pos)

        # Right top panels
        top_rect = pygame.Rect(RIGHT_X, LIST_Y, RIGHT_W, TOP_PANEL_H)
        draw_panel(self.screen, top_rect, "Selection", self.font_md)

        slot_txt = f"Selecting for: Fighter {self.active_slot} (TAB to switch)"
        t = self.font_md.render(slot_txt, True, ACCENT)
        self.screen.blit(t, (top_rect.x + 14, top_rect.y + 52))

        # Cards
        card_w = (RIGHT_W - 3 * 14) // 2
        card_h = 150
        rect_a = pygame.Rect(top_rect.x + 14, top_rect.y + 90, card_w, card_h)
        rect_b = pygame.Rect(top_rect.x + 28 + card_w, top_rect.y + 90, card_w, card_h)

        self.draw_fighter_card(self.fighter_a, rect_a, "Fighter A")
        self.draw_fighter_card(self.fighter_b, rect_b, "Fighter B")

        # Buttons column (right side inside top_rect)
        bx = top_rect.right - 300
        by = top_rect.y + 20
        self.btn_fight.rect.topleft = (bx, by)
        self.btn_seed.rect.topleft = (bx, by + 70)
        self.btn_random.rect.topleft = (bx, by + 128)
        self.btn_create.rect.topleft = (bx, by + 186)
        self.btn_ai.rect.topleft = (bx, by + 244)
        self.btn_refresh.rect.topleft = (bx, by + 302)
        self.btn_quit.rect.topleft = (bx, by + 360)

        self.btn_fight.draw(self.screen, mouse_pos)
        self.btn_seed.draw(self.screen, mouse_pos)
        self.btn_random.draw(self.screen, mouse_pos)
        self.btn_create.draw(self.screen, mouse_pos)
        self.btn_ai.draw(self.screen, mouse_pos)
        self.btn_refresh.draw(self.screen, mouse_pos)
        self.btn_quit.draw(self.screen, mouse_pos)

        # Bottom log
        self.draw_log_panel()

    def scene_create_draw(self, mouse_pos):
        self.screen.fill(BG)
        self.draw_header()

        rect = pygame.Rect(RIGHT_X, LIST_Y, RIGHT_W, HEIGHT - LIST_Y - LOG_H - 2 * PADDING)
        draw_panel(self.screen, rect, "Create Fighter", self.font_md)

        # Instructions
        self.screen.blit(self.font.render("Click name field and type. Choose weight & style. Then Save.", True, MUTED),
                         (rect.x + 18, rect.y + 60))

        # Name input
        self.screen.blit(self.font_md.render("Name:", True, TEXT), (rect.x + 18, rect.y + 104))
        self.create_name.draw(self.screen)

        # Weight & style pickers
        wc = self.weight_classes[self.create_weight_index]
        st = self.styles[self.create_style_index]

        self.screen.blit(self.font_md.render(f"Weight class: {wc}", True, TEXT), (rect.x + 18, rect.y + 220))
        self.screen.blit(self.font.render("Use LEFT/RIGHT arrows to change", True, MUTED), (rect.x + 18, rect.y + 246))

        self.screen.blit(self.font_md.render(f"Style: {st}", True, TEXT), (rect.x + 18, rect.y + 280))
        self.screen.blit(self.font.render("Use UP/DOWN arrows to change", True, MUTED), (rect.x + 18, rect.y + 306))

        # Buttons
        self.btn_create_save.draw(self.screen, mouse_pos)
        self.btn_create_back.draw(self.screen, mouse_pos)

        # Bottom log
        self.draw_log_panel()

    def start_fight_scene(self):
        if not self.fighter_a or not self.fighter_b:
            self.push_log("Pick TWO fighters first.")
            return
        if self.fighter_a.fighter_id == self.fighter_b.fighter_id:
            self.push_log("Choose two different fighters.")
            return

        self.reset_fight_runtime()
        self.scene = "fight"
        self.push_log(f"Fight started: {self.fighter_a.name} vs {self.fighter_b.name}")
        self.push_log("Controls: 1=Jab  2=Kick  3=Grapple  4=Block  5=Rest")

    def end_fight(self, winner: str, method: str):
        self.fight_over = True
        self.fight_winner = winner
        self.fight_method = method

        # Update records + save fight in DB
        if self.fighter_a and self.fighter_b:
            if winner == self.fighter_a.name:
                self.fighter_a.add_win()
                self.fighter_b.add_loss()
            elif winner == self.fighter_b.name:
                self.fighter_b.add_win()
                self.fighter_a.add_loss()

            self.repo.update_fighter(self.fighter_a)
            self.repo.update_fighter(self.fighter_b)

            fight_result = {
                "fighter1": self.fighter_a.name,
                "fighter2": self.fighter_b.name,
                "winner": winner,
                "method": method,
                "fighter1_score": float(self.fight_hp_a),
                "fighter2_score": float(self.fight_hp_b),
            }
            self.repo.save_fight_result(fight_result)

        self.push_log(f"🏆 Winner: {winner} ({method})")
        self.push_log("Fight saved + records updated in DB.")
        self.refresh()

    def apply_move(self, attacker: str, move: str):
        if self.fight_over:
            return

        A = self.fighter_a
        B = self.fighter_b
        if not A or not B:
            return

        if attacker == "A":
            atk, defn = A, B
            def_hp = self.fight_hp_b
            atk_name, def_name = A.name, B.name
            blocked = self.block_b
        else:
            atk, defn = B, A
            def_hp = self.fight_hp_a
            atk_name, def_name = B.name, A.name
            blocked = self.block_a

        # Resolve special moves
        if move == "block":
            if attacker == "A":
                self.block_a = True
            else:
                self.block_b = True
            self.push_log(f"{atk_name} blocks (reduces next hit).")
            return

        if move == "rest":
            heal = random.randint(6, 10)
            if attacker == "A":
                self.fight_hp_a = clamp(self.fight_hp_a + heal, 0, 100)
            else:
                self.fight_hp_b = clamp(self.fight_hp_b + heal, 0, 100)
            self.push_log(f"{atk_name} rests (+{heal} HP).")
            return

        # Attack move
        dmg = calc_damage(atk, move)

        if blocked:
            dmg = max(1, int(dmg * 0.45))
            if attacker == "A":
                self.block_b = False
            else:
                self.block_a = False
            self.push_log(f"{def_name} partially blocks!")

        def_hp -= dmg
        def_hp = clamp(def_hp, 0, 100)

        move_name = {"jab": "Jab", "kick": "Kick", "grapple": "Grapple"}.get(move, move)
        self.push_log(f"{atk_name} uses {move_name} (-{dmg} HP)")

        # Write back
        if attacker == "A":
            self.fight_hp_b = def_hp
        else:
            self.fight_hp_a = def_hp

        # Check KO
        if self.fight_hp_a <= 0 and self.fight_hp_b <= 0:
            # Rare double KO – choose draw-ish
            self.end_fight("Draw", "Double KO")
        elif self.fight_hp_a <= 0:
            self.end_fight(B.name, "KO")
        elif self.fight_hp_b <= 0:
            self.end_fight(A.name, "KO")

    def fight_tick_ai(self):
        if self.fight_over:
            return
        if self.turn != "B":
            return

        move = choose_ai_move(self.fighter_b, self.fight_hp_a, self.fight_hp_b)
        self.apply_move("B", move)
        self.turn = "A"

    def scene_fight_draw(self, mouse_pos):
        self.screen.fill(BG)
        self.draw_header()

        rect = pygame.Rect(PADDING, LIST_Y, WIDTH - 2 * PADDING, HEIGHT - LIST_Y - LOG_H - 2 * PADDING)
        draw_panel(self.screen, rect, "Fight", self.font_md)

        # Buttons
        self.btn_fight_back.rect.topleft = (rect.right - 240, rect.y + 18)
        self.btn_fight_restart.rect.topleft = (rect.right - 240, rect.y + 70)
        self.btn_fight_back.draw(self.screen, mouse_pos)
        self.btn_fight_restart.draw(self.screen, mouse_pos)

        if not self.fighter_a or not self.fighter_b:
            self.push_log("Missing fighters. Back to select.")
            self.scene = "select"
            return

        # Fighter names
        a_name = self.font_big.render(self.fighter_a.name, True, ACCENT)
        b_name = self.font_big.render(self.fighter_b.name, True, ACCENT_2)
        self.screen.blit(a_name, (rect.x + 20, rect.y + 60))
        self.screen.blit(b_name, (rect.x + 20, rect.y + 140))

        # HP bars
        draw_bar(self.screen, rect.x + 20, rect.y + 95, 560, 20, "Fighter A HP", self.fight_hp_a, 100, self.font)
        draw_bar(self.screen, rect.x + 20, rect.y + 175, 560, 20, "Fighter B HP", self.fight_hp_b, 100, self.font)

        # Turn / controls panel
        ctrl = pygame.Rect(rect.x + 620, rect.y + 55, rect.w - 620 - 20, 190)
        draw_panel(self.screen, ctrl, "Controls", self.font_md, fill=PANEL_2)

        lines = [
            "1 = Jab (strike)",
            "2 = Kick (strong strike)",
            "3 = Grapple (wrestle/submission)",
            "4 = Block (reduce next hit)",
            "5 = Rest (+HP)",
            "",
            f"Turn: {'You (A)' if self.turn == 'A' else 'AI (B)'}",
        ]
        y = ctrl.y + 52
        for ln in lines:
            t = self.font.render(ln, True, TEXT if ln else MUTED)
            self.screen.blit(t, (ctrl.x + 14, y))
            y += 20

        # Result line
        if self.fight_over:
            res = f"RESULT: {self.fight_winner} — {self.fight_method}"
            t = self.font_big.render(res, True, GOOD)
            self.screen.blit(t, (rect.x + 20, rect.y + 240))

        # Bottom log
        self.draw_log_panel()

    # -----------------------------
    # AI (Ollama)
    # -----------------------------
    def run_ollama_matchup(self):
        if self.ollama is None:
            self.push_log("Ollama client not available (import failed).")
            return
        if not self.fighter_a or not self.fighter_b:
            self.push_log("Pick two fighters first for AI matchup.")
            return
        if not self.ollama.is_available():
            self.push_log("Ollama server not available. Start it and try again.")
            return

        s1 = fighter_style_name(self.fighter_a)
        s2 = fighter_style_name(self.fighter_b)
        self.push_log("AI is generating matchup analysis...")
        analysis = self.ollama.generate_fighter_matchup_analysis(
            self.fighter_a.name, self.fighter_b.name, s1, s2
        )
        self.push_log(analysis)

    # -----------------------------
    # Main loop
    # -----------------------------
    def handle_select_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.active_slot = "B" if self.active_slot == "A" else "A"
                self.push_log(f"Selecting for Fighter {self.active_slot}")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.start_fight_scene()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y
            self.scroll = clamp(self.scroll, 0, max(0, len(self.fighters) - 15))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            f = self.fighter_from_click(event.pos)
            if f:
                if self.active_slot == "A":
                    self.fighter_a = f
                    self.push_log(f"Selected A: {f.name}")
                else:
                    self.fighter_b = f
                    self.push_log(f"Selected B: {f.name}")

        # Buttons
        if self.btn_quit.clicked(event):
            pygame.quit()
            sys.exit()

        if self.btn_refresh.clicked(event):
            self.refresh()
            self.push_log("Refreshed fighters from DB.")

        if self.btn_seed.clicked(event):
            self.add_sample_fighters()

        if self.btn_random.clicked(event):
            self.create_random_fighter()

        if self.btn_create.clicked(event):
            self.scene = "create"
            self.push_log("Create mode: enter name, pick weight/style, then Save.")

        if self.btn_ai.clicked(event):
            self.run_ollama_matchup()

        if self.btn_fight.clicked(event):
            self.start_fight_scene()

    def handle_create_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.scene = "select"
                return
            if event.key == pygame.K_LEFT:
                self.create_weight_index = (self.create_weight_index - 1) % len(self.weight_classes)
            if event.key == pygame.K_RIGHT:
                self.create_weight_index = (self.create_weight_index + 1) % len(self.weight_classes)
            if event.key == pygame.K_UP:
                self.create_style_index = (self.create_style_index - 1) % len(self.styles)
            if event.key == pygame.K_DOWN:
                self.create_style_index = (self.create_style_index + 1) % len(self.styles)

        submit = self.create_name.handle_event(event)
        if submit == "submit":
            ok = self.save_custom_fighter()
            if ok:
                self.create_name.text = ""
                self.scene = "select"

        if self.btn_create_back.clicked(event):
            self.scene = "select"

        if self.btn_create_save.clicked(event):
            ok = self.save_custom_fighter()
            if ok:
                self.create_name.text = ""
                self.scene = "select"

    def handle_fight_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.scene = "select"
                return

            # Only allow player input on player's turn
            if self.turn == "A" and not self.fight_over:
                if event.key == pygame.K_1:
                    self.apply_move("A", "jab")
                    self.turn = "B"
                elif event.key == pygame.K_2:
                    self.apply_move("A", "kick")
                    self.turn = "B"
                elif event.key == pygame.K_3:
                    self.apply_move("A", "grapple")
                    self.turn = "B"
                elif event.key == pygame.K_4:
                    self.apply_move("A", "block")
                    self.turn = "B"
                elif event.key == pygame.K_5:
                    self.apply_move("A", "rest")
                    self.turn = "B"

        if self.btn_fight_back.clicked(event):
            self.scene = "select"

        if self.btn_fight_restart.clicked(event):
            self.reset_fight_runtime()
            self.push_log("Fight restarted.")
            self.push_log("Controls: 1=Jab  2=Kick  3=Grapple  4=Block  5=Rest")

    def run(self):
        while True:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.scene == "select":
                    self.handle_select_events(event)
                elif self.scene == "create":
                    self.handle_create_events(event)
                elif self.scene == "fight":
                    self.handle_fight_events(event)

            # AI turn tick
            if self.scene == "fight":
                self.fight_tick_ai()

            # Draw
            if self.scene == "select":
                self.scene_select_draw(mouse_pos)
            elif self.scene == "create":
                self.scene_create_draw(mouse_pos)
            elif self.scene == "fight":
                self.scene_fight_draw(mouse_pos)

            pygame.display.flip()


if __name__ == "__main__":
    UFCGame().run()
