"""
Equipment Model Class
מחלקת Equipment - ציוד אימון ללוחמים
מדגימה: אנקפסולציה, הורשה
"""

class Equipment:
    """
    מחלקת בסיס לציוד אימון
    """
    
    def __init__(self, equipment_id: int, name: str, equipment_type: str, 
                 condition: int = 100, price: float = 0.0):
        """
        אתחול ציוד
        
        Args:
            equipment_id: מזהה ייחודי
            name: שם הציוד
            equipment_type: סוג הציוד (gloves, pads, etc)
            condition: מצב הציוד (0-100)
            price: מחיר
        """
        self._equipment_id = equipment_id
        self._name = name
        self._equipment_type = equipment_type
        self._condition = max(0, min(100, condition))
        self._price = price
    
    @property
    def equipment_id(self):
        return self._equipment_id
    
    @property
    def name(self):
        return self._name
    
    @property
    def equipment_type(self):
        return self._equipment_type
    
    @property
    def condition(self):
        return self._condition
    
    @property
    def price(self):
        return self._price
    
    def use_equipment(self, wear_amount: int = 5):
        """שימוש בציוד - פוגע במצב"""
        self._condition = max(0, self._condition - wear_amount)
        return self._condition > 0
    
    def repair(self, repair_amount: int = 20):
        """תיקון ציוד"""
        self._condition = min(100, self._condition + repair_amount)
    
    def __str__(self):
        """ייצוג טקסטואלי"""
        return (f"{self._name} ({self._equipment_type})\n"
                f"  מצב: {self._condition}%\n"
                f"  מחיר: ${self._price:.2f}")
    
    def __repr__(self):
        """ייצוג טכני"""
        return (f"Equipment(equipment_id={self._equipment_id}, "
                f"name='{self._name}', type='{self._equipment_type}')")
    
    def to_dict(self):
        """המרה למילון"""
        return {
            'equipment_id': self._equipment_id,
            'name': self._name,
            'equipment_type': self._equipment_type,
            'condition': self._condition,
            'price': self._price
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """יצירת ציוד ממילון"""
        return cls(
            equipment_id=data['equipment_id'],
            name=data['name'],
            equipment_type=data['equipment_type'],
            condition=data.get('condition', 100),
            price=data.get('price', 0.0)
        )




class StrikingPads(Equipment):
    """
    מחלקה יורשת - כריות אגרוף
    מדגימה: הורשה ורטיקלית
    """
    
    def __init__(self, equipment_id: int, name: str, pad_type: str = "Focus Mitts",
                 condition: int = 100, price: float = 80.0):
        """
        אתחול כריות
        
        Args:
            pad_type: סוג הכרית (Focus Mitts, Thai Pads, etc)
        """
        super().__init__(equipment_id, name, "Striking Pads", condition, price)
        self._pad_type = pad_type
    
    @property
    def pad_type(self):
        return self._pad_type
    
    def __str__(self):
        """Override - הוספת סוג כרית"""
        base_str = super().__str__()
        return f"{base_str}\n  סוג כרית: {self._pad_type}"
    
    def to_dict(self):
        """Override - הוספת סוג כרית"""
        data = super().to_dict()
        data['pad_type'] = self._pad_type
        return data