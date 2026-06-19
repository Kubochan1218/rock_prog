from datetime import datetime
from typing import List, Optional

class Member:
    def __init__(self, name: str, student_id: Optional[str] = None):
        self.name = name
        self.student_id = student_id

class Band:
    def __init__(self, name: str, members: List[Member], performance_minutes: int, available_dates: List[str]):
        self.name = name
        self.members = members
        self.performance_minutes = performance_minutes
        self.available_dates = available_dates  # 例: ['2025/10/12', ...]

class AttendanceRate:
    def __init__(self, member: Member, period: str, rate: float):
        self.member = member
        self.period = period
        self.rate = rate

class LiveSchedule:
    def __init__(self, date, start_time, end_time):
        self.date = date              # datetime.date
        self.start_time = start_time  # "HH:MM" 形式の文字列
        self.end_time = end_time      # "HH:MM" 形式の文字列

class BandInfo:
    def __init__(self, name, performance_minutes, available_dates):
        self.name = name
        self.performance_minutes = performance_minutes
        self.available_dates = available_dates  # List[date]
