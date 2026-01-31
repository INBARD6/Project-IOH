"""
Ollama Client (Optional)
לקוח לשרת Ollama - אינטגרציה עם AI מקומי
מדגים: אינטגרציה עם LLM, ניתוח טקסט
"""

import requests
import json
from typing import Optional


class OllamaClient:
    """
    לקוח לשרת Ollama מקומי
    מאפשר ניתוח טקסט, Q&A, וסנטימנט
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        אתחול לקוח Ollama
        
        Args:
            base_url: כתובת שרת Ollama
        """
        self._base_url = base_url
        self._model = "llama2"  # ברירת מחדל
    
    def is_available(self) -> bool:
        """
        בדיקה האם שרת Ollama זמין
        
        Returns:
            bool: האם השרת זמין
        """
        try:
            response = requests.get(f"{self._base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def generate(self, prompt: str, model: str = None) -> Optional[str]:
        """
        יצירת תשובה מהמודל
        
        Args:
            prompt: השאלה/בקשה
            model: שם המודל (אופציונלי)
            
        Returns:
            str: התשובה או None במקרה של כשלון
        """
        if not self.is_available():
            print("❌ שרת Ollama לא זמין")
            return None
        
        used_model = model or self._model
        
        try:
            response = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": used_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                print(f"❌ שגיאה: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ שגיאה בתקשורת עם Ollama: {e}")
            return None
    
    def analyze_fighter_description(self, description: str) -> dict:
        """
        ניתוח תיאור של לוחם
        
        Args:
            description: תיאור טקסטואלי של הלוחם
            
        Returns:
            dict: ניתוח הטקסט
        """
        prompt = f"""
        Analyze this UFC fighter description and extract key information:
        
        Description: {description}
        
        Please provide:
        1. Fighting style (Striker/Grappler/Hybrid)
        2. Strengths (list 2-3)
        3. Suggested weight class
        4. Overall skill level (1-10)
        
        Format your response as JSON.
        """
        
        response = self.generate(prompt)
        
        if response:
            try:
                # ניסיון לחלץ JSON מהתשובה
                # זה פשטני - בפרודקשן צריך parsing מתוחכם יותר
                return {
                    'raw_analysis': response,
                    'success': True
                }
            except Exception:
                return {
                    'raw_analysis': response,
                    'success': False
                }
        
        return {'success': False, 'error': 'No response'}
    
    def generate_fighter_matchup_analysis(self, fighter1_name: str, 
                                         fighter2_name: str,
                                         fighter1_style: str,
                                         fighter2_style: str) -> str:
        """
        ניתוח התאמה בין שני לוחמים
        
        Args:
            fighter1_name: שם לוחם 1
            fighter2_name: שם לוחם 2
            fighter1_style: סגנון לוחם 1
            fighter2_style: סגנון לוחם 2
            
        Returns:
            str: ניתוח התאמה
        """
        prompt = f"""
        Analyze this UFC matchup:
        
        Fighter 1: {fighter1_name} (Style: {fighter1_style})
        Fighter 2: {fighter2_name} (Style: {fighter2_style})
        
        Provide a brief analysis (2-3 sentences) of:
        - Style matchup advantages
        - Key factors to watch
        - Prediction
        """
        
        response = self.generate(prompt)
        return response if response else "Analysis not available"
    
    def sentiment_analysis(self, text: str) -> str:
        """
        ניתוח סנטימנט של טקסט
        
        Args:
            text: הטקסט לניתוח
            
        Returns:
            str: חיובי/שלילי/נייטרלי
        """
        prompt = f"""
        Analyze the sentiment of this text about a UFC fight or fighter.
        Respond with only one word: Positive, Negative, or Neutral.
        
        Text: {text}
        """
        
        response = self.generate(prompt)
        
        if response:
            response_lower = response.lower().strip()
            if 'positive' in response_lower:
                return 'Positive'
            elif 'negative' in response_lower:
                return 'Negative'
            else:
                return 'Neutral'
        
        return 'Unknown'
    
    def get_available_models(self) -> list:
        """
        קבלת רשימת מודלים זמינים
        
        Returns:
            list: רשימת שמות מודלים
        """
        try:
            response = requests.get(f"{self._base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            print(f"❌ שגיאה בקבלת מודלים: {e}")
        
        return []
    
    def set_model(self, model: str):
        """
        הגדרת מודל ברירת מחדל
        
        Args:
            model: שם המודל
        """
        self._model = model
        print(f"✅ מודל הוגדר ל-{model}")


# דוגמה לשימוש
if __name__ == "__main__":
    client = OllamaClient()
    
    if client.is_available():
        print("✅ שרת Ollama זמין!")
        
        # בדיקת מודלים זמינים
        models = client.get_available_models()
        print(f"מודלים זמינים: {models}")
        
        # דוגמה לשימוש
        analysis = client.generate_fighter_matchup_analysis(
            "Conor McGregor", "Khabib Nurmagomedov",
            "Striker", "Grappler"
        )
        print(f"\nניתוח התאמה:\n{analysis}")
    else:
        print("❌ שרת Ollama לא זמין")
        print("להתקנה: docker pull ollama/ollama")