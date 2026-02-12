"""
Repository Class
שכבת הנתונים - ניהול מסד נתונים SQLite
מדגים: SoC, CRUD Operations, Persistence
"""

import sqlite3
from typing import List, Optional
from fighter import Fighter
from striker import Striker
from grappler import Grappler
from hybrid_champion import HybridChampion


class Repository:
    """
    מחלקה לניהול מסד נתונים SQLite
    מדגימה: שכבת גישה לנתונים (Data Access Layer)
    """
    
    def __init__(self, db_name: str = "ufc_database.db"):
        """
        אתחול מסד נתונים
        
        Args:
            db_name: שם קובץ מסד הנתונים
        """
        self._db_name = db_name
        self._create_tables()
    
    def _get_connection(self):
        """יצירת חיבור למסד נתונים"""
        return sqlite3.connect(self._db_name)
    
    def _create_tables(self):
        """יצירת טבלאות במסד נתונים"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # טבלת לוחמים
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fighters (
                fighter_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                weight_class TEXT NOT NULL,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                striking_power INTEGER DEFAULT 50,
                grappling_skill INTEGER DEFAULT 50,
                fighter_type TEXT DEFAULT 'Fighter',
                speed INTEGER,
                kick_power INTEGER,
                knockout_wins INTEGER,
                submission_skill INTEGER,
                takedown_defense INTEGER,
                submission_wins INTEGER,
                versatility INTEGER,
                title_defenses INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # טבלת קרבות
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fights (
                fight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fighter1_name TEXT NOT NULL,
                fighter2_name TEXT NOT NULL,
                winner_name TEXT NOT NULL,
                method TEXT NOT NULL,
                fighter1_score REAL,
                fighter2_score REAL,
                fight_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ מסד נתונים '{self._db_name}' אותחל בהצלחה")
    
    # CRUD Operations - CREATE
    def add_fighter(self, fighter: Fighter) -> bool:
        """
        הוספת לוחם למסד נתונים
        
        Args:
            fighter: אובייקט לוחם
            
        Returns:
            bool: האם ההוספה הצליחה
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            data = fighter.to_dict()
            
            cursor.execute('''
                INSERT INTO fighters (
                    fighter_id, name, weight_class, wins, losses, draws,
                    striking_power, grappling_skill, fighter_type,
                    speed, kick_power, knockout_wins,
                    submission_skill, takedown_defense, submission_wins,
                    versatility, title_defenses
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['fighter_id'],
                data['name'],
                data['weight_class'],
                data['wins'],
                data['losses'],
                data['draws'],
                data['striking_power'],
                data['grappling_skill'],
                data.get('fighter_type', 'Fighter'),
                data.get('speed'),
                data.get('kick_power'),
                data.get('knockout_wins'),
                data.get('submission_skill'),
                data.get('takedown_defense'),
                data.get('submission_wins'),
                data.get('versatility'),
                data.get('title_defenses')
            ))
            
            conn.commit()
            conn.close()
            print(f"✅ {fighter.name} נוסף למסד הנתונים")
            return True
            
        except sqlite3.IntegrityError:
            print(f"❌ שגיאה: לוחם עם ID {fighter.fighter_id} כבר קיים")
            return False
        except Exception as e:
            print(f"❌ שגיאה בהוספת לוחם: {e}")
            return False
    
    # CRUD Operations - READ
    def get_fighter_by_id(self, fighter_id: int) -> Optional[Fighter]:
        """
        קריאת לוחם לפי מזהה
        
        Args:
            fighter_id: מזהה הלוחם
            
        Returns:
            Fighter או None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM fighters WHERE fighter_id = ?', (fighter_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_fighter(row)
    
    def get_fighter_by_name(self, name: str) -> Optional[Fighter]:
        """קריאת לוחם לפי שם"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM fighters WHERE name LIKE ?', (f'%{name}%',))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_fighter(row)
    
    def get_all_fighters(self) -> List[Fighter]:
        """קריאת כל הלוחמים"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM fighters ORDER BY wins DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_fighter(row) for row in rows]
    
    def get_fighters_by_weight_class(self, weight_class: str) -> List[Fighter]:
        """קריאת לוחמים לפי קטגוריית משקל"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM fighters WHERE weight_class = ?', (weight_class,))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_fighter(row) for row in rows]
    
    # CRUD Operations - UPDATE
    def update_fighter(self, fighter: Fighter) -> bool:
        """
        עדכון נתוני לוחם
        
        Args:
            fighter: אובייקט לוחם מעודכן
            
        Returns:
            bool: האם העדכון הצליח
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            data = fighter.to_dict()
            
            cursor.execute('''
                UPDATE fighters SET
                    name = ?, weight_class = ?, wins = ?, losses = ?, draws = ?,
                    striking_power = ?, grappling_skill = ?,
                    speed = ?, kick_power = ?, knockout_wins = ?,
                    submission_skill = ?, takedown_defense = ?, submission_wins = ?,
                    versatility = ?, title_defenses = ?
                WHERE fighter_id = ?
            ''', (
                data['name'],
                data['weight_class'],
                data['wins'],
                data['losses'],
                data['draws'],
                data['striking_power'],
                data['grappling_skill'],
                data.get('speed'),
                data.get('kick_power'),
                data.get('knockout_wins'),
                data.get('submission_skill'),
                data.get('takedown_defense'),
                data.get('submission_wins'),
                data.get('versatility'),
                data.get('title_defenses'),
                data['fighter_id']
            ))
            
            conn.commit()
            conn.close()
            print(f"✅ {fighter.name} עודכן במסד הנתונים")
            return True
            
        except Exception as e:
            print(f"❌ שגיאה בעדכון לוחם: {e}")
            return False
    
    # CRUD Operations - DELETE
    def delete_fighter(self, fighter_id: int) -> bool:
        """
        מחיקת לוחם
        
        Args:
            fighter_id: מזהה הלוחם
            
        Returns:
            bool: האם המחיקה הצליחה
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM fighters WHERE fighter_id = ?', (fighter_id,))
            
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            
            if deleted:
                print(f"✅ לוחם {fighter_id} נמחק")
            else:
                print(f"❌ לוחם {fighter_id} לא נמצא")
            
            return deleted
            
        except Exception as e:
            print(f"❌ שגיאה במחיקת לוחם: {e}")
            return False
    
    def save_fight_result(self, fight_result: dict) -> bool:
        """שמירת תוצאות קרב"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO fights (
                    fighter1_name, fighter2_name, winner_name, method,
                    fighter1_score, fighter2_score
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                fight_result['fighter1'],
                fight_result['fighter2'],
                fight_result['winner'],
                fight_result['method'],
                fight_result['fighter1_score'],
                fight_result['fighter2_score']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ שגיאה בשמירת קרב: {e}")
            return False
    
    def get_fight_history(self, limit: int = 10) -> List[dict]:
        """קריאת היסטוריית קרבות"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM fights 
            ORDER BY fight_date DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        fights = []
        for row in rows:
            fights.append({
                'fight_id': row[0],
                'fighter1': row[1],
                'fighter2': row[2],
                'winner': row[3],
                'method': row[4],
                'fighter1_score': row[5],
                'fighter2_score': row[6],
                'date': row[7]
            })
        
        return fights
    
    def _row_to_fighter(self, row) -> Fighter:
        """המרת שורה ממסד נתונים לאובייקט לוחם"""
        fighter_type = row[8]  # fighter_type column
        
        data = {
            'fighter_id': row[0],
            'name': row[1],
            'weight_class': row[2],
            'wins': row[3],
            'losses': row[4],
            'draws': row[5],
            'striking_power': row[6],
            'grappling_skill': row[7],
            'speed': row[9],
            'kick_power': row[10],
            'knockout_wins': row[11],
            'submission_skill': row[12],
            'takedown_defense': row[13],
            'submission_wins': row[14],
            'versatility': row[15],
            'title_defenses': row[16]
        }
        
        # יצירת הלוחם המתאים לפי הסוג
        if fighter_type == 'Striker':
            return Striker.from_dict(data)
        elif fighter_type == 'Grappler':
            return Grappler.from_dict(data)
        elif fighter_type == 'HybridChampion':
            return HybridChampion.from_dict(data)
        else:
            return Fighter.from_dict(data)
    
    def get_statistics(self) -> dict:
        """סטטיסטיקות כלליות"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM fighters')
        total_fighters = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM fights')
        total_fights = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_fighters': total_fighters,
            'total_fights': total_fights
        }