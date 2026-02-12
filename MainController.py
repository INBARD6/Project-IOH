"""
MainController Class
הבקר הראשי - לוגיקת הבקרה של האפליקציה
מדגים: תבנית MVC (Controller), REPL Loop, SoC
"""

from cli_view import CLIView
from repository import Repository
from combat_engine import CombatEngine
from fighter import Fighter
from striker import Striker
from grappler import Grappler
from hybrid_champion import HybridChampion


class MainController:
    """
    הבקר הראשי - מתאם בין View, Model ו-Repository
    מדגים: תבנית MVC, הפרדת אחריות (SoC)
    """
    
    def __init__(self):
        """אתחול הבקר"""
        self._view = CLIView()
        self._repository = Repository()
        self._combat_engine = CombatEngine()
        self._running = False
        self._next_fighter_id = self._get_next_fighter_id()
    
    def _get_next_fighter_id(self) -> int:
        """חישוב ID הבא ללוחם חדש"""
        fighters = self._repository.get_all_fighters()
        if not fighters:
            return 1
        return max(f.fighter_id for f in fighters) + 1
    
    def run(self):
        """
        הפעלת REPL Loop - התחלת האפליקציה
        REPL: Read-Eval-Print Loop
        """
        self._running = True
        self._view.show_welcome()
        
        # REPL Loop
        while self._running:
            self._view.show_main_menu()
            choice = self._view.get_user_choice()
            
            # Eval - הפעלת הפעולה המבוקשת
            self._handle_choice(choice)
        
        self._view.show_goodbye()
    
    def _handle_choice(self, choice: str):
        """
        טיפול בבחירת המשתמש
        
        Args:
            choice: בחירת המשתמש מהתפריט
        """
        menu_actions = {
            '1': self._add_fighter,
            '2': self._show_all_fighters,
            '3': self._search_fighter,
            '4': self._simulate_fight,
            '5': self._simulate_tournament,
            '6': self._update_fighter,
            '7': self._delete_fighter,
            '8': self._show_fight_history,
            '9': self._show_statistics,
            '0': self._exit
        }
        
        action = menu_actions.get(choice)
        if action:
            action()
        else:
            self._view.show_error("בחירה לא חוקית")
    
    def _add_fighter(self):
        """הוספת לוחם חדש"""
        self._view.show_info("➕ הוספת לוחם חדש")
        
        # בחירת סוג לוחם
        self._view.show_fighter_types_menu()
        fighter_type = self._view.get_user_choice()
        
        # קבלת פרטים בסיסיים
        name = self._view.get_input("שם הלוחם: ")
        if not name:
            self._view.show_error("שם לא יכול להיות ריק")
            return
        
        # בחירת קטגוריית משקל
        weight_classes = self._view.show_weight_classes_menu()
        wc_choice = self._view.get_user_choice()
        try:
            weight_class = weight_classes[int(wc_choice) - 1]
        except (ValueError, IndexError):
            self._view.show_error("בחירה לא חוקית")
            return
        
        # יצירת הלוחם לפי הסוג
        try:
            if fighter_type == '1':
                fighter = self._create_basic_fighter(name, weight_class)
            elif fighter_type == '2':
                fighter = self._create_striker(name, weight_class)
            elif fighter_type == '3':
                fighter = self._create_grappler(name, weight_class)
            elif fighter_type == '4':
                fighter = self._create_hybrid_champion(name, weight_class)
            else:
                self._view.show_error("סוג לוחם לא חוקי")
                return
            
            # שמירה במסד נתונים
            if self._repository.add_fighter(fighter):
                self._view.show_success(f"הלוחם {name} נוסף בהצלחה!")
                self._view.display_fighter(fighter)
                self._next_fighter_id += 1
            
        except Exception as e:
            self._view.show_error(f"שגיאה ביצירת לוחם: {e}")
    
    def _create_basic_fighter(self, name: str, weight_class: str) -> Fighter:
        """יצירת לוחם רגיל"""
        striking = int(self._view.get_input("כוח מכה (0-100) [50]: ") or "50")
        grappling = int(self._view.get_input("כישורי היאבקות (0-100) [50]: ") or "50")
        
        return Fighter(
            fighter_id=self._next_fighter_id,
            name=name,
            weight_class=weight_class,
            striking_power=striking,
            grappling_skill=grappling
        )
    
    def _create_striker(self, name: str, weight_class: str) -> Striker:
        """יצירת Striker"""
        striking = int(self._view.get_input("כוח מכה (0-100) [85]: ") or "85")
        speed = int(self._view.get_input("מהירות (0-100) [75]: ") or "75")
        kick_power = int(self._view.get_input("כוח בעיטות (0-100) [70]: ") or "70")
        
        return Striker(
            fighter_id=self._next_fighter_id,
            name=name,
            weight_class=weight_class,
            striking_power=striking,
            speed=speed,
            kick_power=kick_power
        )
    
    def _create_grappler(self, name: str, weight_class: str) -> Grappler:
        """יצירת Grappler"""
        grappling = int(self._view.get_input("כישורי היאבקות (0-100) [80]: ") or "80")
        submission = int(self._view.get_input("כישורי סאבמישן (0-100) [75]: ") or "75")
        takedown_def = int(self._view.get_input("הגנת טייקדאון (0-100) [70]: ") or "70")
        
        return Grappler(
            fighter_id=self._next_fighter_id,
            name=name,
            weight_class=weight_class,
            grappling_skill=grappling,
            submission_skill=submission,
            takedown_defense=takedown_def
        )
    
    def _create_hybrid_champion(self, name: str, weight_class: str) -> HybridChampion:
        """יצירת HybridChampion"""
        self._view.show_info("יצירת אלוף היברידי - מאוזן בכל הדיסציפלינות")
        
        return HybridChampion(
            fighter_id=self._next_fighter_id,
            name=name,
            weight_class=weight_class,
            striking_power=75,
            grappling_skill=75,
            speed=70,
            kick_power=70,
            submission_skill=70,
            takedown_defense=70,
            versatility=85
        )
    
    def _show_all_fighters(self):
        """הצגת כל הלוחמים"""
        fighters = self._repository.get_all_fighters()
        
        if not fighters:
            self._view.show_error("אין לוחמים במערכת")
            return
        
        self._view.show_info(f"נמצאו {len(fighters)} לוחמים")
        
        # בחירת סוג תצוגה
        print("\n1. תצוגה פשוטה")
        print("2. תצוגה מפורטת")
        print("3. תצוגה מלאה")
        
        view_choice = self._view.get_user_choice()
        
        if view_choice == '1':
            self._view.display_fighters_list(fighters)
        elif view_choice == '2':
            self._view.display_fighters_table(fighters)
        elif view_choice == '3':
            for fighter in fighters:
                self._view.display_fighter(fighter)
        else:
            self._view.display_fighters_list(fighters)
    
    def _search_fighter(self):
        """חיפוש לוחם"""
        print("\n1. חיפוש לפי שם")
        print("2. חיפוש לפי ID")
        print("3. חיפוש לפי קטגוריית משקל")
        
        search_type = self._view.get_user_choice()
        
        if search_type == '1':
            name = self._view.get_input("הכנס שם לחיפוש: ")
            fighter = self._repository.get_fighter_by_name(name)
            if fighter:
                self._view.display_fighter(fighter)
            else:
                self._view.show_error(f"לא נמצא לוחם בשם '{name}'")
        
        elif search_type == '2':
            try:
                fighter_id = int(self._view.get_input("הכנס ID: "))
                fighter = self._repository.get_fighter_by_id(fighter_id)
                if fighter:
                    self._view.display_fighter(fighter)
                else:
                    self._view.show_error(f"לא נמצא לוחם עם ID {fighter_id}")
            except ValueError:
                self._view.show_error("ID חייב להיות מספר")
        
        elif search_type == '3':
            weight_classes = self._view.show_weight_classes_menu()
            wc_choice = self._view.get_user_choice()
            try:
                weight_class = weight_classes[int(wc_choice) - 1]
                fighters = self._repository.get_fighters_by_weight_class(weight_class)
                if fighters:
                    self._view.display_fighters_list(fighters)
                else:
                    self._view.show_error(f"לא נמצאו לוחמים בקטגוריה {weight_class}")
            except (ValueError, IndexError):
                self._view.show_error("בחירה לא חוקית")
#המשחק עצמו
    def _simulate_fight(self):
        """סימולציית קרב"""
        fighters = self._repository.get_all_fighters()
        
        if len(fighters) < 2:
            self._view.show_error("נדרשים לפחות 2 לוחמים לקרב")
            return
        
        self._view.show_info("בחר שני לוחמים לקרב:")
        self._view.display_fighters_list(fighters)
        
        try:
            id1 = int(self._view.get_input("ID לוחם ראשון: "))
            id2 = int(self._view.get_input("ID לוחם שני: "))
            
            fighter1 = self._repository.get_fighter_by_id(id1)
            fighter2 = self._repository.get_fighter_by_id(id2)
            
            if not fighter1 or not fighter2:
                self._view.show_error("אחד הלוחמים לא נמצא")
                return
            
            if fighter1 == fighter2:
                self._view.show_error("לא ניתן להילחם מול עצמך")
                return
            
            # סימולציית הקרב
            result = self._combat_engine.simulate_fight(fighter1, fighter2)
            
            # עדכון במסד נתונים
            self._repository.update_fighter(fighter1)
            self._repository.update_fighter(fighter2)
            self._repository.save_fight_result(result)
            
            self._view.show_success("הקרב הסתיים ונשמר במערכת!")
            
        except ValueError:
            self._view.show_error("יש להזין מספרים בלבד")
    
    def _simulate_tournament(self):
        """סימולציית טורניר"""
        fighters = self._repository.get_all_fighters()
        
        if len(fighters) < 2:
            self._view.show_error("נדרשים לפחות 2 לוחמים לטורניר")
            return
        
        self._view.show_info(f"יש {len(fighters)} לוחמים זמינים")
        
        # בחירת מספר משתתפים
        try:
            num_fighters = int(self._view.get_input("כמה לוחמים בטורניר? (2-8): "))
            if num_fighters < 2 or num_fighters > min(8, len(fighters)):
                self._view.show_error("מספר לא חוקי")
                return
        except ValueError:
            self._view.show_error("יש להזין מספר")
            return
        
        # בחירת לוחמים
        self._view.display_fighters_list(fighters)
        selected_fighters = []
        
        for i in range(num_fighters):
            try:
                fighter_id = int(self._view.get_input(f"ID לוחם #{i+1}: "))
                fighter = self._repository.get_fighter_by_id(fighter_id)
                if fighter and fighter not in selected_fighters:
                    selected_fighters.append(fighter)
                else:
                    self._view.show_error("לוחם לא נמצא או כבר נבחר")
                    return
            except ValueError:
                self._view.show_error("יש להזין מספר")
                return
        
        # הרצת הטורניר
        if self._view.confirm_action("להתחיל את הטורניר?"):
            champion = self._combat_engine.simulate_tournament(selected_fighters)
            
            # עדכון כל הלוחמים במסד נתונים
            for fighter in selected_fighters:
                self._repository.update_fighter(fighter)
            
            self._view.show_success(f"הטורניר הסתיים! האלוף: {champion.name}")
    
    def _update_fighter(self):
        """עדכון לוחם"""
        fighter_id = int(self._view.get_input("הכנס ID של לוחם לעדכון: "))
        fighter = self._repository.get_fighter_by_id(fighter_id)
        
        if not fighter:
            self._view.show_error(f"לוחם {fighter_id} לא נמצא")
            return
        
        self._view.display_fighter(fighter)
        
        print("\nמה תרצה לעדכן?")
        print("1. שם")
        print("2. הוספת ניצחון")
        print("3. הוספת הפסד")
        print("4. שיפור כישורים")
        
        choice = self._view.get_user_choice()
        
        if choice == '1':
            new_name = self._view.get_input("שם חדש: ")
            fighter.name = new_name
        elif choice == '2':
            fighter.add_win()
        elif choice == '3':
            fighter.add_loss()
        elif choice == '4':
            if isinstance(fighter, Striker):
                fighter.train_striking()
            elif isinstance(fighter, Grappler):
                fighter.train_grappling()
            else:
                self._view.show_info("לוחם זה אינו יכול להתאמן באופן ספציפי")
                return
        
        if self._repository.update_fighter(fighter):
            self._view.show_success("הלוחם עודכן בהצלחה!")
    
    def _delete_fighter(self):
        """מחיקת לוחם"""
        fighter_id = int(self._view.get_input("הכנס ID של לוחם למחיקה: "))
        fighter = self._repository.get_fighter_by_id(fighter_id)
        
        if not fighter:
            self._view.show_error(f"לוחם {fighter_id} לא נמצא")
            return
        
        self._view.display_fighter(fighter)
        
        if self._view.confirm_action(f"האם אתה בטוח שברצונך למחוק את {fighter.name}?"):
            if self._repository.delete_fighter(fighter_id):
                self._view.show_success("הלוחם נמחק בהצלחה")
    
    def _show_fight_history(self):
        """הצגת היסטוריית קרבות"""
        try:
            limit = int(self._view.get_input("כמה קרבות להציג? [10]: ") or "10")
            fights = self._repository.get_fight_history(limit)
            self._view.display_fight_history(fights)
        except ValueError:
            self._view.show_error("יש להזין מספר")
    
    def _show_statistics(self):
        """הצגת סטטיסטיקות"""
        db_stats = self._repository.get_statistics()
        combat_stats = self._combat_engine.get_fight_stats()
        
        combined_stats = {**db_stats, **combat_stats}
        self._view.display_statistics(combined_stats)
    
    def _exit(self):
        """יציאה מהתוכנית"""
        if self._view.confirm_action("האם אתה בטוח שברצונך לצאת?"):
            self._running = False


# נקודת כניסה לתוכנית
if __name__ == "__main__":
    controller = MainController()
    controller.run()