
from  equipment import Equipment

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