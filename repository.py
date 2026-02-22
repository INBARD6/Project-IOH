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
    
    def __init__(self, db_name: str = "ufc_v3.db"):
        """
        אתחול מסד נתונים
        
        Args:
            db_name: שם קובץ מסד הנתונים
        """
        self._db_name = db_name
        self._create_tables()
    
    def _get_connection(self):
        """יצירת חיבור למסד נתונים עם תמיכה בשמות עמודות"""
        conn = sqlite3.connect(self._db_name)
        # השורה הזו היא הקסם - היא מאפשרת לנו לגשת לנתונים לפי שם העמודה
        conn.row_factory = sqlite3.Row
        return conn
    
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
                skin_color TEXT,
                hair_color TEXT,
                pants_color TEXT,
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
        print(f"✅ Database '{self._db_name}' Successfully Initialized")
    
    # CRUD Operations - CREATE
    def add_fighter(self, f: Fighter) -> bool:
        """הוספת לוחם למסד נתונים כולל צבעי מראה"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # אנחנו מוסיפים את עמודות הצבעים לפקודת ה-INSERT
            cursor.execute('''
                INSERT OR IGNORE INTO fighters (
                    fighter_id, name, weight_class, wins, losses, draws, 
                    striking_power, grappling_skill, 
                    skin_color, hair_color, pants_color, 
                    fighter_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f.fighter_id, f.name, f.weight_class, f.wins, f.losses, f.draws,
                f.striking_power, f.grappling_skill,
                # הופכים את ה-Tuple (R,G,B) למחרוזת טקסט פשוטה "R,G,B"
                ",".join(map(str, getattr(f, 'skin_color', (255,220,180)))),
                ",".join(map(str, getattr(f, 'hair_color', (40,40,40)))),
                ",".join(map(str, getattr(f, 'pants_color', (30,30,30)))),
                f.__class__.__name__
            ))
            
            conn.commit()
            conn.close()
            print(f"✅ {f.name} added with custom style")
            return True
            
        except Exception as e:
            print(f"❌ Error adding fighter: {e}")
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
            print(f"✅ {fighter.name} Updated Successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error updating fighter: {e}")
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
                print(f"✅ Fighter {fighter_id} Deleted Successfully")
            else:
                print(f"❌ Fighter {fighter_id} Not Found")
            
            return deleted
            
        except Exception as e:
            print(f"❌ Error deleting fighter: {e}")
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
            print(f"❌ Error saving fight result: {e}")
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
    
    def _row_to_fighter(self, row: sqlite3.Row) -> Fighter:
        """הופכת שורה מהדאטה-בייס לאובייקט לוחם עם צבעים"""
        # שליפת סוג הלוחם
        f_type = row['fighter_type']
        
        # יצירת הלוחם עם נתוני הבסיס
        args = (row['fighter_id'], row['name'], row['weight_class'], 
                row['wins'], row['losses'], row['draws'], 
                row['striking_power'], row['grappling_skill'])
        
        if f_type == 'Striker':
            f = Striker(*args)
        elif f_type == 'Grappler':
            f = Grappler(*args)
        elif f_type == 'HybridChampion':
            f = HybridChampion(*args)
        else:
            f = Fighter(*args)

        # פונקציית עזר להפוך טקסט "255,0,0" חזרה לטבלה של מספרים
        def parse_color(color_str, default):
            if not color_str: return default
            try:
                return tuple(map(int, color_str.split(',')))
            except:
                return default

        # הוספת הצבעים לאובייקט הלוחם
        f.skin_color = parse_color(row['skin_color'], (255, 220, 180))
        f.hair_color = parse_color(row['hair_color'], (40, 40, 40))
        f.pants_color = parse_color(row['pants_color'], (30, 30, 30))
        
        return f
    
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