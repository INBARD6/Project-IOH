"""
CLI View Class
שכבת התצוגה - ממשק משתמש CLI
מדגים: SoC, תבנית MVC (View)
"""

from typing import List
from fighter import Fighter


class CLIView:
    """
    מחלקת תצוגה - אחראית על כל הקלט והפלט מהמשתמש
    """
    
    def __init__(self):
        """אתחול תצוגה"""
        self._colors = {
            'HEADER': '\033[95m',
            'BLUE': '\033[94m',
            'GREEN': '\033[92m',
            'YELLOW': '\033[93m',
            'RED': '\033[91m',
            'ENDC': '\033[0m',
            'BOLD': '\033[1m'
        }
    
    def show_welcome(self):
        """הצגת מסך פתיחה"""
        print(f"\n{self._colors['BOLD']}{self._colors['HEADER']}")
        print("=" * 60)
        print("         🥊 Managment System UFC - Ultimate Fighting Championship 🥊")
        print("=" * 60)
        print(f"{self._colors['ENDC']}")
        print(f"{self._colors['BLUE']}OOP Project - Python OOP{self._colors['ENDC']}\n")
    
    def show_main_menu(self):
        """הצגת תפריט ראשי"""
        print(f"\n{self._colors['BOLD']}📋 תפריט ראשי:{self._colors['ENDC']}")
        print(f"{self._colors['GREEN']}1.{self._colors['ENDC']} Add Fighter")
        print(f"{self._colors['GREEN']}2.{self._colors['ENDC']} Show All Fighters")
        print(f"{self._colors['GREEN']}3.{self._colors['ENDC']} Search Fighter")
        print(f"{self._colors['GREEN']}4.{self._colors['ENDC']} Simulate Fight")
        print(f"{self._colors['GREEN']}5.{self._colors['ENDC']} Simulate Tournament")
        print(f"{self._colors['GREEN']}6.{self._colors['ENDC']} Update Fighter")
        print(f"{self._colors['GREEN']}7.{self._colors['ENDC']} Delete Fighter")
        print(f"{self._colors['GREEN']}8.{self._colors['ENDC']} Fight History")
        print(f"{self._colors['GREEN']}9.{self._colors['ENDC']} Statistics")
        print(f"{self._colors['RED']}0.{self._colors['ENDC']} Exit")
        print("-" * 60)
    
    def get_user_choice(self) -> str:
        """קבלת בחירת משתמש"""
        return input(f"{self._colors['YELLOW']}👉 בחר אופציה: {self._colors['ENDC']}").strip()
    
    def get_input(self, prompt: str) -> str:
        """קבלת קלט מהמשתמש"""
        return input(f"{self._colors['BLUE']}{prompt}{self._colors['ENDC']}").strip()
    
    def show_fighter_types_menu(self):
        """הצגת תפריט סוגי לוחמים"""
        print(f"\n{self._colors['BOLD']}🥋 Choose fighter type:{self._colors['ENDC']}")
        print(f"{self._colors['GREEN']}1.{self._colors['ENDC']} Fighter (Normal fighter)")
        print(f"{self._colors['GREEN']}2.{self._colors['ENDC']} Striker (Striking specialist)")
        print(f"{self._colors['GREEN']}3.{self._colors['ENDC']} Grappler (Grappling specialist)")
        print(f"{self._colors['GREEN']}4.{self._colors['ENDC']} HybridChampion (Well-rounded fighter)")
    
    def show_weight_classes_menu(self):
        """הצגת קטגוריות משקל"""
        print(f"\n{self._colors['BOLD']}⚖️ Weight Classes Available:{self._colors['ENDC']}")
        classes = [
            "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
            "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
        ]
        for i, wc in enumerate(classes, 1):
            print(f"{self._colors['GREEN']}{i}.{self._colors['ENDC']} {wc}")
        return classes
    
    def display_fighter(self, fighter: Fighter):
        """הצגת פרטי לוחם בודד"""
        print(f"\n{self._colors['BOLD']}{self._colors['HEADER']}{'=' * 60}{self._colors['ENDC']}")
        print(f"{self._colors['BOLD']}🥊 {fighter.name}{self._colors['ENDC']}")
        print(f"{self._colors['HEADER']}{'=' * 60}{self._colors['ENDC']}")
        print(fighter)
        print(f"{self._colors['HEADER']}{'=' * 60}{self._colors['ENDC']}\n")
    
    def display_fighters_list(self, fighters: List[Fighter]):
        """הצגת רשימת לוחמים"""
        if not fighters:
            self.show_error("No fighters found")
            return
        
        print(f"\n{self._colors['BOLD']}{self._colors['HEADER']}")
        print("=" * 100)
        print(f"{'ID':<5} {'Name':<25} {'Category':<20} {'Record':<15} {'Win Percentage':<15}")
        print("=" * 100)
        print(f"{self._colors['ENDC']}")
        
        for fighter in fighters:
            record = f"{fighter.wins}-{fighter.losses}-{fighter.draws}"
            win_pct = f"{fighter.win_percentage:.1f}%"
            print(f"{fighter.fighter_id:<5} {fighter.name:<25} {fighter.weight_class:<20} "
                  f"{record:<15} {win_pct:<15}")
        
        print(f"{self._colors['HEADER']}{'=' * 100}{self._colors['ENDC']}\n")
    
    def display_fighters_table(self, fighters: List[Fighter]):
        """הצגת טבלה מפורטת של לוחמים"""
        if not fighters:
            self.show_error("No fighters found")
            return
        
        print(f"\n{self._colors['BOLD']}{self._colors['HEADER']}")
        print("=" * 120)
        print(f"{'ID':<5} {'Name':<20} {'Category':<15} {'W-L-D':<12} {'Striking':<8} "
              f"{'Grappling':<10} {'Overall Skill':<12}")
        print("=" * 120)
        print(f"{self._colors['ENDC']}")
        
        for f in fighters:
            record = f"{f.wins}-{f.losses}-{f.draws}"
            skill = f"{f.overall_skill:.1f}"
            print(f"{f.fighter_id:<5} {f.name:<20} {f.weight_class:<15} {record:<12} "
                  f"{f.striking_power:<8} {f.grappling_skill:<10} {skill:<12}")
        
        print(f"{self._colors['HEADER']}{'=' * 120}{self._colors['ENDC']}\n")
    
    def display_fight_history(self, fights: List[dict]):
        """הצגת היסטוריית קרבות"""
        if not fights:
            self.show_error("No fights in history")
            return
        
        print(f"\n{self._colors['BOLD']}{self._colors['HEADER']}")
        print("=" * 100)
        print("📜 Fight History")
        print("=" * 100)
        print(f"{self._colors['ENDC']}")
        
        for fight in fights:
            print(f"\n{self._colors['BOLD']}Fight #{fight.get('fight_id', 'N/A')}:{self._colors['ENDC']}")
            print(f"  {fight['fighter1']} vs {fight['fighter2']}")
            print(f"  {self._colors['GREEN']}🏆 Winnner: {fight['winner']}{self._colors['ENDC']}")
            print(f"  שיטה: {fight['method']}")
            if 'date' in fight:
                print(f"  Date: {fight['date']}")
        
        print(f"\n{self._colors['HEADER']}{'=' * 100}{self._colors['ENDC']}\n")
    
    def display_statistics(self, stats: dict):
        """הצגת סטטיסטיקות"""
        print(f"\n{self._colors['BOLD']}{self._colors['HEADER']}")
        print("=" * 60)
        print("📊 System Statistics")
        print("=" * 60)
        print(f"{self._colors['ENDC']}")
        
        for key, value in stats.items():
            formatted_key = key.replace('_', ' ').title()
            print(f"{self._colors['BLUE']}{formatted_key}:{self._colors['ENDC']} {value}")
        
        print(f"{self._colors['HEADER']}{'=' * 60}{self._colors['ENDC']}\n")
    
    def show_success(self, message: str):
        """הצגת הודעת הצלחה"""
        print(f"{self._colors['GREEN']}✅ {message}{self._colors['ENDC']}")
    
    def show_error(self, message: str):
        """הצגת הודעת שגיאה"""
        print(f"{self._colors['RED']}❌ {message}{self._colors['ENDC']}")
    
    def show_info(self, message: str):
        """הצגת הודעת מידע"""
        print(f"{self._colors['BLUE']}ℹ️  {message}{self._colors['ENDC']}")
    
    def show_warning(self, message: str):
        """הצגת אזהרה"""
        print(f"{self._colors['YELLOW']}⚠️  {message}{self._colors['ENDC']}")
    
    def confirm_action(self, message: str) -> bool:
        """בקשת אישור מהמשתמש"""
        response = self.get_input(f"{message} (y/n): ").lower()
        return response in ['y', 'yes', 'כן']
    
    def show_goodbye(self):
        """הצגת הודעת פרידה"""
        print(f"\n{self._colors['BOLD']}{self._colors['HEADER']}")
        print("=" * 60)
        print("         🥊 Thanks for playing UFC! Goodbye! 🥊")
        print("=" * 60)
        print(f"{self._colors['ENDC']}\n")
    
    def pause(self):
        """המתנה ללחיצת Enter"""
        input(f"\n{self._colors['YELLOW']}לחץ Enter להמשך...{self._colors['ENDC']}")
    
    def clear_screen(self):
        """ניקוי מסך (אופציונלי)"""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')