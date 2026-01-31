"""
Striker Class
מחלקה יורשת - לוחם מתמחה במכות
מדגימה: הורשה, פולימורפיזם
"""

from fighter import Fighter


class Striker(Fighter):
    """
    לוחם מתמחה במכות (Boxing, Muay Thai, Kickboxing)
    """
    
    def __init__(self, fighter_id: int, name: str, weight_class: str,
                 wins: int = 0, losses: int = 0, draws: int = 0,
                 striking_power: int = 85, grappling_skill: int = 45,
                 speed: int = 75, kick_power: int = 70):
        """
        אתחול Striker
        
        Args:
            speed: מהירות מכות (0-100)
            kick_power: כוח בעיטות (0-100)
        """
        super().__init__(fighter_id, name, weight_class, wins, losses, draws,
                        striking_power, grappling_skill)
        self._speed = max(0, min(100, speed))
        self._kick_power = max(0, min(100, kick_power))
        self._knockout_wins = 0
    
    @property
    def speed(self):
        return self._speed
    
    @property
    def kick_power(self):
        return self._kick_power
    
    @property
    def knockout_wins(self):
        return self._knockout_wins
    
    @property
    def overall_skill(self):
        """
        Override - חישוב כישורי כולל עם דגש על מכות
        פולימורפיזם
        """
        return (self._striking_power * 0.4 + 
                self._speed * 0.3 + 
                self._kick_power * 0.2 +
                self._grappling_skill * 0.1)
    
    def add_knockout_win(self):
        """הוספת ניצחון נוקאאוט"""
        self._knockout_wins += 1
        self.add_win()
    
    def train_striking(self):
        """אימון מיוחד למכות"""
        improvement = 2
        self._striking_power = min(100, self._striking_power + improvement)
        self._speed = min(100, self._speed + improvement)
        return f"{self._name} שיפר כישורי מכות!"
    
    def __str__(self):
        """
        Override - הוספת מידע ספציפי ל-Striker
        פולימורפיזם
        """
        base_str = super().__str__()
        return (f"{base_str}\n"
                f"  מהירות: {self._speed}\n"
                f"  כוח בעיטות: {self._kick_power}\n"
                f"  ניצחונות נוקאאוט: {self._knockout_wins}")
    
    def __repr__(self):
        """Override - ייצוג טכני"""
        return (f"Striker(fighter_id={self._fighter_id}, name='{self._name}', "
                f"speed={self._speed})")
    
    def to_dict(self):
        """Override - הוספת שדות ספציפיים"""
        data = super().to_dict()
        data['fighter_type'] = 'Striker'
        data['speed'] = self._speed
        data['kick_power'] = self._kick_power
        data['knockout_wins'] = self._knockout_wins
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        """יצירת Striker ממילון"""
        return cls(
            fighter_id=data['fighter_id'],
            name=data['name'],
            weight_class=data['weight_class'],
            wins=data.get('wins', 0),
            losses=data.get('losses', 0),
            draws=data.get('draws', 0),
            striking_power=data.get('striking_power', 85),
            grappling_skill=data.get('grappling_skill', 45),
            speed=data.get('speed', 75),
            kick_power=data.get('kick_power', 70)
        )