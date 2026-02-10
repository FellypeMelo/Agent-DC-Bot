# time_handler.py
import logging
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union, Optional

logger = logging.getLogger(__name__)

class TimeHandler:
    def __init__(self, config):
        """
        Initializes the Time Handler with locale-specific names and pre-defined holidays.
        
        Big (O): O(1) - Constant time setup.
        """
        self.config = config
        
        self.weekdays_pt = [
            "segunda-feira", "terça-feira", "quarta-feira", 
            "quinta-feira", "sexta-feira", "sábado", "domingo"
        ]
        
        self.months_pt = [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
        ]
        
        # O(1) Lookup for holidays using a set of tuples (day, month)
        self.HOLIDAYS_BR = {
            (1, 1), (21, 4), (1, 5), (7, 9), (12, 10), (2, 11), (15, 11), (25, 12)
        }
        
    def get_current_time(self) -> datetime:
        """Returns current time adjusted by configured offset. Big(O): O(1)."""
        return datetime.now()

    def get_time_of_day(self, hour: int) -> str:
        """Categorizes hour into period of day. Big(O): O(1)."""
        if 5 <= hour < 12: return "manhã"
        if 12 <= hour < 18: return "tarde"
        if 18 <= hour < 22: return "noite"
        return "madrugada"

    def get_time_context(self) -> Dict[str, Any]:
        """
        Generates a comprehensive dictionary of the current temporal context for the LLM.
        
        Returns:
            Context dictionary.
            
        Big (O): O(1) - All operations are fixed-time date manipulations.
        """
        now = self.get_current_time()
        day, month, year = now.day, now.month, now.year
        weekday_idx = now.weekday()

        return {
            "current_time": now.strftime("%H:%M"),
            "current_date": now.strftime("%d/%m/%Y"),
            "weekday": self.weekdays_pt[weekday_idx],
            "month": self.months_pt[month - 1],
            "time_of_day": self.get_time_of_day(now.hour),
            "is_weekend": weekday_idx >= 5,
            "is_holiday": (day, month) in self.HOLIDAYS_BR,
            "year": str(year)
        }
    
    def format_time_context_for_ai(self) -> str:
        """
        Formats time context into a natural language block for the System Prompt.
        
        Big (O): O(1) - Fixed string formatting.
        """
        ctx = self.get_time_context()
        
        lines = [
            f"Hoje é {ctx['weekday']}, {ctx['current_date']}.",
            f"Hora atual: {ctx['current_time']} ({ctx['time_of_day']})."
        ]
        
        if ctx['is_weekend']: lines.append("É fim de semana.")
        if ctx['is_holiday']: lines.append("Hoje é um feriado nacional no Brasil.")
        
        return "\n".join(lines)

    def detect_date_triggers(self, message: str) -> Optional[Dict[str, int]]:
        """
        Detects date patterns in text using optimized regular expressions.
        
        Args:
            message: User message.
            
        Returns:
            Dict with day, month, year if found.
            
        Big (O): O(L) - L is the message length. Single pass regex match.
        """
        # Optimized regex for DD/MM/YYYY or DD/MM
        match = re.search(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', message)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            
            if not (1 <= day <= 31 and 1 <= month <= 12):
                return None
                
            year = match.group(3)
            if year:
                year = int(year)
                if year < 100: year += 2000 # Handle YY
                
            return {"day": day, "month": month, "year": year}
        
        return None