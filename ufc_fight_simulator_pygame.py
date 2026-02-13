import pygame, sys, random, math, time, os, json, re
from dataclasses import dataclass

from repository import Repository
from fighter import Fighter
from striker import Striker
from grappler import Grappler
from hybrid_champion import HybridChampion

try:
    from ollama_client import OllamaClient
except Exception:
    OllamaClient = None

# ----------------- Config -----------------
WIDTH, HEIGHT = 1280, 720
FPS = 60
ASSETS_DIR = "assets"
HOME_IMAGE = os.path.join(ASSETS_DIR, "home_fighters.png")

# Colors
BG = (10, 10, 14)
PANEL = (18, 18, 26)
PANEL_2 = (22, 22, 32)
BORDER = (85, 85, 120)
TEXT = (240, 240, 255)
MUTED = (170, 170, 200)
RED = (235, 70, 85)
BLUE = (80, 150, 255)
YELLOW = (255, 210, 120)
GREEN = (95, 235, 170)

def clamp(v, lo, hi): return max(lo, min(hi, v))

def fighter_style(f: Fighter) -> str:
    if isinstance(f, HybridChampion): return "Hybrid"
    if isinstance(f, Striker): return "Striker"
    if isinstance(f, Grappler): return "Grappler"
    return "Fighter"

def get_stat(f: Fighter, name: str, default: int = 50) -> int:
    return int(getattr(f, name, default) or default)

def draw_rect_round(surf, rect, color, r=14, width=0):
    pygame.draw.rect(surf, color, rect, width=width, border_radius=r)

def draw_panel(surf, rect, title, font, fill=PANEL):
    draw_rect_round(surf, rect, fill, r=18)
    draw_rect_round(surf, rect, BORDER, r=18, width=2)
    if title:
        t = font.render(title, True, TEXT)
        surf.blit(t, (rect.x + 16, rect.y + 12))

def load_image(path, max_size=None):
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if max_size:
            w, h = img.get_size()
            mw, mh = max_size
            scale = min(mw / w, mh / h)
            if scale < 1:
                img = pygame.transform.smoothscale(img, (int(w*scale), int(h*scale)))
        return img
    except Exception:
        return None

class Button:
    def __init__(self, rect, text, font, accent=RED):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.accent = accent

    def draw(self, surf, mouse):
        hovered = self.rect.collidepoint(mouse)
        bg = (28, 28, 40) if not hovered else (38, 38, 56)
        draw_rect_round(surf, self.rect, bg, r=14)
        draw_rect_round(surf, self.rect, self.accent if hovered else BORDER, r=14, width=2)
        t = self.font.render(self.text, True, TEXT)
        surf.blit(t, t.get_rect(center=self.rect.center))

    def clicked(self, ev):
        return ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos)

@dataclass
class AppState:
    mode: str = "CPU"  # "CPU" or "2P"

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Fight Simulator")
        self.clock = pygame.time.Clock()

        self.font_s = pygame.font.SysFont(None, 20)
        self.font = pygame.font.SysFont(None, 26)
        self.font_b = pygame.font.SysFont(None, 36)
        self.font_title = pygame.font.SysFont(None, 64)

        self.home_img = load_image(HOME_IMAGE, max_size=(360, 260))

        self.repo = Repository()
        self.refresh_fighters()
        self.ollama = OllamaClient() if OllamaClient else None

        self.state = AppState()
        self.scene = "home"  # home/select/create/roster/fight/about
        self.log = ["Welcome! If no fighters appear, click Add Legends."]
        self.log_max = 6

        # selection
        self.sel_a = None
        self.sel_b = None
        self.scroll_a = 0
        self.scroll_b = 0

        # create
        self.create_name = ""
        self.create_weight_idx = 3
        self.create_type_idx = 0
        self.weight_classes = ["Flyweight","Bantamweight","Featherweight","Lightweight","Welterweight","Middleweight","Light Heavyweight","Heavyweight"]
        self.types = ["Striker","Grappler","Hybrid"]
        self.edit_stat_idx = 0
        self.stats_template = {"STR":70,"GRP":70,"SPD":70,"KICK":70,"SUB":70,"DEF":70,"VERS":70,"STA":70}
        self.stats = dict(self.stats_template)

        # roster
        self.roster_scroll = 0
        self.roster_selected = None
        self.roster_ai_text = ""

        # fight
        self.fight = None

        # home buttons - clear mode
        self.btn_vs_cpu = Button((WIDTH//2-260, 300, 520, 70), "PLAY VS CPU", self.font_b, accent=GREEN)
        self.btn_2p = Button((WIDTH//2-260, 385, 520, 70), "PLAY 2 PLAYERS", self.font_b, accent=BLUE)
        self.btn_roster = Button((WIDTH//2-260, 470, 520, 70), "FIGHTER ROSTER", self.font_b, accent=YELLOW)
        self.btn_about = Button((WIDTH//2-260, 555, 250, 60), "ABOUT", self.font_b, accent=(140,140,200))
        self.btn_exit = Button((WIDTH//2+10, 555, 250, 60), "EXIT", self.font_b, accent=(120,120,180))

        # select buttons
        self.btn_add_legends = Button((70, 620, 220, 52), "Add Legends", self.font, accent=RED)
        self.btn_create = Button((300, 620, 220, 52), "Create Fighter", self.font, accent=YELLOW)
        self.btn_start = Button((530, 620, 220, 52), "START FIGHT", self.font, accent=GREEN)
        self.btn_back = Button((760, 620, 160, 52), "Back", self.font, accent=(140,140,200))

        # create buttons
        self.btn_save = Button((920, 560, 260, 56), "SAVE", self.font_b, accent=GREEN)
        self.btn_create_back = Button((920, 630, 260, 56), "BACK", self.font_b, accent=(140,140,200))

        # roster buttons
        self.btn_roster_ai = Button((980, 120, 250, 50), "AI Stats (Ollama)", self.font, accent=YELLOW)
        self.btn_roster_back = Button((980, 180, 250, 50), "Back", self.font, accent=(140,140,200))

    def push_log(self, msg):
        for line in str(msg).splitlines():
            line = line.strip()
            if line:
                self.log.append(line)
        self.log = self.log[-self.log_max:]

    def refresh_fighters(self):
        self.fighters = self.repo.get_all_fighters()

    def next_id(self):
        if not self.fighters:
            return 1
        return max(f.fighter_id for f in self.fighters) + 1

    def add_legends(self):
        base = self.next_id()
        legends = [
            Grappler(base, "Khabib Nurmagomedov", "Lightweight", striking_power=78, grappling_skill=97, submission_skill=92, takedown_defense=90),
            Striker(base+1, "Conor McGregor", "Lightweight", striking_power=95, grappling_skill=65, speed=78, kick_power=86),
            HybridChampion(base+2, "Jon Jones", "Heavyweight", striking_power=92, grappling_skill=90, speed=78, kick_power=80, submission_skill=80, takedown_defense=93, versatility=92),
            HybridChampion(base+3, "Amanda Nunes", "Bantamweight", striking_power=93, grappling_skill=85, speed=82, kick_power=86, submission_skill=78, takedown_defense=82, versatility=88),
            Striker(base+4, "Anderson Silva", "Middleweight", striking_power=97, grappling_skill=78, speed=84, kick_power=95),
            HybridChampion(base+5, "Georges St-Pierre", "Welterweight", striking_power=88, grappling_skill=93, speed=84, kick_power=80, submission_skill=82, takedown_defense=92, versatility=90),
        ]
        added = 0
        for f in legends:
            if self.repo.add_fighter(f):
                added += 1
        self.refresh_fighters()
        self.push_log(f"Added {added} legends to DB.")

    # ----------------- HOME -----------------
    def draw_home(self, mouse):
        self.screen.fill(BG)

        # background vibe
        for i in range(0, 260, 10):
            col = (10+i//7, 8, 10)
            pygame.draw.rect(self.screen, col, (0, i, WIDTH, 10))

        sub = self.font.render("ULTIMATE FIGHTING CHAMPIONSHIP", True, MUTED)
        self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 70))

        title1 = self.font_title.render("FIGHT", True, TEXT)
        title2 = self.font_title.render("SIMULATOR", True, RED)
        self.screen.blit(title1, (WIDTH//2 - title1.get_width()//2, 110))
        self.screen.blit(title2, (WIDTH//2 - title2.get_width()//2, 165))

        self.btn_vs_cpu.draw(self.screen, mouse)
        self.btn_2p.draw(self.screen, mouse)
        self.btn_roster.draw(self.screen, mouse)
        self.btn_about.draw(self.screen, mouse)
        self.btn_exit.draw(self.screen, mouse)

        # bottom-left image
        self.draw_home_art()

        # team names (EN)
        names = "Inbar Dayan ; Or Higani ; Chen Turgeman"
        n = self.font_s.render(names, True, MUTED)
        self.screen.blit(n, (WIDTH - n.get_width() - 18, HEIGHT - 24))

    def draw_home_art(self):
        x, y = 26, HEIGHT - 260
        w, h = 360, 230
        frame = pygame.Rect(x, y, w, h)
        draw_rect_round(self.screen, frame, (16,16,24), r=18)
        draw_rect_round(self.screen, frame, (40,40,60), r=18, width=2)

        if self.home_img:
            img = self.home_img
            ix = x + 12
            iy = y + 12
            self.screen.blit(img, (ix, iy))
        else:
            # placeholder silhouette
            pygame.draw.circle(self.screen, (90, 90, 125), (x+120, y+90), 26)
            pygame.draw.circle(self.screen, (90, 90, 125), (x+240, y+90), 26)
            pygame.draw.rect(self.screen, (75, 75, 110), (x+98, y+118, 44, 80), border_radius=12)
            pygame.draw.rect(self.screen, (75, 75, 110), (x+218, y+118, 44, 80), border_radius=12)
            pygame.draw.circle(self.screen, RED, (x+168, y+160), 18)
            pygame.draw.circle(self.screen, RED, (x+192, y+160), 18)
            t = self.font_s.render("Put assets/home_fighters.png here", True, MUTED)
            self.screen.blit(t, (x+16, y+h-26))

    def handle_home(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

        if self.btn_vs_cpu.clicked(ev):
            self.state.mode = "CPU"
            self.scene = "select"
            self.push_log("Mode: VS CPU. Select two fighters.")
        elif self.btn_2p.clicked(ev):
            self.state.mode = "2P"
            self.scene = "select"
            self.push_log("Mode: 2 Players. Select two fighters.")
        elif self.btn_roster.clicked(ev):
            self.scene = "roster"
            self.roster_selected = None
            self.roster_ai_text = ""
        elif self.btn_about.clicked(ev):
            self.scene = "about"
        elif self.btn_exit.clicked(ev):
            pygame.quit(); sys.exit()

    # ----------------- ABOUT -----------------
    def draw_about(self, mouse):
        self.screen.fill(BG)
        rect = pygame.Rect(80, 90, WIDTH-160, HEIGHT-180)
        draw_panel(self.screen, rect, "About", self.font_b)
        lines = [
            "Fight Simulator (Pygame) - Real-time arena",
            "",
            "Home:",
            "• PLAY VS CPU  - Player controls Fighter 1 (Arrows), CPU controls Fighter 2",
            "• PLAY 2 PLAYERS - Two players: P1 Arrows, P2 WASD",
            "",
            "Fight Controls:",
            "P1: Move = Arrows | Actions = 1/2/3/4/5",
            "P2: Move = WASD  | Actions = 6/7/8/9/0",
            "Actions: 1/6 Jab, 2/7 Kick, 3/8 Grapple, 4/9 Block, 5/0 Rest",
            "",
            "Back: ESC",
        ]
        y = rect.y + 70
        for ln in lines:
            t = self.font.render(ln, True, TEXT if ln and not ln.startswith("•") else MUTED)
            self.screen.blit(t, (rect.x + 24, y)); y += 28

        self._about_back = Button((WIDTH-260, HEIGHT-120, 180, 50), "Back", self.font, accent=(140,140,200))
        self._about_back.draw(self.screen, mouse)

    def handle_about(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.scene = "home"
        if hasattr(self, "_about_back") and self._about_back.clicked(ev):
            self.scene = "home"

    # ----------------- SELECT -----------------
    def draw_select(self, mouse):
        self.screen.fill(BG)
        title = self.font_title.render("SELECT FIGHTERS", True, TEXT)
        self.screen.blit(title, (70, 60))

        mode_txt = "VS CPU" if self.state.mode == "CPU" else "2 PLAYERS"
        badge = self.font_b.render(f"MODE: {mode_txt}", True, GREEN if self.state.mode=="CPU" else BLUE)
        self.screen.blit(badge, (70, 120))

        hint1 = self.font.render("Pick Fighter 1 (left) and Fighter 2 (right), then press START FIGHT.", True, MUTED)
        self.screen.blit(hint1, (70, 150))

        if self.state.mode == "CPU":
            hint2 = self.font_s.render("Fight controls: Move=Arrows | 1 Jab 2 Kick 3 Grapple 4 Block 5 Rest", True, MUTED)
        else:
            hint2 = self.font_s.render("P1: Arrows+1..5   |   P2: WASD+6..0", True, MUTED)
        self.screen.blit(hint2, (70, 175))

        left = pygame.Rect(70, 210, 520, 380)
        right = pygame.Rect(690, 210, 520, 380)
        draw_panel(self.screen, left, "FIGHTER 1", self.font_b)
        draw_panel(self.screen, right, "FIGHTER 2", self.font_b)

        self.draw_fighter_list(left, mouse, side="A")
        self.draw_fighter_list(right, mouse, side="B")

        self.btn_add_legends.draw(self.screen, mouse)
        self.btn_create.draw(self.screen, mouse)
        self.btn_start.draw(self.screen, mouse)
        self.btn_back.draw(self.screen, mouse)

        self.draw_log()

    def draw_fighter_list(self, panel_rect, mouse, side="A"):
        view = pygame.Rect(panel_rect.x + 18, panel_rect.y + 68, panel_rect.w - 36, panel_rect.h - 88)
        draw_rect_round(self.screen, view, (14, 14, 22), r=14)
        draw_rect_round(self.screen, view, (45,45,70), r=14, width=2)

        fighters = self.fighters
        if not fighters:
            t = self.font.render("No fighters in DB. Click 'Add Legends'.", True, MUTED)
            self.screen.blit(t, (view.x + 16, view.y + 18))
            return

        item_h = 58
        visible = view.h // item_h
        scroll = self.scroll_a if side=="A" else self.scroll_b
        scroll = clamp(scroll, 0, max(0, len(fighters)-visible))
        if side=="A": self.scroll_a = scroll
        else: self.scroll_b = scroll

        for i in range(visible):
            idx = int(scroll) + i
            if idx >= len(fighters): break
            f = fighters[idx]
            r = pygame.Rect(view.x + 10, view.y + 10 + i*item_h, view.w - 20, item_h - 10)

            selected = (self.sel_a and f.fighter_id == self.sel_a.fighter_id) if side=="A" else (self.sel_b and f.fighter_id == self.sel_b.fighter_id)
            bg = (26, 26, 38) if not selected else (34, 30, 44)
            draw_rect_round(self.screen, r, bg, r=12)
            outline = (RED if side=="A" else BLUE) if selected else (70,70,105)
            draw_rect_round(self.screen, r, outline, r=12, width=2 if r.collidepoint(mouse) else 1)

            icon_color = RED if side=="A" else BLUE
            pygame.draw.circle(self.screen, icon_color, (r.x+22, r.y+26), 9)

            name = self.font.render(f.name.upper()[:22], True, TEXT)
            self.screen.blit(name, (r.x + 44, r.y + 10))
            sub = self.font_s.render(f"{f.weight_class}  •  {fighter_style(f)}", True, MUTED)
            self.screen.blit(sub, (r.x + 44, r.y + 32))

            ovr = int(get_stat(f, "overall_skill", 50))
            o = self.font.render(f"OVR {ovr}", True, YELLOW)
            self.screen.blit(o, (r.right - o.get_width() - 14, r.y + 18))

    def handle_select(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.scene = "home"
            return

        if self.btn_back.clicked(ev):
            self.scene = "home"
            return

        if self.btn_add_legends.clicked(ev):
            self.add_legends()
            return

        if self.btn_create.clicked(ev):
            self.scene = "create"
            self.create_name = ""
            self.stats = dict(self.stats_template)
            self.push_log("Create Fighter: type name, pick weight/type, set stats.")
            return

        if ev.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if 70 <= mx <= 590 and 210 <= my <= 590:
                self.scroll_a = clamp(self.scroll_a - ev.y, 0, max(0, len(self.fighters)-6))
            if 690 <= mx <= 1210 and 210 <= my <= 590:
                self.scroll_b = clamp(self.scroll_b - ev.y, 0, max(0, len(self.fighters)-6))

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            f = self.pick_from_list(ev.pos, side="A")
            if f:
                self.sel_a = f
                self.push_log(f"Fighter 1: {f.name}")
            f = self.pick_from_list(ev.pos, side="B")
            if f:
                self.sel_b = f
                self.push_log(f"Fighter 2: {f.name}")

        if self.btn_start.clicked(ev) or (ev.type==pygame.KEYDOWN and ev.key==pygame.K_RETURN):
            if not self.sel_a or not self.sel_b:
                self.push_log("Pick TWO fighters first.")
                return
            if self.sel_a.fighter_id == self.sel_b.fighter_id:
                self.push_log("Choose two different fighters.")
                return
            self.start_fight()

    def pick_from_list(self, pos, side="A"):
        fighters = self.fighters
        if not fighters: return None
        panel = pygame.Rect(70, 210, 520, 380) if side=="A" else pygame.Rect(690, 210, 520, 380)
        view = pygame.Rect(panel.x + 18, panel.y + 68, panel.w - 36, panel.h - 88)
        if not view.collidepoint(pos): return None
        item_h = 58
        rel_y = pos[1] - (view.y + 10)
        if rel_y < 0: return None
        row = rel_y // item_h
        scroll = self.scroll_a if side=="A" else self.scroll_b
        idx = int(scroll) + int(row)
        if 0 <= idx < len(fighters):
            return fighters[idx]
        return None

    # ----------------- CREATE -----------------
    def draw_create(self, mouse):
        self.screen.fill(BG)
        title = self.font_title.render("CREATE FIGHTER", True, TEXT)
        self.screen.blit(title, (70, 60))

        rect = pygame.Rect(70, 150, 820, 540)
        draw_panel(self.screen, rect, "Details & Stats", self.font_b)

        self.screen.blit(self.font.render("Name (type):", True, MUTED), (rect.x+24, rect.y+80))
        name_box = pygame.Rect(rect.x+24, rect.y+110, 360, 44)
        draw_rect_round(self.screen, name_box, (14,14,22), r=12)
        draw_rect_round(self.screen, name_box, BORDER, r=12, width=2)
        nm = self.font.render(self.create_name or "—", True, TEXT)
        self.screen.blit(nm, (name_box.x+12, name_box.y+10))

        wc = self.weight_classes[self.create_weight_idx]
        self.screen.blit(self.font.render(f"Weight class: {wc}  (LEFT/RIGHT)", True, MUTED), (rect.x+24, rect.y+175))

        tp = self.types[self.create_type_idx]
        self.screen.blit(self.font.render(f"Type: {tp}  (UP/DOWN)", True, MUTED), (rect.x+24, rect.y+210))

        self.screen.blit(self.font.render("Edit stats: TAB to select, +/- to change", True, MUTED), (rect.x+24, rect.y+250))

        stat_keys = ["STR","GRP","SPD","KICK","SUB","DEF","VERS","STA"]
        x0, y0 = rect.x+24, rect.y+285
        for i,k in enumerate(stat_keys):
            val = int(self.stats.get(k,70))
            row = i//2
            col = i%2
            bx = x0 + col*380
            by = y0 + row*70
            colr = RED if k in ("STR","KICK") else BLUE if k in ("GRP","SUB") else YELLOW if k in ("STA","DEF") else (150,150,220)
            label = f"{k} {'<-' if i==self.edit_stat_idx else ''}"
            self._draw_bar(bx, by+24, 330, 18, label, val, 100, colr)

        self.btn_save.draw(self.screen, mouse)
        self.btn_create_back.draw(self.screen, mouse)
        self.draw_log()

    def _draw_bar(self, x, y, w, h, label, val, maxv, color):
        val = clamp(val, 0, maxv)
        draw_rect_round(self.screen, pygame.Rect(x, y, w, h), (12, 12, 18), r=10)
        draw_rect_round(self.screen, pygame.Rect(x, y, w, h), BORDER, r=10, width=2)
        fill_w = int((w - 4) * (val / maxv if maxv else 0))
        draw_rect_round(self.screen, pygame.Rect(x + 2, y + 2, fill_w, h - 4), color, r=10)
        txt = self.font_s.render(f"{label}: {val}/{maxv}", True, TEXT)
        self.screen.blit(txt, (x, y - 20))

    def handle_create(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.scene = "select"; return
            if ev.key == pygame.K_BACKSPACE:
                self.create_name = self.create_name[:-1]
            elif ev.key == pygame.K_TAB:
                self.edit_stat_idx = (self.edit_stat_idx + 1) % 8
            elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self._change_stat(+3)
            elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self._change_stat(-3)
            elif ev.key == pygame.K_LEFT:
                self.create_weight_idx = (self.create_weight_idx - 1) % len(self.weight_classes)
            elif ev.key == pygame.K_RIGHT:
                self.create_weight_idx = (self.create_weight_idx + 1) % len(self.weight_classes)
            elif ev.key == pygame.K_UP:
                self.create_type_idx = (self.create_type_idx - 1) % len(self.types)
            elif ev.key == pygame.K_DOWN:
                self.create_type_idx = (self.create_type_idx + 1) % len(self.types)
            elif ev.unicode and ev.unicode.isprintable():
                if len(self.create_name) < 22:
                    self.create_name += ev.unicode

        if self.btn_create_back.clicked(ev):
            self.scene = "select"; return

        if self.btn_save.clicked(ev) or (ev.type==pygame.KEYDOWN and ev.key==pygame.K_RETURN):
            if not self.create_name.strip():
                self.push_log("Name is required.")
                return
            f = self.build_custom_fighter()
            ok = self.repo.add_fighter(f)
            self.refresh_fighters()
            self.push_log(f"Saved: {f.name} ({fighter_style(f)})" if ok else "Failed to save fighter.")
            self.scene = "select"

    def _change_stat(self, delta):
        stat_keys = ["STR","GRP","SPD","KICK","SUB","DEF","VERS","STA"]
        k = stat_keys[self.edit_stat_idx]
        self.stats[k] = int(clamp(self.stats.get(k,70) + delta, 10, 100))

    def build_custom_fighter(self):
        fid = self.next_id()
        name = self.create_name.strip()
        wc = self.weight_classes[self.create_weight_idx]
        tp = self.types[self.create_type_idx]

        STR = int(self.stats["STR"])
        GRP = int(self.stats["GRP"])
        SPD = int(self.stats["SPD"])
        KICK = int(self.stats["KICK"])
        SUB = int(self.stats["SUB"])
        DEF = int(self.stats["DEF"])
        VERS = int(self.stats["VERS"])

        if tp == "Striker":
            return Striker(fid, name, wc, striking_power=STR, grappling_skill=GRP, speed=SPD, kick_power=KICK)
        if tp == "Grappler":
            return Grappler(fid, name, wc, striking_power=STR, grappling_skill=GRP, submission_skill=SUB, takedown_defense=DEF)
        return HybridChampion(fid, name, wc, striking_power=STR, grappling_skill=GRP, speed=SPD, kick_power=KICK,
                             submission_skill=SUB, takedown_defense=DEF, versatility=VERS)

    # ----------------- ROSTER -----------------
    def draw_roster(self, mouse):
        self.screen.fill(BG)
        title = self.font_title.render("FIGHTER ROSTER", True, TEXT)
        self.screen.blit(title, (70, 60))

        grid = pygame.Rect(70, 150, 880, 540)
        draw_panel(self.screen, grid, "", self.font_b)

        self.btn_roster_ai.draw(self.screen, mouse)
        self.btn_roster_back.draw(self.screen, mouse)

        draw_panel(self.screen, pygame.Rect(980, 250, 250, 440), "AI Panel", self.font)

        fighters = self.fighters
        if not fighters:
            t = self.font.render("No fighters. Go Select > Add Legends.", True, MUTED)
            self.screen.blit(t, (grid.x+24, grid.y+60))
            return

        cols = 2
        card_w = (grid.w - 24*3)//2
        card_h = 170
        per_page = 3*cols
        rows_total = math.ceil(len(fighters)/cols)
        max_scroll = max(0, rows_total - 3)
        self.roster_scroll = clamp(self.roster_scroll, 0, max_scroll)

        start_row = int(self.roster_scroll)
        idx0 = start_row*cols
        show = fighters[idx0: idx0 + per_page]

        for i,f in enumerate(show):
            r = i//cols
            c = i%cols
            x = grid.x + 24 + c*(card_w+24)
            y = grid.y + 24 + r*(card_h+24)
            card = pygame.Rect(x, y, card_w, card_h)
            selected = self.roster_selected and f.fighter_id == self.roster_selected.fighter_id
            draw_rect_round(self.screen, card, PANEL_2 if selected else PANEL, r=16)
            draw_rect_round(self.screen, card, (RED if selected else BORDER), r=16, width=2)

            nm = self.font_b.render(f.name.upper()[:18], True, TEXT)
            self.screen.blit(nm, (card.x+16, card.y+14))
            st = self.font_s.render(f"{fighter_style(f)}  •  {f.weight_class}", True, MUTED)
            self.screen.blit(st, (card.x+16, card.y+52))

            STR = get_stat(f,"striking_power",50)
            GRP = get_stat(f,"grappling_skill",50)
            STA = int(60 + (get_stat(f,"speed",60)*0.2) + (get_stat(f,"versatility",60)*0.2))
            DEF = int((get_stat(f,"takedown_defense",60) + get_stat(f,"grappling_skill",60)) / 2)

            self._mini_bar(card.x+16, card.y+82, 250, "STR", STR, RED)
            self._mini_bar(card.x+16, card.y+104, 250, "GRP", GRP, BLUE)
            self._mini_bar(card.x+16, card.y+126, 250, "STA", clamp(STA,10,100), YELLOW)
            self._mini_bar(card.x+16, card.y+148, 250, "DEF", clamp(DEF,10,100), GREEN)

        txt = self.roster_ai_text or "Select a fighter, then click AI Stats."
        self.draw_wrapped_text(txt, pygame.Rect(990, 292, 230, 388), self.font_s)
        self.draw_log()

    def _mini_bar(self, x, y, w, label, val, color):
        t = self.font_s.render(label, True, MUTED)
        self.screen.blit(t, (x, y))
        bar = pygame.Rect(x+34, y+4, w-34, 12)
        pygame.draw.rect(self.screen, (12,12,18), bar, border_radius=8)
        pygame.draw.rect(self.screen, BORDER, bar, width=1, border_radius=8)
        fill = int((bar.w-2)*clamp(val,0,100)/100)
        pygame.draw.rect(self.screen, color, (bar.x+1, bar.y+1, fill, bar.h-2), border_radius=8)
        v = self.font_s.render(str(val), True, TEXT)
        self.screen.blit(v, (x+w+8, y-1))

    def draw_wrapped_text(self, txt, rect, font):
        words = txt.split()
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= rect.w:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)

        y = rect.y
        for ln in lines[:22]:
            t = font.render(ln, True, TEXT)
            self.screen.blit(t, (rect.x, y))
            y += font.get_height() + 2

    def handle_roster(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.scene = "home"; return
        if self.btn_roster_back.clicked(ev):
            self.scene = "home"; return
        if ev.type == pygame.MOUSEWHEEL:
            self.roster_scroll = clamp(self.roster_scroll - ev.y, 0, 999)

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            f = self.pick_roster_card(ev.pos)
            if f:
                self.roster_selected = f
                self.roster_ai_text = f"Selected: {f.name} ({fighter_style(f)})"
        if self.btn_roster_ai.clicked(ev):
            self.run_ai_stats()

    def pick_roster_card(self, pos):
        grid = pygame.Rect(70, 150, 880, 540)
        if not grid.collidepoint(pos): return None
        cols=2
        card_w = (grid.w - 24*3)//2
        card_h = 170
        start_row = int(self.roster_scroll)
        for r in range(3):
            for c in range(cols):
                x = grid.x + 24 + c*(card_w+24)
                y = grid.y + 24 + r*(card_h+24)
                card = pygame.Rect(x,y,card_w,card_h)
                if card.collidepoint(pos):
                    idx = (start_row*cols) + (r*cols+c)
                    if 0 <= idx < len(self.fighters):
                        return self.fighters[idx]
        return None

    def run_ai_stats(self):
        if not self.roster_selected:
            self.roster_ai_text = "Pick a fighter first."
            return
        if not self.ollama:
            self.roster_ai_text = "Ollama client not available (import failed)."
            return
        if not self.ollama.is_available():
            self.roster_ai_text = "Ollama server not available. Start Ollama and try again."
            return

        f = self.roster_selected
        prompt = f"""
You are an MMA analyst. Provide BOTH:
1) Short scouting report (3-5 bullet points).
2) A JSON object with ratings 0-100: STR, GRP, STA, DEF, IQ.

Fighter:
Name: {f.name}
Weight: {f.weight_class}
Style: {fighter_style(f)}
Existing stats: striking_power={get_stat(f,'striking_power',50)}, grappling_skill={get_stat(f,'grappling_skill',50)},
speed={get_stat(f,'speed',60)}, kick_power={get_stat(f,'kick_power',60)}, submission_skill={get_stat(f,'submission_skill',60)},
takedown_defense={get_stat(f,'takedown_defense',60)}, versatility={get_stat(f,'versatility',60)}.

Return the JSON on a separate line, and keep it valid JSON.
"""
        self.roster_ai_text = "AI loading..."
        try:
            resp = self.ollama.generate(prompt) or ""
            m = re.search(r"\{.*\}", resp, flags=re.S)
            ratings = ""
            if m:
                try:
                    j = json.loads(m.group(0))
                    ratings = f"RATINGS: STR {j.get('STR')}  GRP {j.get('GRP')}  STA {j.get('STA')}  DEF {j.get('DEF')}  IQ {j.get('IQ')}\n\n"
                except Exception:
                    pass
            self.roster_ai_text = ratings + resp.strip()[:900]
        except Exception as e:
            self.roster_ai_text = f"AI error: {e}"

    # ----------------- FIGHT -----------------
    def start_fight(self):
        self.scene = "fight"
        self.fight = FightArena(self, self.sel_a, self.sel_b, self.state.mode)
        self.push_log("Fight started!")

    def draw_fight(self, mouse):
        self.fight.draw(self.screen, mouse)

    def handle_fight(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.scene = "select"
            self.fight = None
            return
        self.fight.handle_event(ev)

    # ----------------- LOG -----------------
    def draw_log(self):
        rect = pygame.Rect(70, 690-80, 1150, 70)
        draw_rect_round(self.screen, rect, (14,14,22), r=14)
        draw_rect_round(self.screen, rect, (45,45,70), r=14, width=2)
        y = rect.y + 10
        for ln in self.log[-3:]:
            t = self.font_s.render(ln[:150], True, MUTED)
            self.screen.blit(t, (rect.x + 12, y))
            y += 18

    def run(self):
        while True:
            self.clock.tick(FPS)
            mouse = pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if self.scene == "home": self.handle_home(ev)
                elif self.scene == "about": self.handle_about(ev)
                elif self.scene == "select": self.handle_select(ev)
                elif self.scene == "create": self.handle_create(ev)
                elif self.scene == "roster": self.handle_roster(ev)
                elif self.scene == "fight": self.handle_fight(ev)

            if self.scene == "home": self.draw_home(mouse)
            elif self.scene == "about": self.draw_about(mouse)
            elif self.scene == "select": self.draw_select(mouse)
            elif self.scene == "create": self.draw_create(mouse)
            elif self.scene == "roster": self.draw_roster(mouse)
            elif self.scene == "fight":
                self.fight.update(1/FPS)
                self.draw_fight(mouse)

            pygame.display.flip()

class FightArena:
    def __init__(self, app: App, f1: Fighter, f2: Fighter, mode: str):
        self.app = app
        self.f1 = f1
        self.f2 = f2
        self.mode = mode  # "CPU" or "2P"

        self.arena = pygame.Rect(70, 120, 1140, 520)

        self.hp1 = 100
        self.hp2 = 100
        self.sta1 = 100
        self.sta2 = 100

        self.block1_until = 0.0
        self.block2_until = 0.0

        self.cooldowns = {
            "p1": {"jab":0,"kick":0,"grapple":0},
            "p2": {"jab":0,"kick":0,"grapple":0},
        }
        self.stun1_until = 0.0
        self.stun2_until = 0.0

        self.p1 = pygame.Vector2(self.arena.left+220, self.arena.centery)
        self.p2 = pygame.Vector2(self.arena.right-220, self.arena.centery)
        self.v1 = pygame.Vector2(0,0)
        self.v2 = pygame.Vector2(0,0)

        self.size = 40
        self.over = False
        self.winner = None
        self.saved = False
        self.spawn_time = time.time()

    def update(self, dt):
        if self.over:
            return

        self.sta1 = clamp(self.sta1 + 7*dt, 0, 100)
        self.sta2 = clamp(self.sta2 + 7*dt, 0, 100)

        self.p1 += self.v1 * dt
        self.p2 += self.v2 * dt

        self.p1.x = clamp(self.p1.x, self.arena.left + self.size, self.arena.right - self.size)
        self.p1.y = clamp(self.p1.y, self.arena.top + self.size, self.arena.bottom - self.size)
        self.p2.x = clamp(self.p2.x, self.arena.left + self.size, self.arena.right - self.size)
        self.p2.y = clamp(self.p2.y, self.arena.top + self.size, self.arena.bottom - self.size)

        if self.mode == "CPU":
            self.ai_step(dt)

        if self.hp1 <= 0 or self.hp2 <= 0:
            self.over = True
            if self.hp1 <= 0 and self.hp2 <= 0:
                self.winner = "Draw"
            elif self.hp1 <= 0:
                self.winner = self.f2.name
                self.f2.add_win(); self.f1.add_loss()
            else:
                self.winner = self.f1.name
                self.f1.add_win(); self.f2.add_loss()

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_r and self.over:
                self.__init__(self.app, self.f1, self.f2, self.mode)
                return

            now = time.time()
            if not self.over and now > self.stun1_until:
                if ev.key == pygame.K_1: self.try_attack("p1","jab")
                if ev.key == pygame.K_2: self.try_attack("p1","kick")
                if ev.key == pygame.K_3: self.try_attack("p1","grapple")
                if ev.key == pygame.K_4: self.block1_until = now + 0.7
                if ev.key == pygame.K_5: self.sta1 = clamp(self.sta1 + 20, 0, 100)

            if self.mode == "2P" and (not self.over) and now > self.stun2_until:
                if ev.key == pygame.K_6: self.try_attack("p2","jab")
                if ev.key == pygame.K_7: self.try_attack("p2","kick")
                if ev.key == pygame.K_8: self.try_attack("p2","grapple")
                if ev.key == pygame.K_9: self.block2_until = now + 0.7
                if ev.key == pygame.K_0: self.sta2 = clamp(self.sta2 + 20, 0, 100)

        keys = pygame.key.get_pressed()
        now = time.time()

        sp1 = get_stat(self.f1, "speed", 70)
        sp2 = get_stat(self.f2, "speed", 70)

        base1 = 260 + sp1*1.2
        base2 = 260 + sp2*1.2

        if self.sta1 < 25: base1 *= 0.75
        if self.sta2 < 25: base2 *= 0.75

        # P1 always arrows (as you asked)
        dx = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
        dy = (1 if keys[pygame.K_DOWN] else 0) - (1 if keys[pygame.K_UP] else 0)
        v = pygame.Vector2(dx, dy)
        if v.length_squared() > 0: v = v.normalize()
        self.v1 = v * base1 if now > self.stun1_until else pygame.Vector2(0,0)

        # P2 only if 2P
        if self.mode == "2P":
            dx2 = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
            dy2 = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)
            v2 = pygame.Vector2(dx2, dy2)
            if v2.length_squared() > 0: v2 = v2.normalize()
            self.v2 = v2 * base2 if now > self.stun2_until else pygame.Vector2(0,0)

    def ai_step(self, dt):
        now = time.time()
        if now < self.stun2_until:
            self.v2 = pygame.Vector2(0,0)
            return

        to_p1 = self.p1 - self.p2
        dist = to_p1.length()
        dirv = to_p1.normalize() if dist > 1 else pygame.Vector2(0,0)

        sp2 = get_stat(self.f2, "speed", 70)
        base2 = 260 + sp2*1.2
        if self.sta2 < 25: base2 *= 0.75

        desired = 80 if fighter_style(self.f2) == "Grappler" else 130

        if dist > desired:
            self.v2 = dirv * base2
        else:
            self.v2 *= 0.4
            if self.sta2 < 25 and random.random() < 0.45:
                self.sta2 = clamp(self.sta2 + 18, 0, 100)
            else:
                tp = fighter_style(self.f2)
                if tp == "Grappler" and random.random() < 0.55:
                    self.try_attack("p2","grapple")
                elif tp == "Striker" and random.random() < 0.6:
                    self.try_attack("p2","kick")
                else:
                    self.try_attack("p2","jab")
            if random.random() < 0.2:
                self.block2_until = now + 0.55

    def try_attack(self, who, move):
        now = time.time()
        cd = self.cooldowns[who]
        if now < cd[move]:
            return

        cost = {"jab":10,"kick":14,"grapple":16}[move]
        if who == "p1":
            if self.sta1 < cost: return
            self.sta1 -= cost
        else:
            if self.sta2 < cost: return
            self.sta2 -= cost

        cd[move] = now + {"jab":0.35,"kick":0.55,"grapple":0.75}[move]
        self.resolve_attack(who, move)

    def resolve_attack(self, who, move):
        atk = self.f1 if who=="p1" else self.f2
        dfd = self.f2 if who=="p1" else self.f1
        atk_pos = self.p1 if who=="p1" else self.p2
        dfd_pos = self.p2 if who=="p1" else self.p1

        dist = (dfd_pos - atk_pos).length()
        in_range = dist <= (125 if move!="grapple" else 85)
        if not in_range:
            return

        STR = get_stat(atk,"striking_power",50)
        GRP = get_stat(atk,"grappling_skill",50)
        KICK = get_stat(atk,"kick_power",STR)
        SUB = get_stat(atk,"submission_skill",GRP)
        VERS = get_stat(atk,"versatility",60)
        DEF = int((get_stat(dfd,"takedown_defense",60) + get_stat(dfd,"grappling_skill",60))/2)

        st = fighter_style(atk)
        bonus = 1.0
        if st == "Striker" and move in ("jab","kick"): bonus = 1.15
        if st == "Grappler" and move == "grapple": bonus = 1.2
        if st == "Hybrid": bonus = 1.07

        if move == "jab":
            dmg = int((6 + STR*0.10 + VERS*0.03) * bonus) + random.randint(-2,3)
        elif move == "kick":
            dmg = int((8 + KICK*0.11 + VERS*0.02) * bonus) + random.randint(-3,4)
        else:
            dmg = int((7 + GRP*0.08 + SUB*0.06) * bonus) + random.randint(-2,5)

        dmg = clamp(dmg, 3, 28)

        now = time.time()
        blocking = (now < self.block2_until) if who=="p1" else (now < self.block1_until)
        if blocking:
            dmg = max(1, int(dmg * 0.45))

        if move == "grapple":
            dmg = max(1, int(dmg * (100 - clamp(DEF,10,95)) / 100 + 6))

        if who=="p1":
            self.hp2 = clamp(self.hp2 - dmg, 0, 100)
            if move=="grapple" and random.random() < 0.35:
                self.stun2_until = time.time() + 0.45
        else:
            self.hp1 = clamp(self.hp1 - dmg, 0, 100)
            if move=="grapple" and random.random() < 0.35:
                self.stun1_until = time.time() + 0.45

    def draw_fighter(self, surf, center, main_color):
        # Simple "fighter" silhouette (head+body+gloves), not a square
        cx, cy = int(center.x), int(center.y)
        # body
        pygame.draw.ellipse(surf, (20,20,28), (cx-26, cy-18, 52, 62))
        pygame.draw.ellipse(surf, main_color, (cx-26, cy-18, 52, 62), 3)
        # head
        pygame.draw.circle(surf, (24,24,36), (cx, cy-40), 16)
        pygame.draw.circle(surf, main_color, (cx, cy-40), 16, 3)
        # gloves
        pygame.draw.circle(surf, main_color, (cx-34, cy-5), 10)
        pygame.draw.circle(surf, main_color, (cx+34, cy-5), 10)
        pygame.draw.circle(surf, (10,10,14), (cx-34, cy-5), 10, 2)
        pygame.draw.circle(surf, (10,10,14), (cx+34, cy-5), 10, 2)

    def draw(self, surf, mouse):
        surf.fill(BG)

        # HUD
        self.draw_bar(surf, 70, 80, 520, 16, f"{self.f1.name} HP", self.hp1, 100, RED)
        self.draw_bar(surf, 70, 110, 520, 14, "STA", int(self.sta1), 100, YELLOW)

        self.draw_bar(surf, 690, 80, 520, 16, f"{self.f2.name} HP", self.hp2, 100, BLUE)
        self.draw_bar(surf, 690, 110, 520, 14, "STA", int(self.sta2), 100, YELLOW)

        # Arena (NOT split)
        draw_rect_round(surf, self.arena, (14,14,22), r=18)
        draw_rect_round(surf, self.arena, (45,45,70), r=18, width=2)

        # fighters
        self.draw_fighter(surf, self.p1, RED)
        self.draw_fighter(surf, self.p2, BLUE)

        # controls overlay (first 3 seconds)
        now = time.time()
        if now - self.spawn_time < 3.0:
            box = pygame.Rect(260, 600, 760, 80)
            draw_rect_round(surf, box, (10,10,14), r=16)
            draw_rect_round(surf, box, BORDER, r=16, width=2)
            if self.mode == "CPU":
                txt = "VS CPU | P1: Arrows + 1/2/3/4/5"
            else:
                txt = "2 Players | P1: Arrows+1..5  |  P2: WASD+6..0"
            t = self.app.font.render(txt, True, MUTED)
            surf.blit(t, t.get_rect(center=box.center))

        # winner overlay
        if self.hp1 <= 0 or self.hp2 <= 0:
            if not self.over:
                self.over = True
                if self.hp1 <= 0 and self.hp2 <= 0:
                    self.winner = "Draw"
                elif self.hp1 <= 0:
                    self.winner = self.f2.name
                else:
                    self.winner = self.f1.name

            overlay = pygame.Rect(260, 240, 760, 220)
            draw_rect_round(surf, overlay, (10,10,14), r=18)
            draw_rect_round(surf, overlay, BORDER, r=18, width=2)
            wtxt = self.app.font_title.render(f"{self.winner}", True, GREEN if self.winner!="Draw" else YELLOW)
            surf.blit(wtxt, wtxt.get_rect(center=(overlay.centerx, overlay.y+85)))
            t = self.app.font.render("Press R to restart  |  ESC to go back", True, MUTED)
            surf.blit(t, t.get_rect(center=(overlay.centerx, overlay.y+150)))

    def draw_bar(self, surf, x, y, w, h, label, val, maxv, color):
        val = clamp(val, 0, maxv)
        draw_rect_round(surf, pygame.Rect(x, y, w, h), (12, 12, 18), r=10)
        draw_rect_round(surf, pygame.Rect(x, y, w, h), BORDER, r=10, width=2)
        fill_w = int((w - 4) * (val / maxv if maxv else 0))
        draw_rect_round(surf, pygame.Rect(x + 2, y + 2, fill_w, h - 4), color, r=10)
        txt = self.app.font_s.render(f"{label}: {val}/{maxv}", True, TEXT)
        surf.blit(txt, (x, y - 20))


if __name__ == "__main__":
    App().run()
