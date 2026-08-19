import json, datetime, os, openpyxl
import customtkinter as ctk
from tkinter import messagebox

import config

class MainView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self.file_path = self.app.settings.get('excel_file_path', config.FILE_PATH)

        self.show_dashboard()

    def clear_frame(self):
        """フレーム内のウィジェットをすべて削除"""
        for widget in self.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_frame()

        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(padx=0, pady=0, fill='x')
        ctk.CTkLabel(title_frame, text='🏠 ホーム', font=config.FONT_TITLE).pack(side='left', pady=15, anchor="w")
        message_label = ctk.CTkLabel(title_frame, text='', font=config.FONT_TITLE, text_color='gray50')
        message_label.pack(side='left', padx=10, pady=15, anchor="w")
        
        # 前回起動日が設定されている場合、30日以上経過していれば確認ダイアログを表示
        try:
            prev = self.app.settings.get('last_startup')
            today = datetime.date.today()
            if prev:
                prev_date = datetime.date.fromisoformat(prev)
                delta_days = (today - prev_date).days
                if delta_days >= 30:
                    message_label.configure(text=f'最後のバンド登録から{delta_days}日経過しています。登録済みバンドを確認しましょう！', font=config.FONT_SUBTITLE, text_color=("#45965d", "#a3caaf"))
        except Exception:
            pass
        
        # 設定されたExcelファイルが存在しなければ警告表示
        if not os.path.exists(self.file_path):
            message_label.configure(text=f'設定されたExcelファイルが存在しません。設定を確認してください。', font=config.FONT_TITLE, text_color=("#ff4343", "#f5baba"))
            messagebox.showwarning("警告", "設定されたExcelファイルが存在しません。設定を確認してください。")

        # 通常モードのレイアウト（大きなタイルボタンでモダンに変身）
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(pady=0, fill='both', expand=True, padx=0)
        main_frame.grid_columnconfigure(0, weight=1, uniform="col1")
        main_frame.grid_columnconfigure(1, weight=1, uniform="col1")
        main_frame.grid_rowconfigure(0, weight=1)
        
        left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=5, uniform="row1")
        right_frame.grid_rowconfigure(1, weight=3, uniform="row1")
        right_frame.grid_columnconfigure(0, weight=1)

        nest_live_frame = ctk.CTkFrame(left_frame, border_color=("gray30", "gray70"), border_width=0)
        nest_live_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        
        # 次のライブ情報表示枠
        next_live = self.get_next_live()
        ctk.CTkLabel(nest_live_frame, text=f'次のライブ', font=config.FONT_TITLE).pack(padx=10, pady=5, anchor="w")
        ctk.CTkLabel(nest_live_frame, text='登録されている直近のライブ', font=config.FONT_SUBTITLE, text_color='gray50').pack(padx=10, pady=(0, 5), anchor="w")
        if next_live:
            # ライブ情報を表示
            ctk.CTkLabel(
                nest_live_frame, justify="left", anchor="w",
                text=f'ライブ名: {next_live["name"]}\n日程: {next_live["closest_date"].strftime("%Y-%m-%d")}～\n開始まで: {next_live["days_diff"]}日',
                font=(config.FONT_NAME, 18)).pack(padx=10, pady=5, anchor="w")
            
            # 追加済み／未追加バンド表示枠
            bands_frame = ctk.CTkFrame(nest_live_frame, fg_color="transparent")
            bands_frame.pack(padx=2, pady=0, fill="both", expand=True)
            bands_frame.grid_rowconfigure(0, weight=1, uniform="row1")
            bands_frame.grid_rowconfigure(1, weight=1, uniform="row1")
            bands_frame.grid_columnconfigure(0, weight=1)
            
            # タイムテーブル追加済みバンド情報を表示
            added_bands_frame = ctk.CTkFrame(bands_frame, fg_color="#a3caa3")
            added_bands_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
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
            button_frame.pack(padx=2, pady=0, side="bottom", expand=True)
            ctk.CTkButton(
                button_frame,
                text='ライブ情報編集', 
                font=config.FONT_LABEL_BUTTON,
                fg_color='transparent',
                text_color=("#3e909b", "#65e1f1"),
                command=lambda: self.app.register_live(default_live_name=next_live["name"])
                ).pack(pady=10, padx=2, side="left")
            ctk.CTkButton(
                button_frame,
                text='バンド登録・編集',
                font=config.FONT_LABEL_BUTTON,
                fg_color='transparent',
                text_color=("#3e909b", "#65e1f1"),
                command=lambda: self.app.register_band(default_tab="📝 登録済みバンドの管理", default_live_name=next_live["name"])
                ).pack(pady=10, padx=2, side="left")
            ctk.CTkButton(
                button_frame,
                text='バンド選出',
                font=config.FONT_LABEL_BUTTON,
                fg_color='transparent',
                text_color=("#3e909b", "#65e1f1"),
                command=lambda: self.app.register_band(default_tab="バンド選出", default_live_name=next_live["name"])
                ).pack(pady=10, padx=2, side="left")
        else:
            ctk.CTkLabel(nest_live_frame, text='情報なし', font=(config.FONT_NAME, 18)).pack(padx=10, pady=5, anchor="center")
            ctk.CTkButton(
                nest_live_frame,
                text='ライブ情報を登録する',
                font=config.FONT_LABEL_BUTTON,
                fg_color='transparent',
                text_color=("#3e909b", "#65e1f1"),
                command=lambda: self.app.register_live()
                ).pack(pady=10, padx=10, fill="x")

        # 最近の出席率表示枠
        atteendance_frame = ctk.CTkFrame(right_frame, border_color=("gray30", "gray70"), border_width=0)
        atteendance_frame.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="nsew")
        title_frame = ctk.CTkFrame(atteendance_frame, fg_color="transparent")
        title_frame.pack(padx=0, pady=0, fill="x")
        ctk.CTkLabel(title_frame, text='最近の出席', font=config.FONT_TITLE).pack(side="left", padx=10, pady=5, anchor="w")
        ctk.CTkButton(
            title_frame,
            text='出欠管理・確認',
            font=config.FONT_LABEL_BUTTON,
            fg_color='transparent',
            text_color=("#3e909b", "#65e1f1"),
            command=lambda: self.app.show_attendance_date_select()
            ).pack(side="right", padx=10, pady=5)
        ctk.CTkLabel(atteendance_frame, text='登録されている最近の出席情報', font=config.FONT_SUBTITLE, text_color='gray50').pack(padx=10, pady=(0, 5), anchor="w")
        date_frame = ctk.CTkFrame(atteendance_frame, fg_color="transparent")
        date_frame.pack(padx=0, pady=5, fill="both", expand=True)
        date_frame.grid_rowconfigure(0, weight=5, uniform="row1")
        date_frame.grid_rowconfigure(1, weight=3, uniform="row1")
        date_frame.grid_rowconfigure(2, weight=3, uniform="row1")
        date_frame.grid_columnconfigure(0, weight=1)
        latest_frame = ctk.CTkFrame(date_frame, fg_color="transparent")
        latest_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        second_frame = ctk.CTkFrame(date_frame, fg_color="transparent")
        second_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        third_frame = ctk.CTkFrame(date_frame, fg_color="transparent")
        third_frame.grid(row=2, column=0, padx=0, pady=0, sticky="nsew")

        attendance_data = self.get_attendance()[:3]
        if attendance_data:
            # 最新の出席日付を表示
            ctk.CTkLabel(latest_frame, text=f'{attendance_data[0]["date"]}', width=80, anchor="e", font=(config.FONT_NAME, 32)).pack(side="left", padx=10, pady=5)
            if attendance_data[0]["attendance_rate"] >= 80:
                fg_color = ("#45965d", "#a3caaf")  # 緑系
            elif attendance_data[0]["attendance_rate"] >= 50:
                fg_color = ("#cf6c0f", "#f5dfc6")  # 黄系
            else:
                fg_color = ("#ff4343", "#f5baba")  # 赤系
            ctk.CTkFrame(latest_frame, fg_color=fg_color, width=5).pack(side="left", fill="y", padx=0, pady=2)
            ctk.CTkLabel(latest_frame, text=f'出席率: {attendance_data[0]["attendance_rate"]}%', font=(config.FONT_NAME, 20, "bold"), anchor="w").pack(fill="x", padx=10, pady=(5, 0))
            ctk.CTkLabel(
                latest_frame, 
                text=f'○ 出席: {attendance_data[0]["present"]}\n△ 連絡あり: {attendance_data[0]["absent_with_contact"]}  × 無断欠席: {attendance_data[0]["absent_without_contact"]}\nオンライン: {attendance_data[0]["online"]}  忌引き等: {attendance_data[0]["bereavement"]}', 
                font=(config.FONT_NAME, 18), 
                anchor="w", 
                justify="left"
                ).pack(fill="x", padx=10, pady=(0, 5))


            # 2番目に新しい出席日付を表示
            if len(attendance_data) > 1:
                ctk.CTkLabel(second_frame, text=f'{attendance_data[1]["date"]}', width=80, anchor="e", font=(config.FONT_NAME, 32)).pack(side="left", padx=10, pady=5)
                if attendance_data[1]["attendance_rate"] >= 80:
                    fg_color = ("#45965d", "#a3caaf")  # 緑系
                elif attendance_data[1]["attendance_rate"] >= 50:
                    fg_color = ("#cf6c0f", "#f5dfc6")  # 黄系
                else:
                    fg_color = ("#ff4343", "#f5baba")  # 赤系
                ctk.CTkFrame(second_frame, fg_color=fg_color, width=5).pack(side="left", fill="y", padx=0, pady=2)
                ctk.CTkLabel(
                    second_frame, 
                    text=f'出席率: {attendance_data[1]["attendance_rate"]}%\n○ 出席: {attendance_data[1]["present"]}  △ 連絡あり: {attendance_data[1]["absent_with_contact"]}  × 無断欠席: {attendance_data[1]["absent_without_contact"]}\nオンライン・忌引き等: {attendance_data[1]["online"] + attendance_data[1]["bereavement"]}',
                    font=(config.FONT_NAME, 16),
                    anchor="w",
                    justify="left"
                    ).pack(side="left", padx=10, pady=5)

            # 3番目に新しい出席日付を表示
            if len(attendance_data) > 2:
                ctk.CTkLabel(third_frame, text=f'{attendance_data[2]["date"]}', width=80, anchor="e", font=(config.FONT_NAME, 32)).pack(side="left", padx=10, pady=5)
                if attendance_data[2]["attendance_rate"] >= 80:
                    fg_color = ("#45965d", "#a3caaf")  # 緑系
                elif attendance_data[2]["attendance_rate"] >= 50:
                    fg_color = ("#cf6c0f", "#f5dfc6")  # 黄系
                else:
                    fg_color = ("#ff4343", "#f5baba")  # 赤系
                ctk.CTkFrame(third_frame, fg_color=fg_color, width=5).pack(side="left", fill="y", padx=0, pady=2)
                ctk.CTkLabel(
                    third_frame,
                    text=f'出席率: {attendance_data[2]["attendance_rate"]}%\n○ 出席: {attendance_data[2]["present"]}  △ 連絡あり: {attendance_data[2]["absent_with_contact"]}  × 無断欠席: {attendance_data[2]["absent_without_contact"]}\nオンライン・忌引き等: {attendance_data[2]["online"] + attendance_data[2]["bereavement"]}',
                    font=(config.FONT_NAME, 16),
                    anchor="w",
                    justify="left"
                    ).pack(side="left", padx=10, pady=5)
        else:
            ctk.CTkLabel(latest_frame, text='情報なし', font=(config.FONT_NAME, 18)).pack(padx=10, pady=5, anchor="center")
            ctk.CTkButton(
                latest_frame,
                text='出席情報を登録する',
                font=config.FONT_LABEL_BUTTON,
                fg_color='transparent',
                text_color=("#3e909b", "#65e1f1"),
                command=lambda: self.app.show_attendance_date_select()
                ).pack(pady=10, padx=10, fill="x")

        # クイックアクセスボタン表示枠
        quick_access_frame = ctk.CTkFrame(right_frame, border_color=("gray30", "gray70"), border_width=0)
        quick_access_frame.grid(row=1, column=0, padx=0, pady=(5, 0), sticky="nsew")
        ctk.CTkLabel(quick_access_frame, text='クイックアクセス', font=config.FONT_TITLE).pack(padx=10, pady=5, anchor="w")
        ctk.CTkLabel(quick_access_frame, text='よく使う機能', font=config.FONT_SUBTITLE, text_color='gray50').pack(padx=10, pady=(0, 5), anchor="w")
        self.quick_button_frame = ctk.CTkFrame(quick_access_frame, fg_color="transparent")
        self.quick_button_frame.pack(padx=0, pady=0, fill="both", expand=True)
        self.quick_button_frame.grid_rowconfigure(0, weight=1, uniform="row1")
        self.quick_button_frame.grid_rowconfigure(1, weight=1, uniform="row1")
        self.quick_button_frame.grid_columnconfigure(0, weight=1, uniform="col1")
        self.quick_button_frame.grid_columnconfigure(1, weight=1, uniform="col1")
        
        self.show_quick_access_buttons()
        
    def clear_quick_buttons(self):
        """quick_button_frame 内のウィジェットをすべて削除"""
        for widget in self.quick_button_frame.winfo_children():
            widget.destroy()

    def show_quick_access_buttons(self, event=None):
        """クイックアクセスのボタンを表示"""
        if not hasattr(self, 'quick_button_frame') or not self.quick_button_frame.winfo_exists():
            return  # quick_button_frame が存在しない場合は何もしない

        self.clear_quick_buttons()
        self.app.load_settings()  # 設定を再読み込み
        quick_access_items = self.app.settings.get('quick_access', {}).get('items', [])
        if not quick_access_items:
            ctk.CTkLabel(self.quick_button_frame, text='クイックアクセスに登録されていません', font=(config.FONT_NAME, 16, "bold")).pack(padx=10, pady=5, anchor="center")
            ctk.CTkLabel(self.quick_button_frame, text='メニューを右クリックしてピン止めできます', font=(config.FONT_NAME, 14), text_color='gray50').pack(padx=10, pady=(0, 5), anchor="center")
            return
        
        vaild_btn_count = 0
        for item in quick_access_items:
            name = item.get("name", "不明な機能")
            fg_color = item.get("fg_color", "transparent")
            hover_color = item.get("hover_color", "gray")
            command_str = item.get("command", "")
            if hasattr(self.app, command_str):
                target_command = getattr(self.app, command_str)
                btn = ctk.CTkButton(
                    self.quick_button_frame,
                    text=name,
                    font=config.FONT_LABEL_BUTTON,
                    fg_color=fg_color,
                    hover_color=hover_color,
                    text_color="black",
                    command=target_command
                )
                r = vaild_btn_count // 2
                c = vaild_btn_count % 2
                btn.grid(row=r, column=c, pady=5, padx=10, sticky="nsew")
                # 右クリックメニューのバインド
                self.app.bind_pin_menu(widget=btn, name=name, fg_color=fg_color, hover_color=hover_color, command_str=command_str)
                vaild_btn_count += 1

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
            wb = openpyxl.load_workbook(self.file_path, data_only=True)
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

    def get_attendance(self):
        """出席情報を取得"""
        try:
            wb = openpyxl.load_workbook(self.file_path, data_only=True)
            ws = wb[config.SHEET_NAME]
            date_list = []
            for col in range(7, ws.max_column + 1):
                date_str = ws.cell(row=2, column=col).value
                if date_str:
                    try:
                        parts = date_str.split('/')
                        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                            date_list.append(date_str)
                    except:
                        continue
            
            def calculate_days_attendance_rate(date_str):
                """指定された日付の出席率を計算"""
                try:
                    date_col = None
                    for col in range(7, ws.max_column + 1):
                        cell_value = ws.cell(row=2, column=col).value
                        if cell_value and str(cell_value).strip() == date_str:
                            date_col = col
                            break
                    if date_col is None:
                        return {"total": 0, "present": 0, "absent_with_contact": 0, "absent_without_contact": 0, "online": 0, "bereavement": 0, "attendance_rate": 0.0}
                    
                    total_count = 0 # 有効な出席情報の総数
                    present_count = 0 # 出席の数
                    absent_with_contact_count = 0 # 連絡あり欠席の数
                    absent_without_contact_count = 0 # 無断欠席の数
                    online_count = 0 # オンライン出席の数
                    bereavement_count = 0 # 忌引き等の数

                    for row in range(3, ws.max_row + 1):
                        status = ws.cell(row=row, column=date_col).value
                        if status is not None:
                            total_count += 1
                            if str(status).strip() == '出席':
                                present_count += 1
                            elif str(status).strip() == '連絡あり':
                                absent_with_contact_count += 1
                            elif str(status).strip() == '無断欠席':
                                absent_without_contact_count += 1
                            elif str(status).strip() == 'オ':
                                online_count += 1
                            elif str(status).strip() == '忌引':
                                bereavement_count += 1
                    if total_count == 0:
                        return {"total": 0, "present": 0, "absent_with_contact": 0, "absent_without_contact": 0, "online": 0, "bereavement": 0, "attendance_rate": 0.0}
                    
                    attendance_rate = (present_count + online_count) / total_count * 100
                    return {
                        "total": total_count,
                        "present": present_count,
                        "absent_with_contact": absent_with_contact_count,
                        "absent_without_contact": absent_without_contact_count,
                        "online": online_count,
                        "bereavement": bereavement_count,
                        "attendance_rate": round(attendance_rate, 2)
                    }
                except Exception:
                    return {"total": 0, "present": 0, "absent_with_contact": 0, "absent_without_contact": 0, "online": 0, "bereavement": 0, "attendance_rate": 0.0}
            
            attendance_data = []
            for date_str in reversed(date_list):  # 日付を逆順にして最新のものから処理
                stats = calculate_days_attendance_rate(date_str)
                attendance_data.append({
                    "date": date_str,
                    "total": stats["total"],
                    "present": stats["present"],
                    "absent_with_contact": stats["absent_with_contact"],
                    "absent_without_contact": stats["absent_without_contact"],
                    "online": stats["online"],
                    "bereavement": stats["bereavement"],
                    "attendance_rate": stats["attendance_rate"]
                })      
            return attendance_data
        except Exception:
            return []

    def check_attendance_data_format(self, file_path):
        """出席データの形式が最新かどうかをチェック"""
        if not os.path.exists(file_path):
            return True  # ファイルが存在しない場合は形式チェックをスキップ
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            ws = wb[config.SHEET_NAME]
            # 3行目の7列目以降のセルを確認
            for col in range(7, ws.max_column + 1):
                cell_value = ws.cell(row=2, column=col).value
                if cell_value is not None:
                    for row in range(3, ws.max_row + 1):
                        status = ws.cell(row=row, column=col).value
                        if status not in ['出席', '連絡あり', '無断欠席', 'オ', '忌引', '', None]:
                            return False
            return True
        except Exception:
            return False
