from datetime import datetime
from typing import List, Optional

class Member:
    def __init__(self, name: str, student_id: Optional[str] = None):
        self.name = name
        self.student_id = student_id

class Band:
    def __init__(self, name: str, members: List[Member], performance_minutes: int, available_dates: List[str], available_live: str):
        self.name = name
        self.members = members
        self.performance_minutes = performance_minutes
        self.available_dates = available_dates  # 例: ['2025/10/12', ...]
        self.available_live = available_live  # 例: 202601 (※idで表記)

class AttendanceRate:
    def __init__(self, member: Member, period: str, rate: float):
        self.member = member
        self.period = period
        self.rate = rate

class LiveSchedule:
    def __init__(self, live_id, live_name, date, start_time, end_time):
        self.live_id = live_id  # ライブの一意な識別子(id)
        self.live_name = live_name  # ライブの一意な識別子(ライブ名)
        self.date = date              # datetime.date
        self.start_time = start_time  # "HH:MM" 形式の文字列
        self.end_time = end_time      # "HH:MM" 形式の文字列

class BandInfo:
    def __init__(self, name, performance_minutes, available_dates, available_live):
        self.name = name
        self.performance_minutes = performance_minutes
        self.available_dates = available_dates  # List[date]
        self.available_live = available_live  # List[LiveSchedule]
        
