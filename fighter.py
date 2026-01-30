import random
from abc import ABC, abstractmethod

class Fighter(ABC):
    """
    Abstract Base Class representing a fighter.
    Uses Encapsulation for HP and Stamina.
    """
    def __init__(self, name, weight, height, stats):
        self.name = name
        self.weight = weight
        self.height = height
        self.reach = self.height // 2
        
        # Stats dictionary (from your code)
        self.punch = stats.get('punch', 50)
        self.kick = stats.get('kick', 50)
        self.grappling = stats.get('grappling', 50)
        self.speed = stats.get('speed', 50)
        self.luck = stats.get('luck', 50)
        
        # Encapsulated attributes
        self._hp = 100
        self._stamina = stats.get('endurance', 10)
        self.wins = 0
        self.losses = 0
        self.is_champion = False

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = max(0, value)  # Prevent negative HP

    @property
    def total_score(self):
        return self.punch + self.kick + self.grappling + self.speed

    @property
    def salary(self):
        """Calculates salary based on your logic"""
        champion_bonus = 2 if self.is_champion else 1
        return (self.total_score * 1000) + (self.wins * 25000 * champion_bonus)

    @abstractmethod
    def attack(self, opponent):
        pass

    # Dunder Methods
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} (HP: {self.hp})>"

    def __gt__(self, other):
        return self.total_score > other.total_score

    def __add__(self, bonus):
        """Allows: fighter + 5 (adds to all stats)"""
        if isinstance(bonus, int):
            self.punch += bonus
            self.kick += bonus
            self.grappling += bonus
            return self
        raise ValueError("Bonus must be an integer")

# --- Specific Fighter Types (Inheritance) ---

class Striker(Fighter):
    def attack(self, opponent):
        # Logic based on Punch/Kick stats
        hit_chance = (self.speed + self.luck) / 200
        damage = (self.punch + self.kick) / 10
        
        if random.random() < hit_chance:
            opponent.hp -= damage
            return f"{self.name} landed a clean STRIKE! Dealt {damage:.1f} damage."
        else:
            return f"{self.name} missed the strike!"

class Grappler(Fighter):
    def attack(self, opponent):
        # Logic based on Grappling stats
        success_chance = (self.grappling + self.weight) / 300
        damage = self.grappling / 8
        
        if random.random() < success_chance:
            opponent.hp -= damage
            return f"{self.name} executed a TAKEDOWN! Dealt {damage:.1f} damage."
        else:
            return f"{self.name} failed the takedown attempt."

# --- Multiple Inheritance & MRO ---
class HybridChampion(Striker, Grappler):
    def __init__(self, name, weight, height, stats):
        super().__init__(name, weight, height, stats)
        self.is_champion = True # Default for Hybrid

    def attack(self, opponent):
        # Demonstrating MRO: calling the first parent's attack
        # Since Striker is first in (Striker, Grappler), it uses Striker logic
        result = super().attack(opponent) 
        return f"[HYBRID MOVE] {result}"