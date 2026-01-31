"""
HybridChampion Class
מחלקה עם הורשה מרובה - לוחם שמשלב מכות והיאבקות
מדגימה: הורשה מרובה, MRO (Method Resolution Order)
"""

from striker import Striker
from grappler import Grappler


class HybridChampion(Striker, Grappler):
    """
    אלוף היברידי - משלב את שתי הדיסציפלינות
    מדגים הורשה מרובה ו-MRO
    """
    
    def __init__(self, fighter_id: int, name: str, weight_class: str,
                 wins: int = 0, losses: int = 0, draws: int = 0,
                 striking_power: int = 75, grappling_skill: int = 75,
                 speed: int = 70, kick_power: int = 70,
                 submission_skill: int = 70, takedown_defense: int = 70,
                 versatility: int = 85):
        """
        אתחול אלוף היברידי
        
        Args:
            versatility: רב-תחומיות (0-100)
        """
        # קריאה ל-__init__ של Striker (בגלל MRO)
        Striker.__init__(self, fighter_id, name, weight_class, wins, losses, 
                        draws, striking_power, grappling_skill, speed, kick_power)
        
        # הוספה ידנית של תכונות Grappler
        self._submission_skill = max(0, min(100, submission_skill))
        self._takedown_defense = max(0, min(100, takedown_defense))
        self._submission_wins = 0
        
        # תכונה ייחודית
        self._versatility = max(0, min(100, versatility))
        self._title_defenses = 0
    
    @property
    def versatility(self):
        return self._versatility
    
    @property
    def title_defenses(self):
        return self._title_defenses
    
    @property
    def overall_skill(self):
        """
        Override - חישוב מאוזן לאלוף היברידי
        פולימורפיזם - משלב את כל הכישורים
        """
        return (self._striking_power * 0.25 + 
                self._grappling_skill * 0.25 + 
                self._speed * 0.15 +
                self._submission_skill * 0.15 +
                self._versatility * 0.2)
    
    def defend_title(self):
        """הגנה על התואר"""
        self._title_defenses += 1
        self.add_win()
        return f"{self._name} הגן על התואר בהצלחה! ({self._title_defenses} הגנות)"
    
    def train_complete_mma(self):
        """אימון מקיף ב-MMA"""
        self._striking_power = min(100, self._striking_power + 1)
        self._grappling_skill = min(100, self._grappling_skill + 1)
        self._versatility = min(100, self._versatility + 2)
        return f"{self._name} ביצע אימון MMA מקיף!"
    
    def __str__(self):
        """
        Override - הצגה מלאה של אלוף היברידי
        """
        base_str = Striker.__str__(self)  # מתחיל מ-Striker (MRO)
        return (f"{base_str}\n"
                f"  סאבמישן: {self._submission_skill}\n"
                f"  הגנת טייקדאון: {self._takedown_defense}\n"
                f"  רב-תחומיות: {self._versatility}\n"
                f"  הגנות על תואר: {self._title_defenses}\n"
                f"  MRO: {[cls.__name__ for cls in HybridChampion.__mro__]}")
    
    def __repr__(self):
        """Override - ייצוג טכני"""
        return (f"HybridChampion(fighter_id={self._fighter_id}, "
                f"name='{self._name}', versatility={self._versatility})")
    
    def to_dict(self):
        """Override - שילוב כל השדות"""
        data = Striker.to_dict(self)
        data['fighter_type'] = 'HybridChampion'
        data['submission_skill'] = self._submission_skill
        data['takedown_defense'] = self._takedown_defense
        data['submission_wins'] = self._submission_wins
        data['versatility'] = self._versatility
        data['title_defenses'] = self._title_defenses
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        """יצירת HybridChampion ממילון"""
        return cls(
            fighter_id=data['fighter_id'],
            name=data['name'],
            weight_class=data['weight_class'],
            wins=data.get('wins', 0),
            losses=data.get('losses', 0),
            draws=data.get('draws', 0),
            striking_power=data.get('striking_power', 75),
            grappling_skill=data.get('grappling_skill', 75),
            speed=data.get('speed', 70),
            kick_power=data.get('kick_power', 70),
            submission_skill=data.get('submission_skill', 70),
            takedown_defense=data.get('takedown_defense', 70),
            versatility=data.get('versatility', 85)
        )
    
    @staticmethod
    def show_mro():
        """הצגת MRO (Method Resolution Order)"""
        print("Method Resolution Order (MRO) של HybridChampion:")
        for i, cls in enumerate(HybridChampion.__mro__, 1):
            print(f"  {i}. {cls.__name__}")