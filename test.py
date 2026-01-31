"""
test_imports.py
בדיקה מהירה שכל הקבצים עובדים
"""

print("בודק imports...")

try:
    from fighter import Fighter
    print("✅ Fighter imported")
    
    from striker import Striker
    print("✅ Striker imported")
    
    from grappler import Grappler
    print("✅ Grappler imported")
    
    from hybrid_champion import HybridChampion
    print("✅ HybridChampion imported")
    
    from equipment import Equipment, TrainingGloves, StrikingPads
    print("✅ Equipment imported")
    
    from combat_engine import CombatEngine
    print("✅ CombatEngine imported")
    
    from repository import Repository
    print("✅ Repository imported")
    
    from cli_view import CLIView
    print("✅ CLIView imported")
    
    from MainController import MainController
    print("✅ MainController imported")
    
    print("\n🎉 כל ה-imports עובדים!")
    
    # בדיקה מהירה של יצירת לוחם
    print("\n--- בדיקת יצירת לוחם ---")
    f1 = Fighter(1, "Test Fighter", "Lightweight", striking_power=70, grappling_skill=60)
    print(f1)
    
    print("\n--- בדיקת Operator Overloading ---")
    f2 = Fighter(2, "Test Fighter 2", "Lightweight", striking_power=80, grappling_skill=80)
    print(f"האם f1 > f2? {f1 > f2}")
    print(f"האם f1 < f2? {f1 < f2}")
    
    print("\n--- בדיקת הורשה ---")
    striker = Striker(3, "Striker Test", "Welterweight", striking_power=90, speed=85)
    print(f"Striker overall skill: {striker.overall_skill:.2f}")
    
    grappler = Grappler(4, "Grappler Test", "Middleweight", grappling_skill=90, submission_skill=85)
    print(f"Grappler overall skill: {grappler.overall_skill:.2f}")
    
    print("\n--- בדיקת הורשה מרובה ---")
    hybrid = HybridChampion(5, "Hybrid Test", "Light Heavyweight")
    print(f"Hybrid overall skill: {hybrid.overall_skill:.2f}")
    print(f"MRO: {[cls.__name__ for cls in HybridChampion.__mro__]}")
    
    print("\n✅ כל הבדיקות עברו בהצלחה!")
    
except Exception as e:
    print(f"\n❌ שגיאה: {e}")
    import traceback
    traceback.print_exc()