
"""
Ollama Client (Enhanced)
אינטגרציה עם AI מקומי - גרסת פיתוח ותשתית עתידית.
"""

import requests
import json
import re
from typing import Optional, Dict, Any


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", mock_mode: bool = True):
        """
        אתחול לקוח Ollama.
        
        Args:
            base_url: כתובת שרת Ollama.
            mock_mode: אם True, יחזיר תשובות קבועות מראש ללא צורך בשרת (מעולה למצגות).
        """
        self._base_url = base_url
        self._model = "llama3" 
        self._mock_mode = mock_mode

    def is_available(self) -> bool:
        if self._mock_mode:
            return True
        try:
            response = requests.get(f"{self._base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, model: str = None) -> Optional[str]:
        if self._mock_mode:
            return "This is a simulated AI response for development purposes."
            
        if not self.is_available():
            return None

        used_model = model or self._model
        try:
            response = requests.post(
                f"{self._base_url}/api/generate",
                json={"model": used_model, "prompt": prompt, "stream": False},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('response', '')
        except Exception as e:
            print(f"❌ Communication Error: {e}")
        return None

    def analyze_fighter_description(self, description: str) -> Dict[str, Any]:
        """
        ניתוח לוחם עם חילוץ JSON חסין שגיאות.
        """
        if self._mock_mode:
            return {
                'fighting_style': 'Hybrid',
                'strengths': ['Versatility', 'Cardio'],
                'skill_level': 8,
                'success': True
            }

        prompt = f"Analyze this UFC fighter: {description}. Return ONLY a JSON with: fighting_style, strengths (list), skill_level (1-10)."
        response = self.generate(prompt)

        if response:
            try:
                # שימוש ב-Regex כדי למצוא את ה-JSON בתוך הטקסט (למקרה שה-AI מוסיף מלל מיותר)
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    data['success'] = True
                    return data
            except Exception:
                return {'raw_analysis': response, 'success': False}
        
        return {'success': False, 'error': 'No response'}

    def generate_fighter_matchup_analysis(self, f1_name: str, f2_name: str, f1_style: str, f2_style: str) -> str:
        if self._mock_mode:
            return f"Matchup Analysis: {f1_name} ({f1_style}) vs {f2_name} ({f2_style}). Key factor: Grappling vs Striking dynamics. Prediction: Close fight."
            
        prompt = f"Analyze UFC matchup: {f1_name} ({f1_style}) vs {f2_name} ({f2_style}). 2-3 sentences max."
        return self.generate(prompt) or "Analysis currently unavailable."

# --- הרצה לבדיקה ---
if __name__ == "__main__":
    # מצב פיתוח (Mock) - לא דורש שרת Ollama פעיל
    client = OllamaClient(mock_mode=True)
    print(f"Status: {'Online' if client.is_available() else 'Offline'}")
    print(client.generate_fighter_matchup_analysis("Khabib", "Conor", "Grappler", "Striker"))