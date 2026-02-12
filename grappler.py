"""
Grappler Class
מחלקה יורשת - לוחם מתמחה בהיאבקות
מדגימה: הורשה, פולימורפיזם
"""

from fighter import Fighter


class Grappler(Fighter):
    """
    לוחם מתמחה בהיאבקות (BJJ, Wrestling)
    """
    
    def __init__(self, fighter_id: int, name: str, weight_class: str,
                 wins: int = 0, losses: int = 0, draws: int = 0,
                 striking_power: int = 40, grappling_skill: int = 80,
                 submission_skill: int = 75, takedown_defense: int = 70):
        """
        אתחול Grappler
        
        Args:
            submission_skill: כישורי סאבמישן (0-100)
            takedown_defense: הגנת טייקדאון (0-100)
        """
        super().__init__(fighter_id, name, weight_class, wins, losses, draws,
                        striking_power, grappling_skill)
        self._submission_skill = max(0, min(100, submission_skill))
        self._takedown_defense = max(0, min(100, takedown_defense))
        self._submission_wins = 0
    
    @property
    def submission_skill(self):
        return self._submission_skill
    
    @property
    def takedown_defense(self):
        return self._takedown_defense
    
    @property
    def submission_wins(self):
        return self._submission_wins
    
    @property
    def overall_skill(self):
        """
        Override - חישוב כישורי כולל עם דגש על היאבקות
        פולימורפיזם
        """
        return (self._grappling_skill * 0.5 + 
                self._submission_skill * 0.3 + 
                self._takedown_defense * 0.15 +
                self._striking_power * 0.05)
    
    def add_submission_win(self):
        """הוספת ניצחון בסאבמישן"""
        self._submission_wins += 1
        self.add_win()
    
    def train_grappling(self):
        """אימון מיוחד להיאבקות"""
        improvement = 2
        self._grappling_skill = min(100, self._grappling_skill + improvement)
        self._submission_skill = min(100, self._submission_skill + improvement)
        return f"{self._name} שיפר כישורי היאבקות!"
    
    def __str__(self):
        """
        Override - הוספת מידע ספציפי ל-Grappler
        פולימורפיזם
        """
        base_str = super().__str__()
        return (f"{base_str}\n"
                f"  סאבמישן: {self._submission_skill}\n"
                f"  הגנת טייקדאון: {self._takedown_defense}\n"
                f"  ניצחונות בסאבמישן: {self._submission_wins}")
    
    def __repr__(self):
        """Override - ייצוג טכני"""
        return (f"Grappler(fighter_id={self._fighter_id}, name='{self._name}', "
                f"submission_skill={self._submission_skill})")
    
    def to_dict(self):
        """Override - הוספת שדות ספציפיים"""
        data = super().to_dict()
        data['fighter_type'] = 'Grappler'
        data['submission_skill'] = self._submission_skill
        data['takedown_defense'] = self._takedown_defense
        data['submission_wins'] = self._submission_wins
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        """יצירת Grappler ממילון"""
        return cls(
            fighter_id=data['fighter_id'],
            name=data['name'],
            weight_class=data['weight_class'],
            wins=data.get('wins', 0),
            losses=data.get('losses', 0),
            draws=data.get('draws', 0),
            striking_power=data.get('striking_power', 40),
            grappling_skill=data.get('grappling_skill', 80),
            submission_skill=data.get('submission_skill', 75),
            takedown_defense=data.get('takedown_defense', 70)
        )