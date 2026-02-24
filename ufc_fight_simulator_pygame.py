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

        # home buttons - מותאם למצב שחקן יחיד בלבד
        self.btn_vs_cpu = Button((WIDTH//2-260, 320, 520, 80), "PLAY VS CPU", self.font_b, accent=GREEN)
        self.btn_roster = Button((WIDTH//2-260, 420, 520, 80), "FIGHTER ROSTER", self.font_b, accent=YELLOW)
        self.btn_about = Button((WIDTH//2-260, 520, 250, 60), "ABOUT", self.font_b, accent=(140,140,200))
        self.btn_exit = Button((WIDTH//2+10, 520, 250, 60), "EXIT", self.font_b, accent=(120,120,180))

        # select buttons
        # select buttons - הרמנו אותם קצת למעלה
        self.btn_add_legends = Button((70, 600, 220, 50), "Add Legends", self.font, accent=RED)
        self.btn_create = Button((300, 600, 220, 50), "Create Fighter", self.font, accent=YELLOW)
        self.btn_start = Button((530, 600, 220, 50), "START FIGHT", self.font, accent=GREEN)
        self.btn_back = Button((760, 600, 160, 50), "Back", self.font, accent=(140,140,200))

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
        all_from_repo = self.repo.get_all_fighters()
        
        # מסננת למניעת כפילויות ויזואליות
        unique_fighters = []
        seen_names = set()
        
        for f in all_from_repo:
            if f.name not in seen_names:
                unique_fighters.append(f)
                seen_names.add(f.name)
        
        self.fighters = unique_fighters

    def next_id(self):
        if not self.fighters:
            return 1
        return max(f.fighter_id for f in self.fighters) + 1

    def add_legends(self):
        # 1. ניקוי אגרסיבי של המאגר כדי להעיף את GSP ושמירות ישנות
        self.fighters.clear()
        if hasattr(self.repo, 'fighters'):
            self.repo.fighters.clear()
        if hasattr(self.repo, '_fighters'):
            self.repo._fighters.clear()
            
        base = 1 
        
        # --- הגדרת 5 הלוחמים ---
        
        # 1. חביב נורמגומדוב (רוסיה)
        khabib = Grappler(base, "Khabib Nurmagomedov", "Lightweight", 78, 97, 92, 90)
        khabib.skin_color, khabib.hair_color, khabib.pants_color = (198, 134, 103), (20, 20, 20), (20, 20, 20)
        khabib.country = "Russia"  

        # 2. קונור מקגרגור (אירלנד)
        conor = Striker(base+1, "Conor McGregor", "Lightweight", 95, 65, 78, 86)
        conor.country = "Ireland" 
        conor.skin_color, conor.hair_color, conor.pants_color = (255, 224, 196), (180, 90, 40), (34, 139, 34)

        # 3. אהבת "גולדנבוי" גורדון (ישראל - מחליף את GSP)
        ah_gordon = HybridChampion(base+2, 'Ahavat "Goldenboy" Gordon', "Light Heavyweight", 92, 88, 86, 85, 84, 88, 90)
        ah_gordon.skin_color = (220, 175, 140)  
        ah_gordon.hair_color = (160, 130, 80)   
        ah_gordon.pants_color = (90, 10, 10)    
        ah_gordon.hair_length = "long" 
        ah_gordon.country = "Israel"  

        # 4. אנדרסון סילבה (ברזיל)
        silva = Striker(base+3, "Anderson Silva", "Middleweight", 96, 70, 85, 90)
        silva.skin_color, silva.hair_color, silva.pants_color = (110, 75, 55), (10, 10, 10), (255, 215, 0) # מכנסיים צהובים קלאסיים
        silva.country = "Brazil"

        # 5. ג'ון ג'ונס (ארה"ב)
        jones = Grappler(base+4, "Jon Jones", "Heavyweight", 88, 95, 92, 90)
        jones.skin_color, jones.hair_color, jones.pants_color = (100, 65, 45), (10, 10, 10), (200, 20, 20)
        jones.country = "USA"

        # איגוד החמישייה לרשימה אחת
        legends = [khabib, conor, ah_gordon, silva, jones]
        
        # 3. הוספה מחדש למאגר הנתונים
        added = 0
        for f in legends:
            self.repo.add_fighter(f)
            added += 1
            
        # 4. רענון הרשימה והודעה
        self.refresh_fighters()
        self.push_log(f"Roster Reset: {added} legends ready.")
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
        # 1. הגדרת הריבוע בפינה השמאלית התחתונה
        # נשתמש ב-300x300 פיקסלים כדי שיהיה מקום לטקסט
        art_size = (300, 300)
        
        # המיקום: 40 פיקסלים משמאל, ו-340 פיקסלים מהתחתית
        x = 40
        y = HEIGHT - 340
        art_rect = pygame.Rect(x, y, art_size[0], art_size[1])

        # 2. ניסיון לטעון ולהציג את התמונה
        if self.home_img:
            # אנחנו מכווצים את התמונה לריבוע שלנו כדי שהיא לא תצא מהמסגרת
            scaled_img = pygame.transform.smoothscale(self.home_img, art_size)
            
            # הוספת מסגרת דקה מסביב כדי שייראה יפה
            pygame.draw.rect(self.screen, (40, 40, 60), art_rect, width=3, border_radius=12)
            
            # ציור התמונה עצמה בתוך המסגרת
            self.screen.blit(scaled_img, (x+3, y+3))
            
        else:
            # רק למקרה שהקובץ לא נמצא - נצייר ריבוע ריק
            draw_rect_round(self.screen, art_rect, (20, 20, 30), r=12)
            t = self.font_s.render("Image not found", True, MUTED)
            self.screen.blit(t, t.get_rect(center=art_rect.center))

    def handle_home(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

        if self.btn_vs_cpu.clicked(ev):
            self.state.mode = "CPU"
            self.scene = "select"
            self.push_log("Mode: VS CPU. Select two fighters.")
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
        # 1. הגדרת אזור התצוגה והציור שלו
        view = pygame.Rect(panel_rect.x + 18, panel_rect.y + 68, panel_rect.w - 36, panel_rect.h - 88)
        draw_rect_round(self.screen, view, (14, 14, 22), r=14)
        draw_rect_round(self.screen, view, (45, 45, 70), r=14, width=2)

        fighters = self.fighters
        if not fighters:
            t = self.font.render("No fighters in DB. Click 'Add Legends'.", True, (100, 100, 120))
            self.screen.blit(t, (view.x + 16, view.y + 18))
            return

        # 2. ניהול הגלילה (Scrolling)
        item_h = 58
        visible = view.h // item_h
        scroll = self.scroll_a if side == "A" else self.scroll_b
        scroll = clamp(scroll, 0, max(0, len(fighters) - visible))
        
        if side == "A": self.scroll_a = scroll
        else: self.scroll_b = scroll

        # 3. לולאת הציור של הלוחמים ברשימה
        for i in range(visible):
            idx = int(scroll) + i
            if idx >= len(fighters): break
            f = fighters[idx]
            
            # הגדרת המלבן של כל שורה ברשימה
            r = pygame.Rect(view.x + 10, view.y + 10 + i * item_h, view.w - 20, item_h - 10)

            # בדיקה אם הלוחם הנוכחי נבחר
            selected = (self.sel_a and f.fighter_id == self.sel_a.fighter_id) if side == "A" else (self.sel_b and f.fighter_id == self.sel_b.fighter_id)
            bg = (26, 26, 38) if not selected else (34, 30, 44)
            draw_rect_round(self.screen, r, bg, r=12)
            
            # ציור מסגרת מודגשת במעבר עכבר או בחירה
            outline = (RED if side == "A" else BLUE) if selected else (70, 70, 105)
            draw_rect_round(self.screen, r, outline, r=12, width=2 if r.collidepoint(mouse) else 1)

            # אייקון צבעוני קטן בצד
            icon_color = RED if side == "A" else BLUE
            pygame.draw.circle(self.screen, icon_color, (r.x + 22, r.y + 26), 9)

            # --- הוספת השם והדגל (המעקף של מסד הנתונים) ---
            # רינדור השם
            name_txt = self.font.render(f.name.upper()[:22], True, (255, 255, 255))
            self.screen.blit(name_txt, (r.x + 44, r.y + 10))

            # מילון מדינות שקובע איזה דגל לצייר לפי השם במקום לסמוך על ה-DB
            country_map = {
                "Khabib Nurmagomedov": "Russia",
                "Conor McGregor": "Ireland",
                'Ahavat "Goldenboy" Gordon': "Israel",
                "Anderson Silva": "Brazil",
                "Jon Jones": "USA"
            }

            # מושכים את שם המדינה מהמילון
            f_country = country_map.get(f.name)

            if f_country:
                try:
                    # טעינת הדגל מתיקיית ה-assets
                    flag_path = f"assets/{f_country}.png"
                    flag_img = pygame.image.load(flag_path).convert_alpha()
                    
                    # שינוי גודל הדגל לממדים שמתאימים לשורה
                    flag_img = pygame.transform.scale(flag_img, (24, 16))
                    
                    # מיקום הדגל: סוף השם + מרווח של 10 פיקסלים
                    flag_x = r.x + 44 + name_txt.get_width() + 10
                    flag_y = r.y + 14 
                    
                    self.screen.blit(flag_img, (flag_x, flag_y))
                except Exception as e:
                    # אם חסר קובץ או שיש טעות בשם, נדפיס לטרמינל כדי שנדע
                    print(f"DEBUG: Failed to load flag for {f.name} - {e}")
                    pass

            # --- תיאור וסטטיסטיקות ---
            # שורת תיאור (משקל וסגנון)
            sub = self.font_s.render(f"{f.weight_class}  •  {fighter_style(f)}", True, (140, 140, 160))
            self.screen.blit(sub, (r.x + 44, r.y + 32))

            # הצגת ה-Overall (OVR) בצד ימין
            ovr = int(get_stat(f, "overall_skill", 50))
            o = self.font.render(f"OVR {ovr}", True, (255, 215, 0)) # צבע צהוב/זהב
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
        rect = pygame.Rect(70, 660, 1140, 50)
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
        self.f1, self.f2 = f1, f2
        self.mode = mode 
        self.arena = pygame.Rect(70, 120, 1140, 520)
        
        # נתוני חיים וכוח
        self.hp1, self.hp2 = 100, 100
        self.sta1, self.sta2 = 100, 100
        
        # טיימרים להבהוב (אפקט פגיעה)
        self.p1_hit_timer, self.p2_hit_timer = 0.0, 0.0
        
        # הגנה וטעינה
        self.block1_until, self.block2_until = 0.0, 0.0
        self.cooldowns = {"p1": {"jab":0,"kick":0,"grapple":0}, "p2": {"jab":0,"kick":0,"grapple":0}}
        self.stun1_until, self.stun2_until = 0.0, 0.0

        # מיקום התחלתי
        GROUND_Y = self.arena.bottom - 120
        self.p1 = pygame.Vector2(self.arena.left + 220, GROUND_Y)
        self.p2 = pygame.Vector2(self.arena.right - 220, GROUND_Y)
        self.v1, self.v2 = pygame.Vector2(0,0), pygame.Vector2(0,0)
        self.size = 40
        self.over = False
        self.winner = None

        try:
            img = pygame.image.load("assets/arena_bg.png").convert_alpha()
            self.arena_img = pygame.transform.scale(img, (self.arena.width, self.arena.height))
        except: self.arena_img = None

    def update(self, dt):
        if self.over: return

        # התחדשות סטמינה
        self.sta1 = clamp(self.sta1 + 7*dt, 0, 100)
        self.sta2 = clamp(self.sta2 + 7*dt, 0, 100)

        # תנועה
        self.p1.x += self.v1.x * dt
        self.p2.x += self.v2.x * dt

        # --- פיזיקה: מעבר חופשי בין צדדים עם דחייה קלה ---
        dist_x = self.p1.x - self.p2.x
        if abs(dist_x) < 55:
            nudge = 2.5
            if dist_x >= 0: 
                self.p1.x += nudge; self.p2.x -= nudge
            else: 
                self.p1.x -= nudge; self.p2.x += nudge

        # גבולות זירה
        self.p1.x = clamp(self.p1.x, self.arena.left + 40, self.arena.right - 40)
        self.p2.x = clamp(self.p2.x, self.arena.left + 40, self.arena.right - 40)

        # עדכון טיימרים להבהוב נזק
        self.p1_hit_timer = max(0, self.p1_hit_timer - dt)
        self.p2_hit_timer = max(0, self.p2_hit_timer - dt)

        # עדכון AI וניצחון
        if self.mode == "CPU": self.ai_step(dt)
        if int(self.hp1) <= 0 or int(self.hp2) <= 0:
            self.over = True
            self.winner = self.f2.name if self.hp1 <= 0 else self.f1.name

    def handle_event(self, ev):
        # איפוס קרב (R) - עובד רק כשהקרב נגמר
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r and self.over:
            self.__init__(self.app, self.f1, self.f2, self.mode)
            return

        if self.over: return

        # מקשי תנועה (חצים)
        keys = pygame.key.get_pressed()
        self.v1.x = 0
        if keys[pygame.K_LEFT]: self.v1.x = -280
        if keys[pygame.K_RIGHT]: self.v1.x = 280

        # מקשי פעולה (1-5)
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_1: self.try_attack("p1", "jab")
            elif ev.key == pygame.K_2: self.try_attack("p1", "kick")
            elif ev.key == pygame.K_3: self.try_attack("p1", "grapple")
            elif ev.key == pygame.K_4: self.block1_until = time.time() + 0.6
            elif ev.key == pygame.K_5: self.sta1 = clamp(self.sta1 + 15, 0, 100)

    def try_attack(self, who, move):
        now = time.time()
        cd = self.cooldowns[who]
        if now < cd[move]: return
        
        cost = {"jab":10, "kick":15, "grapple":20}[move]
        if who == "p1" and self.sta1 < cost: return
        if who == "p2" and self.sta2 < cost: return
        
        if who == "p1": self.sta1 -= cost
        else: self.sta2 -= cost
        
        cd[move] = now + {"jab":0.4, "kick":0.6, "grapple":0.8}[move]
        self.resolve_attack(who, move)

    def resolve_attack(self, who, move):
        dist = (self.p1 - self.p2).length()
        if dist > (135 if move != "grapple" else 90): return
        
        dmg = random.randint(6, 11) if move == "jab" else random.randint(13, 19)
        if (time.time() < self.block2_until if who == "p1" else time.time() < self.block1_until):
            dmg //= 2

        if who == "p1":
            self.hp2 = clamp(self.hp2 - dmg, 0, 100)
            self.p2_hit_timer = 0.15 # הפעלת הבהוב לשחקן 2
        else:
            self.hp1 = clamp(self.hp1 - dmg, 0, 100)
            self.p1_hit_timer = 0.15 # הפעלת הבהוב לשחקן 1

    def draw_fighter(self, surf, center, fighter_obj, main_color):
        SCALE = 1.6
        cx, cy = int(center.x), int(center.y)
        is_p1 = (center == self.p1)
        p_key = "p1" if is_p1 else "p2"
        dir_x = 1 if self.p1.x < self.p2.x else -1
        if not is_p1: dir_x *= -1

        t = time.time()
        # בדיקת מצבים לאנימציה
        is_punching = t < self.cooldowns[p_key].get("jab", 0)
        is_kicking = t < self.cooldowns[p_key].get("kick", 0)
        is_grappling = t < self.cooldowns[p_key].get("grapple", 0)
        is_blocking = (t < self.block1_until) if is_p1 else (t < self.block2_until)
        
        skin_base = getattr(fighter_obj, 'skin_color', (255, 224, 189))
        skin = (255, 100, 100) if ((self.p1_hit_timer > 0 if is_p1 else self.p2_hit_timer > 0)) else skin_base
        hair = getattr(fighter_obj, 'hair_color', (50, 30, 20))
        pants = getattr(fighter_obj, 'pants_color', (50, 50, 50))
        limb_thickness = int(14 * SCALE)

        # 1. רגליים וגוף (נשאר אותו דבר)
        pygame.draw.line(surf, skin, (cx - int(10*SCALE)*dir_x, cy + int(30*SCALE)), (cx - int(20*SCALE)*dir_x, cy + int(80*SCALE)), limb_thickness)
        if is_kicking:
            pygame.draw.line(surf, skin, (cx + int(10*SCALE)*dir_x, cy + int(30*SCALE)), (cx + int(55*SCALE)*dir_x, cy + int(15*SCALE)), limb_thickness)
        else:
            pygame.draw.line(surf, skin, (cx + int(10*SCALE)*dir_x, cy + int(30*SCALE)), (cx + int(20*SCALE)*dir_x, cy + int(80*SCALE)), limb_thickness)
        
        body_w, body_h = int(55*SCALE), int(70*SCALE)
        pygame.draw.ellipse(surf, skin, (cx - body_w//2, cy - int(20*SCALE), body_w, body_h))
        pygame.draw.rect(surf, pants, (cx - body_w//2, cy + int(25*SCALE), body_w, int(25*SCALE)), border_radius=6)

        # 2. ידיים וכפפות - הלוגיקה החדשה!
        f_hand_x, f_hand_y = cx + int(20*SCALE)*dir_x, cy - int(10*SCALE) # יד קדמית
        b_hand_x, b_hand_y = cx - int(15*SCALE)*dir_x, cy - int(5*SCALE) # יד אחורית

        if is_blocking:
            # שתי הידיים עולות לכיוון הראש
            f_hand_x, f_hand_y = cx + int(10*SCALE)*dir_x, cy - int(45*SCALE)
            b_hand_x, b_hand_y = cx - int(5*SCALE)*dir_x, cy - int(40*SCALE)
        elif is_grappling:
            # שתי הידיים נשלחות קדימה לתפיסה
            reach = int(40 * SCALE)
            f_hand_x += reach * dir_x
            b_hand_x += (reach + 20) * dir_x
            f_hand_y, b_hand_y = cy - int(15*SCALE), cy - int(15*SCALE)
        elif is_punching:
            f_hand_x += int(48 * SCALE) * dir_x

        # ציור הזרועות והכפפות
        pygame.draw.line(surf, skin, (cx + int(15*SCALE)*dir_x, cy - int(10*SCALE)), (f_hand_x, f_hand_y), limb_thickness)
        pygame.draw.line(surf, skin, (cx - int(10*SCALE)*dir_x, cy - int(5*SCALE)), (b_hand_x, b_hand_y), limb_thickness)
        pygame.draw.circle(surf, main_color, (f_hand_x, f_hand_y), int(15 * SCALE)) 
        pygame.draw.circle(surf, main_color, (b_hand_x, b_hand_y), int(13 * SCALE))

        # 3. ראש ושיער (עם התמיכה ב-AH Gordon)
        head_r = int(20 * SCALE)
        head_pos = (cx, cy - int(45*SCALE))
        if getattr(fighter_obj, 'hair_length', 'short') == 'long':
            pygame.draw.rect(surf, hair, (head_pos[0]-head_r, head_pos[1], head_r*2, int(25*SCALE)), border_bottom_left_radius=10, border_bottom_right_radius=10)
        pygame.draw.circle(surf, skin, head_pos, head_r)
        pygame.draw.arc(surf, hair, (head_pos[0]-head_r, head_pos[1]-head_r, head_r*2, head_r*2), 0, 3.14, int(12*SCALE))

    def draw(self, surf, mouse):
        surf.fill(BG)
        if self.arena_img: surf.blit(self.arena_img, self.arena.topleft)
        
        center_x = WIDTH // 2
        self.draw_bar(surf, center_x - 420, 40, 400, 25, self.f1.name, self.hp1, 100, RED)
        self.draw_bar(surf, center_x - 420, 70, 400, 12, "STA", self.sta1, 100, YELLOW)
        self.draw_bar(surf, center_x + 20, 40, 400, 25, self.f2.name, self.hp2, 100, BLUE)
        self.draw_bar(surf, center_x + 20, 70, 400, 12, "STA", self.sta2, 100, YELLOW)
        
        self.draw_fighter(surf, self.p1, self.f1, RED)
        self.draw_fighter(surf, self.p2, self.f2, BLUE)
        
        if self.over:
            overlay = pygame.Rect(WIDTH//2-250, HEIGHT//2-100, 500, 200)
            pygame.draw.rect(surf, PANEL, overlay, border_radius=20)
            pygame.draw.rect(surf, BORDER, overlay, width=3, border_radius=20)
            t1 = self.app.font_b.render(f"WINNER: {self.winner}", True, TEXT)
            t2 = self.app.font.render("Press R to Restart", True, MUTED)
            surf.blit(t1, t1.get_rect(center=(WIDTH//2, HEIGHT//2-20)))
            surf.blit(t2, t2.get_rect(center=(WIDTH//2, HEIGHT//2+40)))

    def draw_bar(self, surf, x, y, w, h, label, val, maxv, color):
        pygame.draw.rect(surf, (12, 12, 18), (x, y, w, h), border_radius=10)
        fill_w = int((w - 4) * (clamp(val, 0, maxv) / maxv))
        if fill_w > 0: pygame.draw.rect(surf, color, (x+2, y+2, fill_w, h-4), border_radius=10)
        if label != "STA":
            t = self.app.font_s.render(f"{label}: {int(val)}/100", True, TEXT)
            surf.blit(t, (x, y - 20))

    def ai_step(self, dt):
        if time.time() < self.stun2_until: return
        dist = (self.p1 - self.p2).length()
        dir_x = 1 if self.p1.x > self.p2.x else -1
        self.v2.x = dir_x * 240 if dist > 115 else 0
        if dist < 135 and random.random() < 0.03:
            self.try_attack("p2", "jab")

