# time_handler.py
# Sistema de gerenciamento de tempo e datas

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union

# Configuração do logger
logger = logging.getLogger(__name__)

class TimeHandler:
    def __init__(self, config):
        self.config = config
        
        # Caminho para o arquivo de datas especiais
        self.special_dates_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'special_dates.json'
        )
        
        # Dicionário para armazenar datas especiais
        self.special_dates = {}
        
        # Carrega datas especiais se o arquivo existir
        self.load_special_dates()
        
        # Configurações de localização e fuso horário
        self.timezone_offset = self.config.get_config_value('timezone_offset', 0)
        self.locale = self.config.get_config_value('locale', 'pt_BR')
        
        # Nomes dos dias da semana e meses em português
        self.weekdays_pt = [
            "segunda-feira", "terça-feira", "quarta-feira", 
            "quinta-feira", "sexta-feira", "sábado", "domingo"
        ]
        
        self.months_pt = [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
        ]
        
        # Lista de feriados nacionais brasileiros (formato: dia, mês)
        self.holidays_br = [
            (1, 1),    # Ano Novo
            (21, 4),   # Tiradentes
            (1, 5),    # Dia do Trabalho
            (7, 9),    # Independência
            (12, 10),  # Nossa Senhora Aparecida
            (2, 11),   # Finados
            (15, 11),  # Proclamação da República
            (25, 12),  # Natal
        ]
        
    def get_current_time(self) -> datetime:
        """Retorna o datetime atual considerando o timezone configurado"""
        now = datetime.now()
        if self.timezone_offset != 0:
            now = now + timedelta(hours=self.timezone_offset)
        return now
    
    def get_formatted_time(self, format_str: str = "%H:%M:%S") -> str:
        """Retorna a hora atual formatada"""
        return self.get_current_time().strftime(format_str)
    
    def get_formatted_date(self, format_str: str = "%d/%m/%Y") -> str:
        """Retorna a data atual formatada"""
        return self.get_current_time().strftime(format_str)
    
    def get_weekday(self, as_number: bool = False) -> Union[str, int]:
        """Retorna o dia da semana atual
        
        Args:
            as_number: Se True, retorna o número do dia (0 = Segunda, 6 = Domingo)
                      Se False, retorna o nome do dia em português
        """
        now = self.get_current_time()
        weekday = now.weekday()
        
        if as_number:
            return weekday
        else:
            return self.weekdays_pt[weekday]
    
    def get_month(self, as_number: bool = False) -> Union[str, int]:
        """Retorna o mês atual
        
        Args:
            as_number: Se True, retorna o número do mês (1-12)
                      Se False, retorna o nome do mês em português
        """
        now = self.get_current_time()
        month = now.month
        
        if as_number:
            return month
        else:
            return self.months_pt[month - 1]
    
    def get_time_of_day(self) -> str:
        """Retorna o período do dia (manhã, tarde, noite, madrugada)"""
        hour = self.get_current_time().hour
        
        if 5 <= hour < 12:
            return "manhã"
        elif 12 <= hour < 18:
            return "tarde"
        elif 18 <= hour < 22:
            return "noite"
        else:
            return "madrugada"
    
    def is_weekend(self) -> bool:
        """Verifica se é fim de semana"""
        weekday = self.get_weekday(as_number=True)
        return weekday >= 5  # 5 = Sábado, 6 = Domingo
    
    def is_business_hour(self) -> bool:
        """Verifica se é horário comercial (seg-sex, 8h-18h)"""
        now = self.get_current_time()
        weekday = now.weekday()
        hour = now.hour
        
        return weekday < 5 and 8 <= hour < 18
    
    def is_holiday(self) -> bool:
        """Verifica se hoje é um feriado nacional brasileiro"""
        now = self.get_current_time()
        day = now.day
        month = now.month
        
        return (day, month) in self.holidays_br
    
    def get_time_context(self) -> Dict[str, str]:
        """Retorna um dicionário com informações de tempo para contexto"""
        now = self.get_current_time()
        
        context = {
            "current_time": self.get_formatted_time(),
            "current_date": self.get_formatted_date(),
            "weekday": self.get_weekday(),
            "month": self.get_month(),
            "time_of_day": self.get_time_of_day(),
            "is_weekend": str(self.is_weekend()),
            "is_business_hour": str(self.is_business_hour()),
            "is_holiday": str(self.is_holiday()),
            "year": str(now.year),
            "day": str(now.day)
        }
        
        # Adiciona informações sobre datas especiais próximas
        upcoming = self.get_upcoming_special_dates(limit=2)
        if upcoming:
            context["upcoming_dates"] = ", ".join(
                [f"{name} em {days} dias" for name, days in upcoming]
            )
        
        return context
    
    def format_time_context_for_ai(self) -> str:
        """Formata o contexto de tempo para ser usado pelo modelo de IA"""
        context = self.get_time_context()
        
        # Cria uma mensagem formatada com as informações de tempo
        message = [
            f"Data atual: {context['current_date']}",
            f"Hora atual: {context['current_time']}",
            f"Dia da semana: {context['weekday']}",
            f"Período do dia: {context['time_of_day']}"
        ]
        
        # Adiciona informações condicionais
        if context['is_weekend'] == 'True':
            message.append("Hoje é fim de semana.")
        
        if context['is_holiday'] == 'True':
            message.append("Hoje é feriado nacional.")
            
        if 'upcoming_dates' in context:
            message.append(f"Datas especiais próximas: {context['upcoming_dates']}")
        
        return "\n".join(message)
    
    def add_special_date(self, name: str, date_str: str, recurring: bool = True) -> bool:
        """Adiciona uma data especial ao calendário
        
        Args:
            name: Nome da data especial (ex: "Aniversário do João")
            date_str: Data no formato DD/MM/YYYY ou DD/MM
            recurring: Se True, a data se repete anualmente
        """
        try:
            # Verifica o formato da data
            if len(date_str.split('/')) == 2:
                day, month = map(int, date_str.split('/'))
                year = None  # Data recorrente anual
            else:
                day, month, year = map(int, date_str.split('/'))
            
            # Valida a data
            if not (1 <= day <= 31 and 1 <= month <= 12):
                logger.error(f"Data inválida: {date_str}")
                return False
            
            # Cria um ID único para a data
            import hashlib
            date_id = f"date_{hashlib.md5(f'{name}_{date_str}'.encode('utf-8')).hexdigest()[:8]}"
            
            # Armazena a data especial
            self.special_dates[date_id] = {
                "name": name,
                "day": day,
                "month": month,
                "year": year,
                "recurring": recurring
            }
            
            # Salva as datas especiais
            self.save_special_dates()
            
            logger.info(f"Data especial adicionada: {name} - {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar data especial: {e}")
            return False
    
    def remove_special_date(self, name: str) -> bool:
        """Remove uma data especial pelo nome"""
        try:
            # Procura a data pelo nome
            date_id = None
            for id, date_info in self.special_dates.items():
                if date_info["name"].lower() == name.lower():
                    date_id = id
                    break
            
            if date_id:
                # Remove a data
                del self.special_dates[date_id]
                
                # Salva as alterações
                self.save_special_dates()
                
                logger.info(f"Data especial removida: {name}")
                return True
            else:
                logger.warning(f"Data especial não encontrada: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover data especial: {e}")
            return False
    
    def get_upcoming_special_dates(self, limit: int = 5) -> List[Tuple[str, int]]:
        """Retorna as próximas datas especiais
        
        Args:
            limit: Número máximo de datas a retornar
            
        Returns:
            Lista de tuplas (nome_da_data, dias_restantes)
        """
        try:
            now = self.get_current_time()
            current_year = now.year
            current_month = now.month
            current_day = now.day
            
            upcoming_dates = []
            
            for date_id, date_info in self.special_dates.items():
                day = date_info["day"]
                month = date_info["month"]
                year = date_info["year"]
                name = date_info["name"]
                recurring = date_info["recurring"]
                
                # Se a data não é recorrente e já passou, pula
                if not recurring and year and datetime(year, month, day) < now:
                    continue
                
                # Calcula a próxima ocorrência da data
                if month < current_month or (month == current_month and day < current_day):
                    # A data já passou este ano, considera para o próximo ano
                    target_year = current_year + 1
                else:
                    # A data ainda não ocorreu este ano
                    target_year = current_year
                
                # Cria a data alvo
                target_date = datetime(target_year, month, day)
                
                # Calcula a diferença em dias
                days_remaining = (target_date - now).days
                
                # Adiciona à lista de datas próximas
                upcoming_dates.append((name, days_remaining))
            
            # Ordena por proximidade e limita o número de resultados
            upcoming_dates.sort(key=lambda x: x[1])
            return upcoming_dates[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao obter datas especiais próximas: {e}")
            return []
    
    def detect_date_triggers(self, message: str, memory) -> bool:
        """Detecta gatilhos para armazenar datas especiais
        
        Args:
            message: Mensagem do usuário
            memory: Objeto de memória para armazenar informações
            
        Returns:
            True se uma data foi detectada e armazenada, False caso contrário
        """
        # Lista de gatilhos que indicam que o usuário quer registrar uma data
        date_triggers = [
            "lembre-se da data", "anote a data", "marque no calendário", 
            "guarde essa data", "salve essa data", "lembre do dia",
            "aniversário", "evento", "compromisso", "reunião", "encontro"
        ]
        
        # Verifica se a mensagem contém algum dos gatilhos
        message_lower = message.lower()
        triggered = False
        
        for trigger in date_triggers:
            if trigger in message_lower:
                triggered = True
                break
                
        if not triggered:
            return False
        
        # Tenta extrair uma data da mensagem
        import re
        
        # Padrões de data (DD/MM/YYYY ou DD/MM)
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})/(\d{1,2})'            # DD/MM
        ]
        
        # Tenta encontrar uma data na mensagem
        date_match = None
        date_str = None
        
        for pattern in date_patterns:
            matches = re.findall(pattern, message)
            if matches:
                date_match = matches[0]
                if isinstance(date_match, tuple):
                    # Formata a data encontrada
                    if len(date_match) == 2:  # DD/MM
                        date_str = f"{date_match[0]}/{date_match[1]}"
                    else:  # DD/MM/YYYY
                        date_str = f"{date_match[0]}/{date_match[1]}/{date_match[2]}"
                else:
                    date_str = date_match
                break
        
        if not date_str:
            # Se não encontrou uma data no formato padrão, tenta extrair usando processamento de linguagem natural
            # Isso seria melhor implementado com uma biblioteca NLP, mas aqui usamos uma abordagem simplificada
            month_patterns = [
                r'(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)',
                r'(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)'
            ]
            
            day_pattern = r'\b(\d{1,2})\s+(?:de\s+)?'
            year_pattern = r'(?:\s+de\s+)?(\d{4})'
            
            # Tenta encontrar padrões como "10 de janeiro de 2023" ou "10 jan 2023"
            for month_pattern in month_patterns:
                full_pattern = day_pattern + month_pattern + year_pattern
                matches = re.findall(full_pattern, message_lower)
                if matches:
                    day, month_name, year = matches[0]
                    
                    # Converte o nome do mês para número
                    month_num = 0
                    for i, month in enumerate(self.months_pt):
                        if month_name.lower() in month.lower() or month_name.lower() == month[:3].lower():
                            month_num = i + 1
                            break
                    
                    if month_num > 0:
                        date_str = f"{day}/{month_num}/{year}"
                        break
        
        # Se encontrou uma data, tenta extrair o nome do evento
        if date_str:
            # Procura por palavras-chave que indicam o tipo de evento
            event_keywords = [
                "aniversário", "niver", "nascimento", "festa", "comemoração",
                "evento", "reunião", "encontro", "compromisso", "consulta",
                "entrega", "prazo", "deadline", "vencimento", "pagamento"
            ]
            
            # Tenta encontrar o nome do evento na mensagem
            event_name = None
            
            # Procura por frases como "aniversário do João" ou "reunião com o cliente"
            for keyword in event_keywords:
                if keyword in message_lower:
                    # Pega o texto após a palavra-chave
                    keyword_index = message_lower.find(keyword)
                    after_keyword = message[keyword_index + len(keyword):].strip()
                    
                    # Remove palavras como "do", "da", "de" no início
                    after_keyword = after_keyword.lstrip("do da de dos das com ").strip()
                    
                    # Se houver texto após a palavra-chave, usa como nome do evento
                    if after_keyword and len(after_keyword) < 50:  # Limita o tamanho
                        event_name = f"{keyword} {after_keyword}"
                        break
            
            # Se não encontrou um nome específico, usa um nome genérico
            if not event_name:
                # Tenta identificar o tipo de evento
                for keyword in event_keywords:
                    if keyword in message_lower:
                        event_name = keyword.capitalize()
                        break
                        
                # Se ainda não tem nome, usa um nome genérico
                if not event_name:
                    event_name = "Evento"
            
            # Adiciona a data especial
            self.add_special_date(event_name, date_str)
            
            # Armazena a informação na memória de longo prazo
            info_to_store = f"{event_name} na data {date_str}"
            import hashlib
            key = f"date_event_{hashlib.md5(info_to_store.encode('utf-8')).hexdigest()[:8]}"
            memory.store_permanent_info(key, info_to_store)
            
            logger.info(f"Data especial detectada e armazenada: {event_name} - {date_str}")
            return True
            
        return False
    
    def load_special_dates(self):
        """Carrega datas especiais do arquivo JSON"""
        try:
            if os.path.exists(self.special_dates_file):
                with open(self.special_dates_file, 'r', encoding='utf-8') as f:
                    self.special_dates = json.load(f)
                logger.info(f"Datas especiais carregadas: {len(self.special_dates)} eventos")
                return True
            else:
                logger.info("Arquivo de datas especiais não encontrado. Iniciando com lista vazia.")
                return False
        except Exception as e:
            logger.error(f"Erro ao carregar datas especiais: {e}")
            return False
    
    def save_special_dates(self):
        """Salva datas especiais em um arquivo JSON"""
        try:
            # Cria o diretório se não existir
            os.makedirs(os.path.dirname(self.special_dates_file), exist_ok=True)
            
            with open(self.special_dates_file, 'w', encoding='utf-8') as f:
                json.dump(self.special_dates, f, indent=4)
            
            logger.info(f"Datas especiais salvas: {len(self.special_dates)} eventos")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar datas especiais: {e}")
            return False
