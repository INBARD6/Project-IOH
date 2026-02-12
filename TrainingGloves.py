
from  equipment import Equipment

class TrainingGloves(Equipment):
    """
    מחלקה יורשת - כפפות אימון
    מדגימה: הורשה ורטיקלית
    """
    
    def __init__(self, equipment_id: int, name: str, weight_oz: int = 16,
                 condition: int = 100, price: float = 50.0):
        """
        אתחול כפפות אימון
        
        Args:
            weight_oz: משקל הכפפות באונקיות
        """
        super().__init__(equipment_id, name, "Training Gloves", condition, price)
        self._weight_oz = weight_oz
    
    @property
    def weight_oz(self):
        return self._weight_oz
    
    def __str__(self):
        """Override - הוספת משקל"""
        base_str = super().__str__()
        return f"{base_str}\n  משקל: {self._weight_oz} oz"
    
    def to_dict(self):
        """Override - הוספת משקל"""
        data = super().to_dict()
        data['weight_oz'] = self._weight_oz
        return data
