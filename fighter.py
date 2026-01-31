"""
Fighter Model Class
מחלקת Fighter - ישות מודל המייצגת לוחם ב-UFC
מדגימה: אנקפסולציה, Dunder Methods, Operator Overloading
"""

class Fighter:
    """
    מחלקה המייצגת לוחם UFC
    """
    
    def __init__(self, fighter_id: int, name: str, weight_class: str, 
                 wins: int = 0, losses: int = 0, draws: int = 0, 
                 striking_power: int = 50, grappling_skill: int = 50):
        """
        אתחול לוחם
        
        Args:
            fighter_id: מזהה ייחודי
            name: שם הלוחם
            weight_class: קטגוריית משקל
            wins: מספר ניצחונות
            losses: מספר הפסדים
            draws: מספר תיקו
            striking_power: כוח מכה (0-100)
            grappling_skill: כישורי היאבקות (0-100)
        """
        self._fighter_id = fighter_id
        self._name = name
        self._weight_class = weight_class
        self._wins = wins
        self._losses = losses
        self._draws = draws
        self._striking_power = max(0, min(100, striking_power))
        self._grappling_skill = max(0, min(100, grappling_skill))
    
    # Properties לאנקפסולציה
    @property
    def fighter_id(self):
        return self._fighter_id
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if not value or not isinstance(value, str):
            raise ValueError("שם הלוחם חייב להיות מחרוזת לא ריקה")
        self._name = value
    
    @property
    def weight_class(self):
        return self._weight_class
    
    @property
    def wins(self):
        return self._wins
    
    @property
    def losses(self):
        return self._losses
    
    @property
    def draws(self):
        return self._draws
    
    @property
    def striking_power(self):
        return self._striking_power
    
    @property
    def grappling_skill(self):
        return self._grappling_skill
    
    @property
    def total_fights(self):
        """סך כל הקרבות"""
        return self._wins + self._losses + self._draws
    
    @property
    def win_percentage(self):
        """אחוז ניצחונות"""
        if self.total_fights == 0:
            return 0.0
        return (self._wins / self.total_fights) * 100
    
    @property
    def overall_skill(self):
        """ציון כישורי כולל"""
        return (self._striking_power + self._grappling_skill) / 2
    
    def add_win(self):
        """הוספת ניצחון"""
        self._wins += 1
    
    def add_loss(self):
        """הוספת הפסד"""
        self._losses += 1
    
    def add_draw(self):
        """הוספת תיקו"""
        self._draws += 1
    
    # Dunder Methods
    def __str__(self):
        """ייצוג טקסטואלי לקריאה"""
        return (f"{self._name} ({self._weight_class})\n"
                f"  רקורד: {self._wins}-{self._losses}-{self._draws}\n"
                f"  אחוז ניצחונות: {self.win_percentage:.1f}%\n"
                f"  כוח מכה: {self._striking_power}, היאבקות: {self._grappling_skill}")
    
    def __repr__(self):
        """ייצוג טכני למפתחים"""
        return (f"Fighter(fighter_id={self._fighter_id}, name='{self._name}', "
                f"weight_class='{self._weight_class}')")
    
    # Operator Overloading
    def __eq__(self, other):
        """השוואת שוויון (==)"""
        if not isinstance(other, Fighter):
            return False
        return self._fighter_id == other._fighter_id
    
    def __lt__(self, other):
        """השוואת קטן מ (<)"""
        if not isinstance(other, Fighter):
            return NotImplemented
        return self.overall_skill < other.overall_skill
    
    def __gt__(self, other):
        """השוואת גדול מ (>)"""
        if not isinstance(other, Fighter):
            return NotImplemented
        return self.overall_skill > other.overall_skill
    
    def __add__(self, other):
        """Operator Overloading - יצירת לוחם היברידי"""
        if not isinstance(other, Fighter):
            return NotImplemented
        
        new_name = f"{self._name} + {other._name} Hybrid"
        avg_striking = (self._striking_power + other._striking_power) // 2
        avg_grappling = (self._grappling_skill + other._grappling_skill) // 2
        
        return Fighter(
            fighter_id=0,
            name=new_name,
            weight_class=self._weight_class,
            striking_power=avg_striking,
            grappling_skill=avg_grappling
        )
    
    def to_dict(self):
        """המרה למילון"""
        return {
            'fighter_id': self._fighter_id,
            'name': self._name,
            'weight_class': self._weight_class,
            'wins': self._wins,
            'losses': self._losses,
            'draws': self._draws,
            'striking_power': self._striking_power,
            'grappling_skill': self._grappling_skill
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """יצירת לוחם ממילון"""
        return cls(
            fighter_id=data['fighter_id'],
            name=data['name'],
            weight_class=data['weight_class'],
            wins=data.get('wins', 0),
            losses=data.get('losses', 0),
            draws=data.get('draws', 0),
            striking_power=data.get('striking_power', 50),
            grappling_skill=data.get('grappling_skill', 50)
        )