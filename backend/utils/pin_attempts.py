import os
import json
import time
from typing import Dict

class PinAttemptManager:
    def __init__(self, max_attempts=10, attempt_window=300, block_duration=7200):  # 10 попыток за 5 минут (300 секунд), блокировка на 2 часа (7200 секунд)
        self.max_attempts = max_attempts
        self.attempt_window = attempt_window
        self.block_duration = block_duration
        self.attempts_file = os.path.join(os.path.dirname(__file__), 'pin_attempts.json')
        self._load_attempts()

    def _load_attempts(self):
        if not os.path.exists(self.attempts_file):
            self.attempts = {}
            self._save_attempts()
        else:
            with open(self.attempts_file, 'r') as f:
                self.attempts = json.load(f)

    def _save_attempts(self):
        with open(self.attempts_file, 'w') as f:
            json.dump(self.attempts, f)

    def check_attempts(self, dirname: str) -> Dict[str, bool]:
        current_time = time.time()
        
        if dirname not in self.attempts:
            return {"allowed": True}

        attempt_data = self.attempts[dirname]
        # Проверка блокировки
        if attempt_data.get('block_until', 0) > current_time:
            return {
                "allowed": False, 
                "message": "Доступ к управлению файлами временно ограничен, повторите попытку через 2 часа",
                "block_remaining": int(attempt_data['block_until'] - current_time)
            }
        
        # Очистка старых попыток в окне 5 минут
        attempt_data['attempts'] = [
            t for t in attempt_data['attempts'] 
            if current_time - t <= self.attempt_window
        ]
        
        return {"allowed": len(attempt_data['attempts']) < self.max_attempts}

    def increment_attempts(self, dirname: str):
        current_time = time.time()
        
        if dirname not in self.attempts:
            self.attempts[dirname] = {
                "attempts": [current_time],
                "block_until": 0
            }
        else:
            attempt_data = self.attempts[dirname]
            
            # Очистка старых попыток
            attempt_data['attempts'] = [
                t for t in attempt_data['attempts'] 
                if current_time - t <= self.attempt_window
            ]
            
            attempt_data['attempts'].append(current_time)
            
            # Проверка на превышение лимита попыток
            if len(attempt_data['attempts']) >= self.max_attempts:
                attempt_data['block_until'] = current_time + self.block_duration
        
        self._save_attempts()

    def reset_attempts(self, dirname: str):
        if dirname in self.attempts:
            # Если была блокировка, она остается
            if self.attempts[dirname].get('block_until', 0) > time.time():
                return
            
            # Иначе даём доступ, чистим попытки
            self.attempts[dirname]['attempts'] = []
        
        self._save_attempts()

pin_attempt_manager = PinAttemptManager()