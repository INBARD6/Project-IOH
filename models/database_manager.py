import sqlite3

class DatabaseManager:
    def __init__(self, db_name="ufc_game.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """יוצר את הטבלה אם היא לא קיימת"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fighters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hp INTEGER,
                attack_power INTEGER,
                stamina INTEGER,
                wins INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def save_fighter(self, fighter):
        """שומר אובייקט של לוחם למסד הנתונים"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # שימו לב: אנחנו שולפים את הנתונים מהאובייקט (Fighter) ושומרים ב-SQL
        cursor.execute('''
            INSERT INTO fighters (name, hp, attack_power, stamina)
            VALUES (?, ?, ?, ?)
        ''', (fighter.name, fighter.hp, 50, 100)) # כרגע שמתי ערכים לדוגמה
        conn.commit()
        conn.close()

    def get_all_fighters(self):
        """שולף את כל הלוחמים ומחזיר רשימה של תוצאות"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fighters")
        rows = cursor.fetchall()
        conn.close()
        return rows