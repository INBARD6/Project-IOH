"""
CombatEngine Class
מנוע הקרב - לוגיקה עסקית לסימולציית קרבות
מדגים: SoC (Separation of Concerns), לוגיקה עסקית
"""

import random
from fighter import Fighter
from striker import Striker
from grappler import Grappler


class CombatEngine:
    """
    מנוע לסימולציית קרבות בין לוחמים
    """
    
    def __init__(self):
        """אתחול מנוע הקרב"""
        self._fight_history = []
    
    @property
    def fight_history(self):
        """היסטוריית קרבות"""
        return self._fight_history.copy()
    
    def simulate_fight(self, fighter1: Fighter, fighter2: Fighter) -> dict:
        """
        סימולציה של קרב בין שני לוחמים
        
        Args:
            fighter1: לוחם ראשון
            fighter2: לוחם שני
            
        Returns:
            dict: תוצאות הקרב
        """
        print(f"\n🥊 קרב: {fighter1.name} vs {fighter2.name}")
        print("=" * 50)
        
        # חישוב יתרון
        fighter1_advantage = self._calculate_advantage(fighter1, fighter2)
        fighter2_advantage = self._calculate_advantage(fighter2, fighter1)
        
        # הוספת רנדומליות (מדמה את אי הוודאות בקרב)
        randomness = random.uniform(0.8, 1.2)
        fighter1_score = fighter1_advantage * randomness
        fighter2_score = fighter2_advantage * (2 - randomness)
        
        # קביעת מנצח
        if fighter1_score > fighter2_score:
            winner = fighter1
            loser = fighter2
            method = self._determine_win_method(fighter1)
        else:
            winner = fighter2
            loser = fighter1
            method = self._determine_win_method(fighter2)
        
        # עדכון סטטיסטיקות
        winner.add_win()
        loser.add_loss()
        
        # שמירת תוצאות
        result = {
            'fighter1': fighter1.name,
            'fighter2': fighter2.name,
            'winner': winner.name,
            'loser': loser.name,
            'method': method,
            'fighter1_score': round(fighter1_score, 2),
            'fighter2_score': round(fighter2_score, 2)
        }
        
        self._fight_history.append(result)
        
        # הצגת תוצאות
        print(f"\n🏆 מנצח: {winner.name} ב-{method}!")
        print(f"   ציון {fighter1.name}: {result['fighter1_score']}")
        print(f"   ציון {fighter2.name}: {result['fighter2_score']}")
        
        return result
    
    def _calculate_advantage(self, attacker: Fighter, defender: Fighter) -> float:
        """
        חישוב יתרון של לוחם על פני יריבו
        
        Args:
            attacker: התוקף
            defender: המגן
            
        Returns:
            float: ציון היתרון
        """
        base_skill = attacker.overall_skill
        
        # בונוס על סמך סוג הלוחם
        if isinstance(attacker, Striker) and isinstance(defender, Grappler):
            # Striker מול Grappler
            advantage = base_skill + (attacker.striking_power * 0.2)
        elif isinstance(attacker, Grappler) and isinstance(defender, Striker):
            # Grappler מול Striker
            advantage = base_skill + (attacker.grappling_skill * 0.2)
        else:
            # משחק סימטרי
            advantage = base_skill
        
        # בונוס לפי אחוז ניצחונות
        win_rate_bonus = attacker.win_percentage * 0.1
        
        return advantage + win_rate_bonus
    
    def _determine_win_method(self, winner: Fighter) -> str:
        """
        קביעת שיטת הניצחון על סמך סוג הלוחם
        
        Args:
            winner: הלוחם המנצח
            
        Returns:
            str: שיטת הניצחון
        """
        if isinstance(winner, Striker):
            methods = ["KO", "TKO", "Decision (Striking)"]
            weights = [0.4, 0.3, 0.3]
        elif isinstance(winner, Grappler):
            methods = ["Submission", "Decision (Grappling)", "Ground and Pound"]
            weights = [0.5, 0.3, 0.2]
        else:
            methods = ["Decision", "KO", "Submission"]
            weights = [0.4, 0.3, 0.3]
        
        return random.choices(methods, weights=weights)[0]
    
    def simulate_tournament(self, fighters: list) -> Fighter:
        """
        סימולציה של טורניר (בראקט חיסול)
        
        Args:
            fighters: רשימת לוחמים
            
        Returns:
            Fighter: המנצח בטורניר
        """
        if len(fighters) < 2:
            raise ValueError("נדרשים לפחות 2 לוחמים לטורניר")
        
        print(f"\n🏆 טורניר UFC - {len(fighters)} לוחמים!")
        print("=" * 60)
        
        current_round = fighters.copy()
        round_num = 1
        
        while len(current_round) > 1:
            print(f"\n--- סיבוב {round_num} ---")
            next_round = []
            
            # צמידות אקראיות
            random.shuffle(current_round)
            
            for i in range(0, len(current_round), 2):
                if i + 1 < len(current_round):
                    result = self.simulate_fight(current_round[i], current_round[i + 1])
                    # מציאת המנצח
                    winner = next(f for f in fighters if f.name == result['winner'])
                    next_round.append(winner)
                else:
                    # לוחם בודד עובר אוטומטית
                    next_round.append(current_round[i])
                    print(f"{current_round[i].name} עובר אוטומטית לסיבוב הבא")
            
            current_round = next_round
            round_num += 1
        
        champion = current_round[0]
        print(f"\n🏆🏆🏆 אלוף הטורניר: {champion.name}! 🏆🏆🏆")
        
        return champion
    
    def get_fight_stats(self) -> dict:
        """
        קבלת סטטיסטיקות על כל הקרבות
        
        Returns:
            dict: סטטיסטיקות
        """
        if not self._fight_history:
            return {'total_fights': 0, 'message': 'אין קרבות בהיסטוריה'}
        
        methods = [fight['method'] for fight in self._fight_history]
        method_counts = {}
        for method in methods:
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            'total_fights': len(self._fight_history),
            'methods_distribution': method_counts,
            'latest_fight': self._fight_history[-1]
        }
    
    def clear_history(self):
        """ניקוי היסטוריית קרבות"""
        self._fight_history.clear()
        print("היסטוריית הקרבות נוקתה")