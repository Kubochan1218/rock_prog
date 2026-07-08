import json, datetime, os, re
import customtkinter as ctk
from tkinter import messagebox

import config

class MainView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        
        self.show_dashboard()

    def clear_frame(self):
        """フレーム内のウィジェットをすべて削除"""
        for widget in self.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_frame()
        
        ctk.CTkLabel(self, text='ロック部 出席管理ダッシュボード', font=config.FONT_TITLE).pack(pady=15, anchor="w")

        # 前回起動日が設定されている場合、30日以上経過していれば確認ダイアログを表示
        try:
            prev = self.app.settings.get('last_startup')
            today = datetime.date.today()
            if prev:
                prev_date = datetime.date.fromisoformat(prev)
                delta_days = (today - prev_date).days
                if delta_days >= 30:
                    ctk.CTkLabel(self, text=f'最後のバンド登録から{delta_days}日経過しています。登録済みバンドを確認しましょう！', font=config.FONT_SUBTITLE, text_color='green').pack(pady=10, anchor="w")
        except Exception:
            pass

        # 通常モードのレイアウト（大きなタイルボタンでモダンに変身）
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(pady=10, fill="both", expand=True)
        grid_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(grid_frame, text=f'次のライブ: {self.get_next_live_date()}', font=config.FONT_LABEL_BUTTON).pack(pady=(5, 0), anchor="w")

        btn_attendance = ctk.CTkButton(grid_frame, text='📅 出席をとる・出欠状況確認', height=80, command=self.show_attendance_date_select, fg_color='#bfff80', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_attendance.grid(row=0, column=0, padx=15, pady=15, sticky="ew")

        btn_check = ctk.CTkButton(grid_frame, text='📊 出欠状況の確認\n(出席率計算)', height=80, fg_color='#80d4ff', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_check.grid(row=0, column=1, padx=15, pady=15, sticky="ew")

        btn_register = ctk.CTkButton(grid_frame, text='🎤 バンドの追加・編集・削除', height=80, command=self.register_band, fg_color='#ffff00', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_register.grid(row=1, column=0, padx=15, pady=15, sticky="ew")
        
        btn_select = ctk.CTkButton(grid_frame, text='🔶 出演バンド選出', height=80, command=self.register_band, fg_color='#ffd480', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_select.grid(row=1, column=1, padx=15, pady=15, sticky="ew")

        btn_timetable = ctk.CTkButton(grid_frame, text='⏱️ タイムテーブル作成 (別ウィンドウ)', height=80, command=self.make_timetable, fg_color="#d080ff", text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_timetable.grid(row=2, column=0, columnspan=2, padx=15, pady=15, sticky="ew")
    
    def get_next_live_date(self):
        """次回ライブの日付を取得"""
        try:
            live_info_path = self.app.get_config_path('live_info.json')
            if not os.path.exists(live_info_path):
                return "未登録"
            
            with open(live_info_path, 'r', encoding='utf-8') as f:
                live_data = json.load(f)
            
            # ライブ情報が存在する場合、最も近い日付を取得
            next_live_date = None
            for live in live_data.values():
                for schedule in live.get('schedules', []):
                    date_str = schedule.get('date')
                    if date_str:
                        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                        if next_live_date is None or date_obj < next_live_date:
                            next_live_date = date_obj
            
            return next_live_date.strftime('%Y/%m/%d') if next_live_date else "未登録"
        except Exception:
            return "未登録"