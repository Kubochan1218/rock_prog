# 2026年6月19日更新 (CustomTkinterモダンデザイン版)

import datetime, openpyxl, re, os, sys
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk
import tkinter.font as tkfont
import customtkinter as ctk  # CustomTkinterの導入
import pandas as pd
import band_selection as bs
import attendance_calculation as ac
from top import TopWindow

FILE_PATH = 'attend_data.xlsx'
SHEET_NAME = '出欠状況'
FONT_NAME = 'Yu Gothic UI'

# アプリ全体のテーマカラー設定
ctk.set_appearance_mode("Light")  # "System", "Dark", "Light"
ctk.set_default_color_theme("green")  # "blue", "green", "dark-blue", "light-blue"

class AttendanceApp:
    def __init__(self, master):
        self.master = master
        master.title('ロック部 出席管理')
        master.geometry('1150x680')
        master.minsize(1050, 600)
        
        # ウィンドウの×ボタンに確認ダイアログを設定
        try:
            self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        except Exception:
            pass
            
        # 設定読み込み（操作支援など）
        self.load_settings()
        
        # -------------------------------------------------------------
        # 全体レイアウト：2カラム構成（左：固定サイドメニュー、右：動的画面）
        # -------------------------------------------------------------
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        
        # 左側：サイドバーフレーム
        self.sidebar_frame = ctk.CTkFrame(self.master, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)  # 設定ボタンを下に押し下げる
        
        # サークルロゴ/タイトル
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🎸 ロック部 出席管理", font=ctk.CTkFont(family=FONT_NAME, size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=25)
        
        # 常駐ナビゲーションボタン群
        self.btn_nav_top = ctk.CTkButton(self.sidebar_frame, text="🏠 トップ画面", fg_color="transparent", text_color=("gray10", "gray90"), font=(FONT_NAME, 16), anchor="w", command=self.show_top)
        self.btn_nav_top.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        
        self.btn_nav_attend = ctk.CTkButton(self.sidebar_frame, text="👥 出欠管理", fg_color="transparent", text_color=("gray10", "gray90"), font=(FONT_NAME, 16), anchor="w", command=self.show_attendance_date_select)
        self.btn_nav_attend.grid(row=2, column=0, padx=20, pady=8, sticky="ew")
        
        self.btn_nav_check = ctk.CTkButton(self.sidebar_frame, text="📅 ライブ管理", fg_color="transparent", text_color=("gray10", "gray90"), font=(FONT_NAME, 16), anchor="w", command=self.show_attendance_check)
        self.btn_nav_check.grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        
        self.btn_nav_band = ctk.CTkButton(self.sidebar_frame, text="🎤 バンド登録・選出", fg_color="transparent", text_color=("gray10", "gray90"), font=(FONT_NAME, 16), anchor="w", command=self.register_band)
        self.btn_nav_band.grid(row=4, column=0, padx=20, pady=8, sticky="ew")
        
        self.btn_nav_select = ctk.CTkButton(self.sidebar_frame, text="🕑 タイムテーブル", fg_color="transparent", text_color=("gray10", "gray90"), font=(FONT_NAME, 16), anchor="w", command=self.show_select_band)
        self.btn_nav_select.grid(row=5, column=0, padx=20, pady=8, sticky="ew")
        
        # 下部の固定設定ボタン
        self.btn_nav_settings = ctk.CTkButton(self.sidebar_frame, text="⚙ 設定メニュー", fg_color="transparent", text_color=("gray10", "gray90"), font=(FONT_NAME, 16), anchor="w", command=self.show_settings)
        self.btn_nav_settings.grid(row=6, column=0, padx=20, pady=25, sticky="s")
        
        # 右側：メインコンテンツ表示用フレーム
        self.main_frame = ctk.CTkFrame(self.master, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")
                    
        self.show_top()
        
        # 起動時ウォークスルー表示
        try:
            self.maybe_show_walkthrough()
        except Exception:
            pass

    def clear(self):
        """右側のメインコンテンツエリアのみを消去するよう修正"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_top(self):
        self.clear()
        ctk.CTkLabel(self.main_frame, text='ロック部 出席管理ダッシュボード', font=ctk.CTkFont(family=FONT_NAME, size=22, weight='bold')).pack(pady=15, anchor="w")
        
        # 操作支援情報
        try:
            if self.settings.get('operation_support', False):
                ctk.CTkLabel(self.main_frame, text='💡 操作支援モード有効: ボタンにマウスを合わせると説明が表示されます。', font=(FONT_NAME, 11), text_color='gray50').pack(pady=2, anchor="w")
        except Exception:
            pass

        # 前回起動日が設定されている場合、30日以上経過していれば確認ダイアログを表示
        try:
            prev = self.settings.get('last_startup')
            today = datetime.date.today()
            if prev:
                prev_date = datetime.date.fromisoformat(prev)
                delta_days = (today - prev_date).days
                if delta_days >= 30:
                    ctk.CTkLabel(self.main_frame, text=f'最後のバンド登録から{delta_days}日経過しています。登録済みバンドを確認しましょう！', font=(FONT_NAME, 16), text_color='green').pack(pady=10, anchor="w")
        except Exception:
            pass

            
        # ヘルプモード用レイアウト
        try:
            if self.settings.get('operation_support', False) and self.settings.get('help_mode', False):
                hl_frame = ctk.CTkFrame(self.main_frame)
                hl_frame.pack(pady=15, fill='both', expand=True)
                
                items = [
                    ('① 出欠をとる', '開く', self.show_attendance_date_select, '#bfff80'),
                    ('② 出席率の計算', '開く', self.show_attendance_check, '#80d4ff'),
                    ('③ バンド登録', '開く', self.register_band, '#ffff00'),
                    ('④ バンド選出', '開く', self.show_select_band, '#ffd480'),
                    ('⑤ タイムテーブル作成', '開く', self.make_timetable, '#d080ff'),
                ]
                prog = getattr(self, 'help_progress_index', 0)
                
                def make_help_cmd(idx, fn):
                    def inner():
                        try:
                            fn()
                            self.help_progress_index = max(getattr(self, 'help_progress_index', 0), idx + 1)
                        except Exception:
                            pass
                    return inner

                for i, (title, btn_text, cmd, default_color) in enumerate(items):
                    if i < prog:
                        color = "#00cf4f"  # 実行済み
                    elif i == prog:
                        color = "#174dff"  # 次に実行
                    else:
                        color = '#cccccc'  # 保留
                        default_color = '#cccccc'

                    row = ctk.CTkFrame(hl_frame, fg_color="transparent")
                    row.pack(fill='x', padx=20, pady=12)
                    
                    lbl = ctk.CTkLabel(row, text=title, font=(FONT_NAME, 14, 'bold'), text_color=color)
                    lbl.pack(side='left')

                    btn = ctk.CTkButton(row, text=btn_text, width=110, fg_color=default_color, text_color="black" if default_color != '#cccccc' else "gray60", font=(FONT_NAME, 12, 'bold'), command=make_help_cmd(i, cmd))
                    btn.pack(side='right', padx=10)
                    try:
                        self.add_tooltip(btn, f'{title} の画面を開きます')
                    except Exception:
                        pass
                        
                btn_exit = ctk.CTkButton(self.main_frame, text='ヘルプモードを終了', width=160, fg_color='#cccccc', text_color="black", font=(FONT_NAME, 12, 'bold'), command=self.toggle_help_mode)
                btn_exit.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)
                return
        except Exception:
            pass

        # 通常モードのレイアウト（大きなタイルボタンでモダンに変身）
        grid_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        grid_frame.pack(pady=20, fill="both", expand=True)
        grid_frame.grid_columnconfigure((0, 1), weight=1)
        
        btn_attendance = ctk.CTkButton(grid_frame, text='📅 出席をとる', height=80, command=self.show_attendance_date_select, fg_color='#bfff80', text_color='black', font=(FONT_NAME, 16, 'bold'))
        btn_attendance.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        self.add_tooltip(btn_attendance, '出欠を記録する画面を開きます')

        btn_check = ctk.CTkButton(grid_frame, text='📊 出欠状況の確認\n(出席率計算)', height=80, command=self.show_attendance_check, fg_color='#80d4ff', text_color='black', font=(FONT_NAME, 16, 'bold'))
        btn_check.grid(row=0, column=1, padx=15, pady=15, sticky="ew")
        self.add_tooltip(btn_check, '出席率の計算と出欠状況の確認を行います')

        btn_register = ctk.CTkButton(grid_frame, text='🎤 バンドの追加・編集・削除', height=80, command=self.register_band, fg_color='#ffff00', text_color='black', font=(FONT_NAME, 16, 'bold'))
        btn_register.grid(row=1, column=0, padx=15, pady=15, sticky="ew")
        self.add_tooltip(btn_register, 'バンドを新規登録・編集・削除します')
        
        btn_select = ctk.CTkButton(grid_frame, text='🔶 出演バンド選出', height=80, command=self.show_select_band, fg_color='#ffd480', text_color='black', font=(FONT_NAME, 16, 'bold'))
        btn_select.grid(row=1, column=1, padx=15, pady=15, sticky="ew")
        self.add_tooltip(btn_select, '応募バンドから出演バンドを選出します')

        btn_timetable = ctk.CTkButton(grid_frame, text='⏱️ タイムテーブル作成 (別ウィンドウ)', height=80, command=self.make_timetable, fg_color="#d080ff", text_color='black', font=(FONT_NAME, 16, 'bold'))
        btn_timetable.grid(row=2, column=0, columnspan=2, padx=15, pady=15, sticky="ew")
        self.add_tooltip(btn_timetable, 'タイムテーブル作成ウィンドウを開きます（別ウィンドウ）')
        
        # ヘルプモード切り替えボタン
        try:
            if self.settings.get('operation_support', False):
                btn_help_mode = ctk.CTkButton(self.main_frame, text='❓ ヘルプモード開始', width=150, height=35, command=self.toggle_help_mode, fg_color="#4375ff", font=(FONT_NAME, 13, 'bold'))
                btn_help_mode.place(relx=0.0, rely=1.0, anchor='sw', x=20, y=-20)
                self.add_tooltip(btn_help_mode, 'ヘルプモードに切り替えます（操作手順を案内します）')
        except Exception:
            pass

    def show_attendance_date_select(self):
        """出席日付選択画面を表示"""
        self.clear()
        ctk.CTkLabel(self.main_frame, text='出欠管理 - 出席をとる日付を選択します。', font=ctk.CTkFont(family=FONT_NAME, size=20, weight='bold')).pack(pady=15, anchor="w")
        
        btn_today = ctk.CTkButton(self.main_frame, text='📅 今日の出席をとる', width=200, height=45, fg_color='#66ff66', text_color='black', font=(FONT_NAME, 16, 'bold'), command=self.start_attendance_today)
        btn_today.pack(pady=10)
        self.add_tooltip(btn_today, '今日の日付で出席登録を開始します')
        
        btn_other = ctk.CTkButton(self.main_frame, text='📆 過去・別日の出席をとる', width=200, height=45, fg_color='#ff9900', text_color='black', font=(FONT_NAME, 16, 'bold'), command=self.start_attendance_otherday)
        btn_other.pack(pady=10)
        self.add_tooltip(btn_other, '別の日付で出席登録を開始します')
        
        ctk.CTkLabel(self.main_frame, text='', font=ctk.CTkFont(family=FONT_NAME, size=20, weight='bold')).pack(pady=15, anchor="w")
        ctk.CTkLabel(self.main_frame, text='出欠状況の確認 - 出欠状況をテキストファイルで出力します。', font=ctk.CTkFont(family=FONT_NAME, size=20, weight='bold')).pack(pady=15, anchor="w")
        date_frame = ctk.CTkFrame(self.main_frame)
        date_frame.pack(pady=15, fill="x", padx=10)
        date_candidates = self.get_available_dates()
        
        ctk.CTkLabel(date_frame, text='開始日:', font=(FONT_NAME, 16)).pack(side='left', padx=10, pady=10)
        start_combo = ctk.CTkComboBox(date_frame, font=(FONT_NAME, 16), width=130, values=date_candidates)
        start_combo.pack(side='left', padx=5, pady=10)
        
        ctk.CTkLabel(date_frame, text='終了日:', font=(FONT_NAME, 16)).pack(side='left', padx=10, pady=10)
        end_combo = ctk.CTkComboBox(date_frame, font=(FONT_NAME, 16), width=130, values=date_candidates)
        end_combo.pack(side='left', padx=5, pady=10)
        
        btn_check = ctk.CTkButton(self.main_frame, text='👁 出欠状況を出力(.txt)', width=200, height=45, fg_color='#4375ff', text_color='white', font=(FONT_NAME, 16, 'bold'), command=lambda: ac.calculate_rate_and_export(start_combo.get(), end_combo.get(), FILE_PATH, SHEET_NAME))
        btn_check.pack(pady=10)
        self.add_tooltip(btn_check, '出欠状況をテキストファイルに出力し、確認します')
        
        btn_top = ctk.CTkButton(self.main_frame, text='トップに戻る', fg_color='#ff0000', text_color='white', font=(FONT_NAME, 16), command=self.show_top)
        btn_top.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)

    def start_attendance_today(self):
        today = datetime.datetime.now().strftime('%m/%d').lstrip('0').replace('/0', '/')
        self.start_attendance(date=today)

    def start_attendance_otherday(self):
        while True:
            date = simpledialog.askstring('日付入力', '日付を「M/D」形式で入力してください（例: 10/2）')
            if date is None:
                return
            if re.fullmatch(r'\s*\d{1,2}/\d{1,2}\s*', date):
                try:
                    m, d = map(int, date.strip().split('/'))
                    if 1 <= m <= 12 and 1 <= d <= 31:
                        self.start_attendance(date=date.strip())
                        return
                    else:
                        messagebox.showerror('入力エラー', '月日は正しい範囲で入力してください。')
                except Exception:
                    messagebox.showerror('入力エラー', '日付の形式が正しくありません。')
            else:
                messagebox.showerror('入力エラー', '日付は「M/D」形式で入力してください（例: 10/2）')

    def start_attendance(self, date):
        self.df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=1, index_col=None)
        self.df = self.df.loc[:, ~self.df.columns.str.contains('^Unnamed')]
        self.date = date
        if date not in self.df.columns:
            self.df[date] = ''
        self.current_idx = 0
        self.show_attendance_entry()

    def show_attendance_entry(self):
        self.clear()
        if self.current_idx < 0:
            self.current_idx = 0
        if self.current_idx >= len(self.df):
            self.current_idx = len(self.df) - 1
        row = self.df.iloc[self.current_idx]
        
        def safe_str(val):
            import math
            return '' if val is None or (isinstance(val, float) and math.isnan(val)) else str(val)
            
        name = safe_str(row['氏名'])
        student_id = safe_str(row['学籍番号'])
        grade = safe_str(row['学年']) if '学年' in self.df.columns else ''
        faculty = safe_str(row['学部']) if '学部' in self.df.columns else ''

        info = f'No. {self.current_idx+1} / 全 {len(self.df)} 名\n氏名: {name}\n学籍番号: {student_id}\n学年: {grade}  学部: {faculty}\n対象日: {self.date}'
        ctk.CTkLabel(self.main_frame, text=info, font=ctk.CTkFont(family=FONT_NAME, size=14, weight='bold'), justify='left', anchor="w").pack(pady=15, fill="x")

        mark_defs = [
            ('出席', '〇 出席', '#66ff66'),
            ('連絡あり', '△ 連絡あり欠席', '#ffff66'),
            ('無断欠席', '× 無断欠席', '#ff0000'),
            ('オ', 'オンライン', '#cccccc'),
            ('忌引', '忌引き等', '#cccccc'),
        ]
        
        btn_frame1 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame1.pack(pady=5)
        btn_frame2 = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame2.pack(pady=5)
        
        for mark, label, color in mark_defs[:3]:
            b = ctk.CTkButton(btn_frame1, text=label, width=140, height=40, fg_color=color, text_color='black', font=(FONT_NAME, 13, 'bold'), command=lambda m=mark: self.set_attendance(m))
            b.pack(side='left', padx=6)
            self.add_tooltip(b, f'{label} を記録します')
            
        for mark, label, color in mark_defs[3:]:
            b2 = ctk.CTkButton(btn_frame2, text=label, width=140, height=40, fg_color=color, text_color='black', font=(FONT_NAME, 13, 'bold'), command=lambda m=mark: self.set_attendance(m))
            b2.pack(side='left', padx=6)
            self.add_tooltip(b2, f'{label} を記録します')

        nav_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        nav_frame.pack(pady=20)
        
        btn_prev = ctk.CTkButton(nav_frame, text='◀ 前の人へ', fg_color='#ff9900', text_color='black', font=(FONT_NAME, 12), command=self.prev_person)
        btn_prev.pack(side='left', padx=10)
        
        btn_next_nav = ctk.CTkButton(nav_frame, text='次の人へ ▶', fg_color='#66ff66', text_color='black', font=(FONT_NAME, 12), command=self.next_person)
        btn_next_nav.pack(side='left', padx=10)

        btn_top = ctk.CTkButton(self.main_frame, text='保存して終了', width=120, fg_color='#ff0000', text_color='white', font=(FONT_NAME, 12, 'bold'), command=self.save_and_back_to_top)
        btn_top.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)

    def set_attendance(self, mark):
        self.df.at[self.current_idx, self.date] = mark
        self.next_person()

    def prev_person(self):
        self.current_idx -= 1
        if self.current_idx < 0:
            self.current_idx = 0
        self.show_attendance_entry()

    def next_person(self):
        self.current_idx += 1
        def is_empty_name(idx):
            import math
            if idx >= len(self.df):
                return True
            val = self.df.iloc[idx]['氏名']
            return (val is None) or (isinstance(val, float) and math.isnan(val)) or (str(val).strip() == '')
        if self.current_idx >= len(self.df) or is_empty_name(self.current_idx):
            messagebox.showinfo('完了', '全員分の出欠登録が完了しました。')
            self.save_and_back_to_top()
        else:
            self.show_attendance_entry()

    def save_and_back_to_top(self):
        try:
            wb = openpyxl.load_workbook(FILE_PATH)
            ws = wb[SHEET_NAME]
            target_col = None
            for col in range(1, ws.max_column + 1):
                if str(ws.cell(row=2, column=col).value) == str(self.date):
                    target_col = col
                    break
            if target_col is None:
                for col in range(7, ws.max_column + 1):
                    val = ws.cell(row=2, column=col).value
                    if val is None or str(val).strip() == '':
                        target_col = col
                        break
            if target_col is None:
                target_col = ws.max_column + 1
                
            from copy import copy
            date_cell = ws.cell(row=2, column=target_col)
            if date_cell.value is None or str(date_cell.value).strip() == '':
                if target_col > 1:
                    left_cell = ws.cell(row=2, column=target_col-1)
                    date_cell.font = copy(left_cell.font)
                    date_cell.alignment = copy(left_cell.alignment)
                    date_cell.border = copy(left_cell.border)
                    date_cell.fill = copy(left_cell.fill)
                date_cell.value = self.date

            id_col = None
            for col in range(1, ws.max_column + 1):
                if str(ws.cell(row=2, column=col).value) == '学籍番号':
                    id_col = col
                    break
            if id_col is None:
                raise Exception('学籍番号列が見つかりません')

            for idx, row in self.df.iterrows():
                student_id = str(row['学籍番号'])
                excel_row = None
                for r in range(3, ws.max_row + 1):
                    if str(ws.cell(row=r, column=id_col).value) == student_id:
                        excel_row = r
                        break
                if excel_row is None:
                    continue
                cell = ws.cell(row=excel_row, column=target_col)
                if target_col > 1:
                    left_cell = ws.cell(row=excel_row, column=target_col-1)
                    cell.font = copy(left_cell.font)
                    cell.alignment = copy(left_cell.alignment)
                    cell.border = copy(left_cell.border)
                    cell.fill = copy(left_cell.fill)
                cell.value = row[self.date]
            wb.save(FILE_PATH)
            messagebox.showinfo('保存完了', 'Excelファイルを保存しました。')
        except Exception as e:
            messagebox.showerror('保存エラー', f'Excel保存に失敗しました: {e}')
        self.show_top()

    def show_attendance_check(self):
        """出欠状況の確認画面"""
        self.clear()
        ctk.CTkLabel(self.main_frame, text='出欠状況の確認・出席率計算', font=ctk.CTkFont(family=FONT_NAME, size=18, weight='bold')).pack(pady=15, anchor="w")
        ctk.CTkLabel(self.main_frame, text='計算を行う対象期間を選択してください。', font=(FONT_NAME, 12)).pack(pady=5, anchor="w")
        
        date_frame = ctk.CTkFrame(self.main_frame)
        date_frame.pack(pady=15, fill="x", padx=10)
        date_candidates = self.get_available_dates()
        
        ctk.CTkLabel(date_frame, text='開始日:', font=(FONT_NAME, 12)).pack(side='left', padx=10, pady=10)
        start_combo = ctk.CTkComboBox(date_frame, font=(FONT_NAME, 12), width=130, values=date_candidates)
        start_combo.pack(side='left', padx=5, pady=10)
        
        ctk.CTkLabel(date_frame, text='終了日:', font=(FONT_NAME, 12)).pack(side='left', padx=10, pady=10)
        end_combo = ctk.CTkComboBox(date_frame, font=(FONT_NAME, 12), width=130, values=date_candidates)
        end_combo.pack(side='left', padx=5, pady=10)
        
        calc_btn = ctk.CTkButton(self.main_frame, text='📊 出席率を計算して記録', width=180, height=40, fg_color='#80bfff', text_color='black', font=(FONT_NAME, 13, 'bold'), command=lambda: ac.calculate_attendance_rate(start_combo.get(), end_combo.get(), FILE_PATH, SHEET_NAME))
        calc_btn.pack(pady=20)
        self.add_tooltip(calc_btn, '指定した期間の出席率を計算して記録します')
        
        back_btn = ctk.CTkButton(self.main_frame, text='トップに戻る', width=120, fg_color='#ff0000', text_color='white', font=(FONT_NAME, 12), command=self.show_top)
        back_btn.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)

    def get_available_dates(self):
        try:
            df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=1, index_col=None)
            date_list = []
            for col in df.columns[6:]:
                if pd.notna(col) and str(col).strip() and '/' in str(col):
                    date_str = str(col).strip()
                    try:
                        parts = date_str.split('/')
                        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                            date_list.append(date_str)
                    except:
                        continue
            def date_sort_key(date_str):
                try:
                    month, day = map(int, date_str.split('/'))
                    return month * 100 + day
                except:
                    return 0
            date_list.sort(key=date_sort_key)
            return date_list
        except Exception:
            return []

    def register_band(self):
        """バンド登録画面を表示"""
        try:
            self.settings['last_startup'] = datetime.date.today().isoformat()
            self.save_settings()
        except Exception:
            pass
            
        def show_date_assign_dialog():
            from tkcalendar import Calendar
            assign_win = ctk.CTkToplevel(self.master)
            assign_win.title('出演日割り当て')
            assign_win.geometry('360(')
            assign_win.geometry('360x650')
            assign_win.attributes("-topmost", True)  # ダイアログを最前面に表示
            
            ctk.CTkLabel(assign_win, text='ライブの日程（枠番号）を設定', font=ctk.CTkFont(family=FONT_NAME, size=14, weight='bold')).pack(pady=10)
            ctk.CTkLabel(assign_win, text='※日付部分をクリックするとカレンダーが開きます', font=(FONT_NAME, 11), text_color="gray").pack(pady=2)
            
            date_vars = {}
            label_vars = {}
            
            def open_calendar(num):
                cal_win = ctk.CTkToplevel(assign_win)
                cal_win.title(f'[{num}]の日付選択')
                cal_win.attributes("-topmost", True)
                cal = Calendar(cal_win, selectmode='day', date_pattern='yyyy-mm-dd')
                cal.pack(padx=15, pady=15)
                
                def set_date():
                    date_vars[num].set(cal.get_date())
                    label_vars[num].configure(text=f'{num}日目:  {cal.get_date()}')
                    cal_win.destroy()
                    
                btn_cal_ok = ctk.CTkButton(cal_win, text='決定', command=set_date)
                btn_cal_ok.pack(pady=10)
                
            frame = ctk.CTkScrollableFrame(assign_win, height=420)
            frame.pack(pady=10, fill='x', padx=15)
            
            for i in range(1, 11):
                date_vars[i] = tk.StringVar(value='')
                label = ctk.CTkLabel(frame, text=f'{i}日目:  [クリックして日付選択]', font=(FONT_NAME, 12), width=260, anchor='w', fg_color=("gray85", "gray25"), corner_radius=6)
                label.grid(row=i-1, column=0, padx=10, pady=5, ipady=4)
                label.bind('<Button-1>', lambda e, n=i: open_calendar(n))
                label_vars[i] = label
                
            def save_dates():
                self._date_assign_map = {}
                self.date_assignments = {}
                for i in range(1, 11):
                    self._date_assign_map[str(i)] = date_vars[i].get()
                    self.date_assignments[f'[{i}]'] = date_vars[i].get()
                assign_win.destroy()
                proceed_band_register()
                
            btn_assign_save = ctk.CTkButton(assign_win, text='この日程で保存', font=(FONT_NAME, 12, 'bold'), fg_color='#bfff80', text_color='black', width=140, command=save_dates)
            btn_assign_save.pack(pady=15)

        def proceed_band_register():
            file_path = filedialog.askopenfilename(title='応募バンド情報のExcelファイルを選択', filetypes=[('Excelファイル', '*.xlsx;*.xls')])
            if not file_path:
                return
            try:
                df_all = pd.read_excel(file_path)
                df_band = df_all.iloc[:, 2:]
            except Exception as e:
                messagebox.showerror('エラー', f'Excelファイルの読み込みに失敗しました:\n{e}')
                return
            self._band_register_queue = []
            for idx, row in df_band.iterrows():
                band_name = str(row.iloc[0])
                members_raw = str(row.iloc[2]) if len(row) > 2 else ''
                self._band_register_queue.append((band_name, members_raw, row))
            if self._band_register_queue:
                next_band = self._band_register_queue.pop(0)
                self.show_band_member_check(*next_band)

        if not hasattr(self, '_date_assign_map'):
            show_date_assign_dialog()
        else:
            proceed_band_register()

    def _convert_perform_dates(self, perform_date_str):
        date_assignments = getattr(self, 'date_assignments', {})
        tokens = re.findall(r'\[\d+\]', str(perform_date_str))
        if not tokens:
            return ''
        out_dates = []
        for tok in tokens:
            if tok == '[0]':
                all_dates = [v for k, v in date_assignments.items() if v]
                out_dates.extend([d for d in all_dates if d])
            else:
                date = date_assignments.get(tok)
                if date:
                    out_dates.append(date)
        return ';'.join(out_dates)

    def show_band_member_check(self, band_name, members_raw, row_obj=None):
        """バンド登録のメンバー確認画面を表示"""
        if hasattr(self, '_band_member_frame') and self._band_member_frame:
            self._band_member_frame.destroy()
            
        self.clear()
        self._band_member_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self._band_member_frame.pack(fill='both', expand=True)
        win = self._band_member_frame

        ctk.CTkLabel(win, text=f'🎤 応募バンド名簿確認: {band_name}', font=ctk.CTkFont(family=FONT_NAME, size=16, weight='bold')).pack(pady=10, anchor="w")

        members_str = re.sub(r'[ \u3000]', '', members_raw)
        member_lines = [line for line in members_str.splitlines() if line.strip()]

        try:
            df_roster = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=1)
        except Exception as e:
            messagebox.showerror('エラー', f'名簿データの取得に失敗しました:\n{e}')
            return
        roster_names = list(df_roster['氏名'].dropna().astype(str))

        def similarity(a, b):
            from difflib import SequenceMatcher
            return SequenceMatcher(None, a, b).ratio()

        matched_members = []
        for mline in member_lines:
            best_match = None
            best_score = 0
            for name in roster_names:
                score = similarity(mline, name)
                if score > best_score:
                    best_score = score
                    best_match = name
            if best_score >= 0.3:
                matched_members.append(best_match)

        # 3カラム構造のデータ確認エリア
        h_frame = ctk.CTkFrame(win, fg_color="transparent")
        h_frame.pack(pady=10, fill='both', expand=True)

        # 左：インポート情報
        left_frame = ctk.CTkFrame(h_frame)
        left_frame.pack(side='left', padx=8, fill='both', expand=True)
        ctk.CTkLabel(left_frame, text='元の読込テキスト', font=(FONT_NAME, 12, 'bold')).pack(pady=5)
        ctk.CTkLabel(left_frame, text=members_raw, font=(FONT_NAME, 11), justify='left', wraplength=200).pack(pady=5, padx=10)

        # 中：自動名寄せ結果
        center_frame = ctk.CTkFrame(h_frame)
        center_frame.pack(side='left', padx=8, fill='both', expand=True)
        ctk.CTkLabel(center_frame, text='自動判定部員', font=(FONT_NAME, 12, 'bold')).pack(pady=5)
        for name in matched_members:
            ctk.CTkLabel(center_frame, text=f"👤 {name}", font=(FONT_NAME, 11)).pack(pady=2, anchor="w", padx=15)

        # 右：手動補正用コンボボックス
        right_frame = ctk.CTkFrame(h_frame)
        right_frame.pack(side='left', padx=8, fill='both', expand=True)
        max_members = 10
        remain = max_members - len(matched_members)
        add_combos = []
        
        if remain > 0:
            ctk.CTkLabel(right_frame, text=f'手動追加 (枠数:{remain})', font=(FONT_NAME, 12, 'bold')).pack(pady=5)
            candidate_names = [n for n in roster_names if n not in matched_members]
            scroll_right = ctk.CTkScrollableFrame(right_frame, fg_color="transparent", height=180)
            scroll_right.pack(fill='both', expand=True, padx=5, pady=5)
            
            for i in range(remain):
                cb = ctk.CTkComboBox(scroll_right, values=[''] + candidate_names, font=(FONT_NAME, 11), width=160)
                cb.pack(pady=2)
                cb.set('')
                add_combos.append(cb)

        def save_band_to_excel():
            members_final = matched_members + [cb.get() for cb in add_combos if cb.get()]
            while len(members_final) < 10:
                members_final.append('')
            l_val = str(row_obj.iloc[1]) if row_obj is not None and len(row_obj) > 1 else ''
            m_val_raw = str(row_obj.iloc[3]) if row_obj is not None and len(row_obj) > 3 else ''
            bracket_nums = re.findall(r'\[\d+\]', m_val_raw)
            converted_dates = [self._convert_perform_dates(bn) for bn in bracket_nums]
            m_val = ';'.join([d for d in converted_dates if d])
            
            n_val = o_val = p_val = ''
            if row_obj is not None:
                opt_cols = [i for i, col in enumerate(row_obj.index) if '[opt1]' in str(col)]
                n_val = str(row_obj.iloc[opt_cols[0]]) if len(opt_cols) > 0 else ''
                opt_cols2 = [i for i, col in enumerate(row_obj.index) if '[opt2]' in str(col)]
                o_val = str(row_obj.iloc[opt_cols2[0]]) if len(opt_cols2) > 0 else ''
                opt_cols3 = [i for i, col in enumerate(row_obj.index) if '[opt3]' in str(col)]
                p_val = str(row_obj.iloc[opt_cols3[0]]) if len(opt_cols3) > 0 else ''
            q_val = ''
            if row_obj is not None:
                for i, col in enumerate(row_obj.index[4:], 4):
                    if not any(f'[opt{n}]' in str(col) for n in range(1, 4)):
                        q_val = str(row_obj.iloc[i])
                        break
                        
            band_row = [band_name]
            band_row.extend(members_final)
            band_row.extend([l_val, m_val, n_val, o_val, p_val, q_val])
            while len(band_row) < 17:
                band_row.append('')
            band_row.append(0)
            
            try:
                wb = openpyxl.load_workbook(FILE_PATH)
                sheet_name = '登録済みバンド'
                if sheet_name not in wb.sheetnames:
                    ws = wb.create_sheet(sheet_name)
                else:
                    ws = wb[sheet_name]
                row_idx = None
                for r in range(1, ws.max_row + 2):
                    if ws.cell(row=r, column=1).value in (None, ''):
                        row_idx = r
                        break
                if row_idx is None:
                    row_idx = ws.max_row + 1
                for col, val in enumerate(band_row, 1):
                    ws.cell(row=row_idx, column=col).value = val
                wb.save(FILE_PATH)
                messagebox.showinfo('保存完了', f'「{band_name}」を登録しました。')
                
                if hasattr(self, '_band_register_queue') and self._band_register_queue:
                    next_band = self._band_register_queue.pop(0)
                    self.show_band_member_check(*next_band)
                else:
                    self.show_top()
            except Exception as e:
                messagebox.showerror('保存エラー', f'Excel保存に失敗しました:\n{e}')

        # 警告表示＆補助メタ情報
        bottom_frame = ctk.CTkFrame(win, fg_color="transparent")
        bottom_frame.pack(pady=5, fill='x')
        
        duplicate_band = False
        try:
            wb = openpyxl.load_workbook(FILE_PATH)
            sheet_name = '登録済みバンド'
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                for r in ws.iter_rows(min_row=1, max_col=1, values_only=True):
                    if r[0] == band_name:
                        duplicate_band = True
                        break
        except Exception:
            pass

        if duplicate_band:
            ctk.CTkLabel(bottom_frame, text='⚠️ 同名のバンドがすでに登録されています。上書き保存にご注意ください。', font=(FONT_NAME, 11, 'bold'), fg_color='#ffff66', text_color='black', corner_radius=6).pack(pady=4, fill="x")
        else:
            ctk.CTkLabel(bottom_frame, text='✨ バンド名の重複はありません。', font=(FONT_NAME, 11, 'bold'), fg_color='#ccffcc', text_color='black', corner_radius=6).pack(pady=4, fill="x")

        info_frame = ctk.CTkFrame(win)
        info_frame.pack(pady=5, fill='x', padx=5)
        
        l_val = str(row_obj.iloc[1]) if row_obj is not None and len(row_obj) > 1 else ''
        m_val = self._convert_perform_dates(str(row_obj.iloc[3]) if row_obj is not None and len(row_obj) > 3 else '')
        
        ctk.CTkLabel(info_frame, text=f'⏱ 演奏希望時間: {l_val}分  📅 変換後出演希望日: {m_val}', font=(FONT_NAME, 11, 'bold')).pack(anchor='w', padx=10, pady=4)

        # アクションボタン群
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=10)

        btn_save = ctk.CTkButton(btn_frame, text='この内容で登録', font=(FONT_NAME, 12, 'bold'), fg_color='#bfff80', text_color='black', width=130, command=save_band_to_excel)
        btn_save.pack(side='left', padx=6)

        def skip_to_next_band():
            if hasattr(self, '_band_register_queue') and self._band_register_queue:
                next_band = self._band_register_queue.pop(0)
                self.show_band_member_check(*next_band)
            else:
                self.show_top()

        btn_next = ctk.CTkButton(btn_frame, text='スキップして次へ', font=(FONT_NAME, 12), fg_color='#ffe680', text_color='black', width=130, command=skip_to_next_band)
        btn_next.pack(side='left', padx=6)

        btn_top = ctk.CTkButton(win, text='中断して戻る', width=120, fg_color='#ff0000', text_color='white', font=(FONT_NAME, 12), command=self.show_top)
        btn_top.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)

    def clear_registered_bands(self):
        try:
            if not messagebox.askyesno('確認', '登録済みのバンド情報をすべて削除します。よろしいですか？', parent=self.master):
                return
        except Exception:
            return
        try:
            wb = openpyxl.load_workbook(FILE_PATH)
            sheet_name = '登録済みバンド'
            if sheet_name not in wb.sheetnames:
                messagebox.showinfo('情報', '登録済みバンドのシートが見つかりません。', parent=self.master)
                return
            ws = wb[sheet_name]
            first_cell = ws.cell(row=1, column=1).value
            start_row = 2 if first_cell and 'バンド' in str(first_cell) else 1
            for r in range(start_row, ws.max_row + 1):
                for c in range(1, ws.max_column + 1):
                    ws.cell(row=r, column=c).value = None
            wb.save(FILE_PATH)
            messagebox.showinfo('完了', '登録済みのバンド情報をすべて削除しました。', parent=self.master)
        except Exception as e:
            messagebox.showerror('エラー', f'バンド情報の削除に失敗しました:\n{e}', parent=self.master)

    def show_select_band(self):
        """出演バンド選出画面を表示"""
        self.clear()
        ctk.CTkLabel(self.main_frame, text='出演バンドのオート選出設定', font=ctk.CTkFont(family=FONT_NAME, size=18, weight='bold')).pack(pady=15, anchor="w")
        
        frm = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frm.pack(pady=10, fill="x")
        
        ctk.CTkLabel(frm, text='出席率参照期間', font=(FONT_NAME, 12)).grid(row=0, column=0, sticky='e', pady=8, padx=5)
        period_list = []
        try:
            wb = openpyxl.load_workbook(FILE_PATH, data_only=True)
            ws = wb['出席率記録']
            for col in range(7, ws.max_column + 1):
                val = ws.cell(row=2, column=col).value
                if val is not None and str(val).strip() != '':
                    period_list.append(str(val).strip())
        except Exception:
            pass
        if not period_list:
            period_list = ['期間未登録']
            
        period_combo = ctk.CTkComboBox(frm, values=period_list, font=(FONT_NAME, 12), width=160)
        period_combo.grid(row=0, column=1, padx=8, pady=8, sticky='w')
        period_combo.set(period_list[0])
        
        btn_calc = ctk.CTkButton(frm, text='期間計算へ', font=(FONT_NAME, 11), fg_color='#80d4ff', text_color='black', width=90, command=self.show_attendance_check)
        btn_calc.grid(row=0, column=2, padx=8, pady=8, sticky='w')
        
        slots_var = tk.IntVar(value=8)
        ctk.CTkLabel(frm, text='最大募集バンド枠数', font=(FONT_NAME, 12)).grid(row=1, column=0, sticky='e', pady=8, padx=5)
        ctk.CTkEntry(frm, textvariable=slots_var, font=(FONT_NAME, 12), width=120).grid(row=1, column=1, padx=8, pady=8, sticky='w')
        
        total_time_var = tk.IntVar(value=240)
        ctk.CTkLabel(frm, text='イベント総枠時間 (分)', font=(FONT_NAME, 12)).grid(row=2, column=0, sticky='e', pady=8, padx=5)
        ctk.CTkEntry(frm, textvariable=total_time_var, font=(FONT_NAME, 12), width=120).grid(row=2, column=1, padx=8, pady=8, sticky='w')
        
        change_time_var = tk.IntVar(value=10)
        ctk.CTkLabel(frm, text='バンド間転換・リハ時間 (分)', font=(FONT_NAME, 12)).grid(row=3, column=0, sticky='e', pady=8, padx=5)
        ctk.CTkEntry(frm, textvariable=change_time_var, font=(FONT_NAME, 12), width=120).grid(row=3, column=1, padx=8, pady=8, sticky='w')
        
        def on_select_band():
            self.select_band(period_combo.get(), slots_var.get(), total_time_var.get(), change_time_var.get())
            
        btn_start_select = ctk.CTkButton(frm, text='🚀 アルゴリズム選出を開始', font=(FONT_NAME, 14, 'bold'), fg_color='#bfff80', text_color='black', width=200, height=45, command=on_select_band)
        btn_start_select.grid(row=4, column=0, columnspan=3, pady=25)
        
        btn_top = ctk.CTkButton(self.main_frame, text='トップに戻る', width=120, fg_color='#ff0000', text_color='white', font=(FONT_NAME, 12), command=self.show_top)
        btn_top.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)

    def select_band(self, period, slots, total_time, change_time):
        result_text = bs.select_bands(period, slots, total_time, change_time, FILE_PATH, self.master)
        win = ctk.CTkToplevel(self.master)
        win.title('出演バンド選出結果')
        win.geometry('480x560')
        win.attributes("-topmost", True)
        
        txt = ctk.CTkTextbox(win, font=(FONT_NAME, 12), width=440, height=360)
        txt.pack(padx=15, pady=15, fill='both', expand=True)
        txt.insert('1.0', result_text)
        txt.configure(state='disabled')
        
        def select_all():
            self.master.clipboard_clear()
            self.master.clipboard_append(result_text)
            messagebox.showinfo('コピー', '選出ログをクリップボードにコピーしました。', parent=win)
            
        btn_copy = ctk.CTkButton(win, text='📋 結果をコピー', font=(FONT_NAME, 11), width=140, command=select_all)
        btn_copy.pack(pady=6)
        
        def show_applied_order():
            try:
                wb = openpyxl.load_workbook(FILE_PATH, data_only=True)
                ws = wb['登録済みバンド']
                band_names = []
                for row in range(1, ws.max_row + 1):
                    name = ws.cell(row=row, column=1).value
                    r_val = ws.cell(row=row, column=18).value
                    if name and r_val == 1:
                        band_names.append(str(name))
                result = '\n'.join(band_names) if band_names else '該当バンドなし'
            except Exception as e:
                result = f'エラー: {e}'
                
            win2 = ctk.CTkToplevel(win)
            win2.title('出演バンド（応募順）')
            win2.geometry('400x450')
            win2.attributes("-topmost", True)
            
            txt2 = ctk.CTkTextbox(win2, font=(FONT_NAME, 12), width=360, height=320)
            txt2.pack(padx=15, pady=15, fill='both', expand=True)
            txt2.insert('1.0', result)
            txt2.configure(state='disabled')
            
            def select_all2():
                self.master.clipboard_clear()
                self.master.clipboard_append(result)
                messagebox.showinfo('コピー', '一覧をコピーしました。', parent=win2)
                
            btn2 = ctk.CTkButton(win2, text='コピー', font=(FONT_NAME, 11), command=select_all2)
            btn2.pack(pady=5)
            
        btn_applied = ctk.CTkButton(win, text='📄 応募順でリストを表示', font=(FONT_NAME, 11), width=140, command=show_applied_order)
        btn_applied.pack(pady=4)

    def make_timetable(self):
        try:
            wb = openpyxl.load_workbook(FILE_PATH, data_only=True)
            ws = wb['登録済みバンド']
            bands = []
            for row in range(1, ws.max_row + 1):
                r_val = ws.cell(row=row, column=18).value
                if r_val == 1:
                    band_name = ws.cell(row=row, column=1).value
                    play_time = ws.cell(row=row, column=12).value
                    perform_dates = ws.cell(row=row, column=13).value
                    opt1 = ws.cell(row=row, column=14).value or ''
                    opt2 = ws.cell(row=row, column=15).value or ''
                    opt3 = ws.cell(row=row, column=16).value or ''
                    other = ws.cell(row=row, column=17).value or ''
                    bands.append([str(band_name), str(play_time), str(perform_dates), str(opt1), str(opt2), str(opt3), str(other)])
            with open('bands.csv', 'w', encoding='utf-8', newline='') as f:
                import csv
                writer = csv.writer(f)
                writer.writerow(['バンド名', '演奏時間', '出演日', 'オプション1', 'オプション2', 'オプション3', 'その他'])
                for band in bands:
                    writer.writerow(band)
        except Exception as e:
            messagebox.showerror('CSV出力エラー', f'bands.csvの出力に失敗しました: {e}')
        app = TopWindow()
        app.mainloop()

    def show_settings(self):
        self.clear()
        ctk.CTkLabel(self.main_frame, text='システム環境設定', font=ctk.CTkFont(family=FONT_NAME, size=20, weight='bold')).pack(pady=20, anchor="w")
        
        btn_excel = ctk.CTkButton(self.main_frame, text='📁 Excelデータソースの設定', font=(FONT_NAME, 13), text_color='white', width=220, height=42, command=self.show_excel_file_settings, fg_color="#00bb44")
        btn_excel.pack(pady=10, anchor="w")
        
        btn_op = ctk.CTkButton(self.main_frame, text='💡 操作支援・ガイド設定', font=(FONT_NAME, 13), text_color='white', width=220, height=42, command=self.show_operation_support_settings, fg_color="#35cbfd")
        btn_op.pack(pady=10, anchor="w")
        
        btn_top = ctk.CTkButton(self.main_frame, text='トップに戻る', width=120, fg_color='#ff0000', text_color='white', font=(FONT_NAME, 12), command=self.show_top)
        btn_top.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)

    def show_excel_file_settings(self):
        settings_win = ctk.CTkToplevel(self.master)
        settings_win.title('Excelファイルの設定')
        settings_win.geometry('420x220')
        settings_win.attributes("-topmost", True)
        
        ctk.CTkLabel(settings_win, text='Excelターゲットパス設定', font=ctk.CTkFont(family=FONT_NAME, size=13, weight="bold")).pack(pady=10)
        ctk.CTkLabel(settings_win, text='※アプリと同じディレクトリ内の相対パス、またはフルパスを指定', font=(FONT_NAME, 11), text_color='gray').pack(pady=2)
        
        file_var = tk.StringVar(value=globals().get('FILE_PATH', 'attend_data.xlsx'))
        entry = ctk.CTkEntry(settings_win, textvariable=file_var, font=(FONT_NAME, 12), width=320)
        entry.pack(pady=10)

        def save_file_path():
            new_path = file_var.get().strip()
            if new_path:
                globals()['FILE_PATH'] = new_path
                messagebox.showinfo('設定', f'ターゲットファイルを「{new_path}」に変更しました。', parent=settings_win)
                settings_win.destroy()
            else:
                messagebox.showerror('エラー', '有効なファイル名を入力してください。', parent=settings_win)

        btn_save = ctk.CTkButton(settings_win, text='適用して保存', font=(FONT_NAME, 12, 'bold'), command=save_file_path, width=120, fg_color='#bfff80', text_color='black')
        btn_save.pack(pady=15)

    def show_operation_support_settings(self):
        settings_win = ctk.CTkToplevel(self.master)
        settings_win.title('操作支援の設定')
        settings_win.geometry('450x220')
        settings_win.attributes("-topmost", True)
        
        ctk.CTkLabel(settings_win, text='操作支援・ナビゲーションシステム', font=ctk.CTkFont(family=FONT_NAME, size=14, weight='bold')).pack(pady=12)
        
        op_var = tk.BooleanVar(value=self.settings.get('operation_support', True))
        chk = ctk.CTkCheckBox(settings_win, text='ボタンホバー時の操作支援（ツールチップ）を有効化', variable=op_var, font=(FONT_NAME, 12))
        chk.pack(pady=10)

        def save_op_setting():
            self.settings['operation_support'] = bool(op_var.get())
            try:
                self.save_settings()
                messagebox.showinfo('設定', '設定を保存しました。', parent=self.master)
                settings_win.destroy()
                self.show_top()
            except Exception as e:
                messagebox.showerror('エラー', f'設定の保存に失敗しました:\n{e}', parent=settings_win)

        btn_frame_ops = ctk.CTkFrame(settings_win, fg_color="transparent")
        btn_frame_ops.pack(pady=15)

        btn_save = ctk.CTkButton(btn_frame_ops, text='設定を保存', font=(FONT_NAME, 12, 'bold'), command=save_op_setting, width=110, fg_color='#bfff80', text_color='black')
        btn_save.pack(side='left', padx=10)

        def rerun_walkthrough():
            self.settings['seen_walkthrough'] = False
            try:
                self.save_settings()
            except Exception:
                pass
            messagebox.showinfo('案内', '次回トップ起動時にチュートリアルを再実行します。', parent=settings_win)
            settings_win.destroy()
            self.show_walkthrough()

        btn_rerun = ctk.CTkButton(btn_frame_ops, text='チュートリアル再表示', font=(FONT_NAME, 12), command=rerun_walkthrough, width=150, fg_color='#ffd480', text_color='black')
        btn_rerun.pack(side='left', padx=10)

    def on_close(self):
        if messagebox.askokcancel('確認', 'アプリを終了しますか？', parent=self.master):
            try:
                self.master.destroy()
            except Exception:
                pass

    def add_tooltip(self, widget, text, delay=300):
        def on_enter(event):
            try:
                if not self.settings.get('operation_support', False):
                    return
            except Exception:
                return
            try:
                widget._tooltip_after = widget.after(delay, lambda: self._show_tooltip(widget, text))
            except Exception:
                pass

        def on_leave(event):
            try:
                if hasattr(widget, '_tooltip_after'):
                    widget.after_cancel(widget._tooltip_after)
                    del widget._tooltip_after
            except Exception:
                pass
            self._hide_tooltip(widget)

        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
        widget.bind('<ButtonPress>', lambda e: self._hide_tooltip(widget))

    def _show_tooltip(self, widget, text):
        try:
            if hasattr(widget, '_tooltip') and widget._tooltip:
                return
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            tw = tk.Toplevel(self.master)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            lbl = tk.Label(tw, text=text, font=(FONT_NAME, 10), bg='#ffffe0', justify='left', relief='solid', bd=1)
            lbl.pack(ipadx=4, ipady=2)
            widget._tooltip = tw
        except Exception:
            pass

    def _hide_tooltip(self, widget):
        try:
            if hasattr(widget, '_tooltip') and widget._tooltip:
                widget._tooltip.destroy()
                widget._tooltip = None
        except Exception:
            pass

    def get_config_path(self, filename='settings.json'):
        if hasattr(sys, '_MEIPASS'):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, filename)

    def load_settings(self):
        path = self.get_config_path()
        self.settings = {}
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    import json
                    self.settings = json.load(f)
        except Exception:
            self.settings = {}
        self.settings.setdefault('operation_support', True)
        self.settings.setdefault('seen_walkthrough', False)

    def save_settings(self):
        path = self.get_config_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                import json
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror('エラー', f'設定の保存に失敗しました:\n{e}', parent=self.master)

    def maybe_show_walkthrough(self):
        try:
            if self.settings.get('operation_support', False) and not self.settings.get('seen_walkthrough', False):
                self.show_walkthrough()
        except Exception:
            pass

    def show_walkthrough(self):
        """モーダル形式のウォークスルーガイド"""
        steps = [
            ('ようこそ！', '幹部専用の出席管理・タイムテーブル作成システムへ案内します。\n左メニューまたはトップ画面から順番に進めていきます。'),
            ('① 出欠をとる', '「出欠をとる」メニューから日付（今日または過去の日付）を選択し、部員の出欠状態をテンポよく入力・記録できます。'),
            ('② 出席率の計算', '「出欠状況の確認」から、ライブ選考の指標となる出席率の「集計開始日」と「集計終了日」を選んで一括計算します。'),
            ('③ バンド登録', '「バンド登録」から応募フォーム等のExcelをインポート。部員名簿との自動名寄せ確認を経て、システムに安全に登録されます。'),
            ('④ バンド選出', '「出演バンド選出」で総演奏時間や募集枠数を入力することで、出席率ベースのオート選出ロジックを実行します。'),
            ('⑤ タイムテーブル作成', '確定した出演バンドデータを元に、別ウィンドウのインタラクティブ・タイムテーブルエディタを立ち上げて最終調整を行います。')
        ]

        win = ctk.CTkToplevel(self.master)
        win.title('システム操作手順案内')
        win.geometry('550x260')
        win.transient(self.master)
        win.grab_set()
        win.attributes("-topmost", True)

        idx_var = tk.IntVar(value=0)
        text_title = ctk.CTkLabel(win, text=steps[0][0], font=ctk.CTkFont(family=FONT_NAME, size=15, weight='bold'))
        text_title.pack(pady=(15, 5))
        text_body = ctk.CTkLabel(win, text=steps[0][1], font=(FONT_NAME, 12), wraplength=480, justify='left')
        text_body.pack(padx=15, pady=5)

        chk_var = tk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(win, text='今後は起動時にこの案内を表示しない', variable=chk_var, font=(FONT_NAME, 11))
        chk.pack(pady=10)

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=10)

        def update_step():
            i = idx_var.get()
            text_title.configure(text=steps[i][0])
            text_body.configure(text=steps[i][1])
            if i == 0:
                btn_back.configure(state='disabled')
            else:
                btn_back.configure(state='normal')
            if i == len(steps)-1:
                btn_next.configure(text='案内完了', fg_color="#00ff62", text_color='black')
            else:
                btn_next.configure(text='次へ', fg_color="#00ff62", text_color='black')

        def on_next():
            i = idx_var.get()
            if i < len(steps)-1:
                idx_var.set(i+1)
                update_step()
            else:
                self.settings['seen_walkthrough'] = bool(chk_var.get())
                self.save_settings()
                win.grab_release()
                win.destroy()

        def on_back():
            i = idx_var.get()
            if i > 0:
                idx_var.set(i-1)
                update_step()

        def on_close():
            if chk_var.get():
                self.settings['seen_walkthrough'] = True
                self.save_settings()
            win.grab_release()
            win.destroy()

        btn_back = ctk.CTkButton(btn_frame, text='戻る', width=90, command=on_back)
        btn_back.pack(side='left', padx=6)
        btn_next = ctk.CTkButton(btn_frame, text='次へ', width=90, command=on_next, fg_color='#00ff62', text_color='black')
        btn_next.pack(side='left', padx=6)
        btn_close = ctk.CTkButton(btn_frame, text='閉じる', width=90, command=on_close, fg_color='#ff0000', text_color='white')
        btn_close.pack(side='left', padx=6)

        update_step()
        win.protocol('WM_DELETE_WINDOW', on_close)

    def toggle_help_mode(self):
        try:
            current = bool(self.settings.get('help_mode', False))
            self.settings['help_mode'] = not current
            self.save_settings()
            self.show_top()
        except Exception:
            pass


if __name__ == '__main__':
    root = ctk.CTk()
    root.geometry('1150x680')
    root.minsize(1050, 600)
    
    # 既存のレガシーフォント設定補正マッピング
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family="Yu Gothic UI", size=11)
    root.option_add("*Font", default_font)
    try:
        tkfont.Font(name=FONT_NAME, family=FONT_NAME, size=11)
    except Exception:
        pass
        
    app = AttendanceApp(root)
    root.mainloop()