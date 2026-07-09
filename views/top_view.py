import json, datetime, os, openpyxl, pandas, re
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
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(pady=0, fill='both', expand=True, padx=0)
        main_frame.grid_columnconfigure(0, weight=1, uniform="col1")
        main_frame.grid_columnconfigure(1, weight=1, uniform="col1")
        main_frame.grid_rowconfigure(0, weight=1)
        # memo:17:3
        nest_live_frame = ctk.CTkFrame(main_frame)
        nest_live_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        live_mgmt_frame = ctk.CTkFrame(main_frame)
        live_mgmt_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        next_live = self.get_next_live()
        ctk.CTkLabel(nest_live_frame, text=f'次のライブ', font=config.FONT_TITLE).pack(padx=10, pady=5)
        if next_live:
            # ライブ情報を表示
            ctk.CTkLabel(
                nest_live_frame, justify="left", anchor="w",
                text=f'ライブ名: {next_live["name"]}\n日程: {next_live["closest_date"].strftime("%Y-%m-%d")}～\n開始まで: {next_live["days_diff"]}日',
                font=(config.FONT_NAME, 18)).pack(padx=10, pady=5, anchor="w")
            
            # 追加済み／未追加バンド表示枠
            bands_frame = ctk.CTkFrame(nest_live_frame, fg_color="transparent")
            bands_frame.pack(padx=0, pady=0, fill="both", expand=True)
            bands_frame.grid_rowconfigure(0, weight=1, uniform="row1")
            bands_frame.grid_rowconfigure(1, weight=1, uniform="row1")
            bands_frame.grid_columnconfigure(0, weight=1)
            
            # タイムテーブル追加済みバンド情報を表示
            added_bands_frame = ctk.CTkFrame(bands_frame, fg_color="#a3caa3")
            added_bands_frame.grid(row=0, column=0, padx=5, pady=(0, 5), sticky="nsew")
            ctk.CTkLabel(added_bands_frame, text='✔ タイムテーブル追加済みバンド', font=(config.FONT_NAME, 18, 'bold'), text_color='black').pack(pady=(5, 0))
            
            bands = self.get_live_bands(next_live["name"])[:3]  # 上位3件まで表示
            num_bands = len(self.get_live_bands(next_live["name"])) # バンド総数を取得
            
            if bands:
                for band in bands:
                    ctk.CTkLabel(added_bands_frame, text=f'🎵 {band}', font=(config.FONT_NAME, 16), text_color='black').pack(padx=10, anchor="w")
                ctk.CTkLabel(added_bands_frame, text=f'全 {num_bands} バンド', font=(config.FONT_NAME, 16), text_color='gray20').pack(padx=10, anchor="w")
            else:
                ctk.CTkLabel(added_bands_frame, text='タイムテーブル追加済みバンド情報なし', font=(config.FONT_NAME, 16), text_color='black').pack(padx=10, anchor="w")
            
            # タイムテーブル未追加バンド情報を表示
            unadded_bands_frame = ctk.CTkFrame(bands_frame, fg_color="#f5dfc6")
            unadded_bands_frame.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="nsew")
            ctk.CTkLabel(unadded_bands_frame, text='⚠ タイムテーブル未追加バンド', font=(config.FONT_NAME, 18, 'bold'), text_color='black').pack(pady=(5, 0))
            
            all_bands = self.get_selected_bands(next_live["name"])
            unadded_bands = [b['band_name'] for b in all_bands if b['band_name'] not in self.get_live_bands(next_live["name"])]
            if unadded_bands:
                for band in unadded_bands[:3]:  # 上位3件まで表示
                    ctk.CTkLabel(unadded_bands_frame, text=f'🎵 {band}', font=(config.FONT_NAME, 16), text_color='black').pack(padx=10, anchor="w")
                ctk.CTkLabel(unadded_bands_frame, text=f'全 {len(unadded_bands)} バンド', font=(config.FONT_NAME, 16), text_color='gray20').pack(padx=10, anchor="w")
            elif not unadded_bands and not self.get_live_bands(next_live["name"]):
                ctk.CTkLabel(unadded_bands_frame, text='バンド選出が完了していません', font=(config.FONT_NAME, 16), text_color='black').pack(padx=10, anchor="w")
            else:
                ctk.CTkLabel(unadded_bands_frame, text='タイムテーブル未追加バンド情報なし', font=(config.FONT_NAME, 16), text_color='black').pack(padx=10, anchor="w")
            
            # ライブ管理ボタン表示枠
            button_frame = ctk.CTkFrame(nest_live_frame, fg_color="transparent")
            button_frame.pack(padx=0, pady=0, side="bottom", expand=True)
            ctk.CTkButton(
                button_frame,
                text='ライブ情報編集', 
                font=config.FONT_LABEL_BUTTON,
                fg_color='transparent',
                text_color="#65e1f1",
                command=lambda: self.app.register_live(default_live_name=next_live["name"])
                ).pack(pady=10, padx=5, side="left")
            ctk.CTkButton(
                button_frame,
                text='バンド登録・編集',
                font=config.FONT_LABEL_BUTTON,
                fg_color='transparent',
                text_color='#65e1f1',
                command=lambda: self.app.register_band(default_tab="📝 登録済みバンドの管理", default_live_name=next_live["name"])
                ).pack(pady=10, padx=5, side="left")
            ctk.CTkButton(
                button_frame,
                text='タイムテーブル作成',
                font=config.FONT_LABEL_BUTTON,
                fg_color='transparent',
                text_color='#65e1f1',
                command=lambda: self.app.make_timetable(default_live_name=next_live["name"])
                ).pack(pady=10, padx=5, side="left")
        else:
            ctk.CTkLabel(nest_live_frame, text='情報なし', font=(config.FONT_NAME, 18)).pack(padx=10, pady=5, anchor="center")
            ctk.CTkButton(
                nest_live_frame,
                text='ライブ情報を登録する',
                font=config.FONT_LABEL_BUTTON,
                fg_color='transparent',
                text_color='#4a90e2',
                command=lambda: self.app.register_live()
                ).pack(pady=10, padx=10, fill="x")



    def get_next_live(self):
        """日付が最も近いライブを取得"""
        LIVE_JSON_PATH = self.app.get_config_path('live_info.json')
        if not os.path.exists(LIVE_JSON_PATH):
            return None
        try:
            with open(LIVE_JSON_PATH, 'r', encoding='utf-8') as f:
                existing_lives = json.load(f)
        except Exception:
            return None

        if not existing_lives:
            return None

        today = datetime.date.today()
        future_lives = []
        past_lives = []

        for live_name, live_data in existing_lives.items():
            schedules = live_data.get('schedules', [])
            if not schedules:
                continue
            
            # ライブに含まれる全日程の日付を datetime.date 型に変換してリスト化
            live_dates = []
            for s in schedules:
                d_str = s.get('date')
                if d_str:
                    # YYYY-MM-DD または YYYY/MM/DD の両方の形式に対応
                    for fmt in ('%Y-%m-%d', '%Y/%m/%d'):
                        try:
                            d_obj = datetime.datetime.strptime(d_str, fmt).date()
                            live_dates.append(d_obj)
                            break
                        except ValueError:
                            continue
            
            if not live_dates:
                continue
            
            # 今日以降（未来・当日）の日程があるか判定
            upcoming_dates = [d for d in live_dates if d >= today]
            if upcoming_dates:
                # 未来の日程の中で、最も今日に近い日（ライブ初日など）
                min_future_date = min(upcoming_dates)
                future_lives.append({
                    'name': live_name,
                    'data': live_data,
                    'closest_date': min_future_date,
                    'days_diff': (min_future_date - today).days,
                    'is_upcoming': True
                })

        # 未来のライブがあれば、今日に一番近いものを最優先で返す
        if future_lives:
            next_live = min(future_lives, key=lambda x: x['days_diff'])
            return next_live
        
        return None
    
    def get_live_bands(self, live_name):
        """指定されたライブのタイムテーブルに追加済みのバンドを取得"""
        LIVE_JSON_PATH = self.app.get_config_path('live_info.json')
        if not os.path.exists(LIVE_JSON_PATH):
            return []
        try:
            with open(LIVE_JSON_PATH, 'r', encoding='utf-8') as f:
                existing_lives = json.load(f)
        except Exception:
            return []

        live_data = existing_lives.get(live_name, {}).get("schedules", [])
        if not live_data:
            return []
        added_bands = []
        for live in live_data:
            bands = live.get('bands', [])
            added_bands.extend(bands)
        return added_bands

    def get_selected_bands(self, live_name):
        """指定されたライブに出演確定のバンドを取得"""
        try:
            wb = openpyxl.load_workbook(config.FILE_PATH, data_only=True)
            ws = wb['登録済みバンド']
            bands = []
            for row in range(1, ws.max_row + 1):
                r_val = ws.cell(row=row, column=18).value
                if r_val == 1 and ws.cell(row=row, column=19).value == live_name:
                    band_name = ws.cell(row=row, column=1).value
                    play_time = ws.cell(row=row, column=12).value
                    perform_dates = ws.cell(row=row, column=13).value
                    opt1 = ws.cell(row=row, column=14).value or ''
                    opt2 = ws.cell(row=row, column=15).value or ''
                    opt3 = ws.cell(row=row, column=16).value or ''
                    other = ws.cell(row=row, column=17).value or ''
                    live_name = ws.cell(row=row, column=19).value or ''
                    bands.append({"band_name" : str(band_name), "play_time" : str(play_time), "perform_dates" : str(perform_dates), "opt1" : str(opt1), "opt2" : str(opt2), "opt3" : str(opt3), "other" : str(other)})
        except Exception:
            return []
        return bands



