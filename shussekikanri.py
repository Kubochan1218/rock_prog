# 2026年6月21日更新 (CustomTkinterモダンデザイン版)

import datetime, openpyxl, re, os, sys, json, difflib, config
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk
import tkinter.font as tkfont
import customtkinter as ctk
import pandas as pd
import band_selection as bs
import attendance_calculation as ac
from top import TopWindow
from views.sidebar import SidebarFrame
from views.attendance_view import AttendanceView
from views.live_view import LiveView

FILE_PATH = config.FILE_PATH
SHEET_NAME = config.SHEET_NAME
FONT_NAME = config.FONT_NAME

# アプリ全体のテーマカラー設定
ctk.set_appearance_mode(config.APP_MODE)  # "System", "Dark", "Light"
ctk.set_default_color_theme(config.APP_COLOR)  # "blue", "green", "dark-blue"

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
        
        # 全体レイアウト：2カラム構成（左：固定サイドメニュー、右：動的画面）
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        
        # 左側：サイドバーフレーム
        self.sidebar = SidebarFrame(self.master, on_menu_select=self.change_screen)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 右側：メインコンテンツ表示用フレーム
        self.main_frame = ctk.CTkFrame(self.master, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")
        
        # 起動時ウォークスルー表示
        try:
            self.maybe_show_walkthrough()
        except Exception:
            pass
                    
        self.change_screen("top")

    def change_screen(self, screen_name):
        """サイドバーのメニュー選択に応じて右側の画面を切り替える"""
        if screen_name == "top":
            self.show_top()
        elif screen_name == "attendance":
            self.show_attendance_date_select()
        elif screen_name == "live":
            self.register_live()
        elif screen_name == "band":
            self.register_band()
        elif screen_name == "timetable":
            self.make_timetable()
        elif screen_name == "settings":
            self.show_settings()

    def clear(self):
        """右側のメインコンテンツエリアのみを消去する"""
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
                    ctk.CTkLabel(self.main_frame, text=f'最後のバンド登録から{delta_days}日経過しています。登録済みバンドを確認しましょう！', font=config.FONT_SUBTITLE, text_color='green').pack(pady=10, anchor="w")
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
        
        btn_attendance = ctk.CTkButton(grid_frame, text='📅 出席をとる・出欠状況確認', height=80, command=self.show_attendance_date_select, fg_color='#bfff80', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_attendance.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        self.add_tooltip(btn_attendance, '出欠を記録する画面を開きます')

        btn_check = ctk.CTkButton(grid_frame, text='📊 出欠状況の確認\n(出席率計算)', height=80, fg_color='#80d4ff', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_check.grid(row=0, column=1, padx=15, pady=15, sticky="ew")
        self.add_tooltip(btn_check, '出席率の計算と出欠状況の確認を行います')

        btn_register = ctk.CTkButton(grid_frame, text='🎤 バンドの追加・編集・削除', height=80, command=self.register_band, fg_color='#ffff00', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_register.grid(row=1, column=0, padx=15, pady=15, sticky="ew")
        self.add_tooltip(btn_register, 'バンドを新規登録・編集・削除します')
        
        btn_select = ctk.CTkButton(grid_frame, text='🔶 出演バンド選出', height=80, command=self.show_select_band, fg_color='#ffd480', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_select.grid(row=1, column=1, padx=15, pady=15, sticky="ew")
        self.add_tooltip(btn_select, '応募バンドから出演バンドを選出します')

        btn_timetable = ctk.CTkButton(grid_frame, text='⏱️ タイムテーブル作成 (別ウィンドウ)', height=80, command=self.make_timetable, fg_color="#d080ff", text_color='black', font=config.FONT_LABEL_BUTTON)
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

    def get_available_dates(self):
        """Excelシートから有効な日付列を取得"""
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

    def show_attendance_date_select(self):
        """出席日付選択画面を表示"""
        self.clear()
        self.attendance_view = AttendanceView(self.main_frame, app=self)
        self.attendance_view.pack(fill='both', expand=True)

    def register_live(self):
        """ライブ情報の登録・編集画面を表示 (JSON保存・時刻選択版)"""
        self.clear()
        self.live_view = LiveView(self.main_frame, app=self)
        self.live_view.pack(fill='both', expand=True)

    def setup_band_selection_tab(self, tabview):
        """バンド選出タブを追加し、UIを構築する"""
        # 1. 新しいタブ「バンド選出」を追加
        tab = tabview.add("バンド選出")
        
        # 全体をスクロール可能にするフレーム（すべてpackで配置）
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # タイトル
        title_lbl = ctk.CTkLabel(scroll_frame, text="🎸 バンド選出 条件設定", font=(FONT_NAME, 18, "bold"))
        title_lbl.pack(pady=15, anchor="w", padx=10)
        
        # 各行のラベル幅を「240ピクセル」に固定し、入力欄の左端を綺麗に揃える
        LBL_WIDTH = 240
        
        # --- 1. 出席率計算 開始日 ---
        row_start = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row_start.pack(fill="x", pady=6, padx=10)
        lbl_start = ctk.CTkLabel(row_start, text="⏰ 出席率計算 開始日 (YYYYMMDD):", font=(FONT_NAME, 15), width=LBL_WIDTH, anchor="w")
        lbl_start.pack(side="left")
        self.entry_start_date = ctk.CTkEntry(row_start, width=180, font=(FONT_NAME, 14))
        self.entry_start_date.pack(side="left", padx=5)
        
        # --- 2. 出席率計算 終了日 ---
        row_end = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row_end.pack(fill="x", pady=6, padx=10)
        lbl_end = ctk.CTkLabel(row_end, text="⏰ 出席率計算 終了日 (YYYYMMDD):", font=(FONT_NAME, 15), width=LBL_WIDTH, anchor="w")
        lbl_end.pack(side="left")
        self.entry_end_date = ctk.CTkEntry(row_end, width=180, font=(FONT_NAME, 14))
        self.entry_end_date.pack(side="left", padx=5)
        
        # --- 3. 募集バンド数 ---
        row_bands = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row_bands.pack(fill="x", pady=6, padx=10)
        lbl_bands = ctk.CTkLabel(row_bands, text="👥 募集バンド数 (空欄で上限なし):", font=(FONT_NAME, 15), width=LBL_WIDTH, anchor="w")
        lbl_bands.pack(side="left")
        self.entry_max_bands = ctk.CTkEntry(row_bands, width=180, font=(FONT_NAME, 14))
        self.entry_max_bands.pack(side="left", padx=5)
        
        # --- 4. ライブの総時間 ---
        row_time = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row_time.pack(fill="x", pady=6, padx=10)
        lbl_time = ctk.CTkLabel(row_time, text="⏳ ライブの総時間 (分・空欄で上限なし):", font=(FONT_NAME, 15), width=LBL_WIDTH, anchor="w")
        lbl_time.pack(side="left")
        self.entry_total_time = ctk.CTkEntry(row_time, width=180, font=(FONT_NAME, 14))
        self.entry_total_time.pack(side="left", padx=5)
        
        # --- 5. リハーサル時間 ---
        row_reh = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row_reh.pack(fill="x", pady=6, padx=10)
        lbl_reh = ctk.CTkLabel(row_reh, text="🔄 リハーサル時間 (分):", font=(FONT_NAME, 15), width=LBL_WIDTH, anchor="w")
        lbl_reh.pack(side="left")
        self.entry_rehearsal_time = ctk.CTkEntry(row_reh, width=180, font=(FONT_NAME, 14))
        self.entry_rehearsal_time.insert(0, "20")  # デフォルト値 20分
        self.entry_rehearsal_time.pack(side="left", padx=5)
        
        # --- 6. 選出ボタン ---
        btn_select = ctk.CTkButton(
            scroll_frame, 
            text="✨ この条件でバンドを選出する", 
            font=(FONT_NAME, 16, "bold"), 
            fg_color="#00ff62", 
            text_color="black", 
            height=40,
            command=self.execute_band_selection
        )
        btn_select.pack(pady=20, padx=10, fill="x")
        
        # --- 7. 結果表示エリア ---
        result_lbl = ctk.CTkLabel(scroll_frame, text="📋 選出結果出力", font=(FONT_NAME, 16, "bold"))
        result_lbl.pack(pady=5, anchor="w", padx=10)
        
        self.result_textbox = ctk.CTkTextbox(scroll_frame, height=250, font=(FONT_NAME, 14))
        self.result_textbox.pack(fill="both", expand=True, pady=5, padx=10)

    def execute_band_selection(self):
        """UIの入力値を解析し、bs.select_bandsを実行する"""
        start_date = self.entry_start_date.get().strip()
        end_date = self.entry_end_date.get().strip()
        
        # 期間は必須バリデーション
        if not start_date or not end_date:
            messagebox.showwarning("入力エラー", "出席率計算の期間（開始日・終了日）を入力してください。")
            return
            
        # 募集バンド数（未入力時は上限なし -> None）
        max_bands_val = self.entry_max_bands.get().strip()
        max_bands = int(max_bands_val) if max_bands_val else None
        
        # ライブ総時間（未入力時は上限なし -> None）
        total_time_val = self.entry_total_time.get().strip()
        total_time = int(total_time_val) if total_time_val else None
        
        # リハーサル時間（未入力時はデフォルト20分）
        rehearsal_val = self.entry_rehearsal_time.get().strip()
        rehearsal_time = int(rehearsal_val) if rehearsal_val else 20
        
        # 画面のテキストエリアをリセット
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("end", "⏳ バンド選出アルゴリズムを実行中...\n\n")
        
        try:
            # インポートされている band_selection (bs) の select_bands メソッドを呼び出し
            if hasattr(bs, 'select_bands'):
                results = bs.select_bands(
                    start_date=start_date,
                    end_date=end_date,
                    max_bands=max_bands,
                    total_time=total_time,
                    rehearsal_time=rehearsal_time
                )
                
                self.result_textbox.delete("1.0", "end")
                if results:
                    # 戻り値がリスト形式で返ってきた場合を想定した綺麗目の出力整形
                    if isinstance(results, list):
                        self.result_textbox.insert("end", f"🎉 条件に合致する {len(results)} つのバンドが選出されました：\n\n")
                        for idx, band in enumerate(results, 1):
                            self.result_textbox.insert("end", f"【{idx}】 {band}\n")
                    else:
                        self.result_textbox.insert("end", str(results))
                else:
                    self.result_textbox.insert("end", "❌ 条件に一致する、または選出枠に入るバンドが見つかりませんでした。")
            else:
                # band_selection.py 側に該当メソッドがまだ準備されていない場合のデバッグ用表示
                self.result_textbox.insert("end", "⚠️ 'band_selection' モジュール内に 'select_bands' メソッドが見つかりません。\n")
                self.result_textbox.insert("end", f"【UIから取得したパラメータ】\n")
                self.result_textbox.insert("end", f"・計算期間: {start_date} ～ {end_date}\n")
                self.result_textbox.insert("end", f"・募集バンド数: {max_bands if max_bands else '上限なし'}\n")
                self.result_textbox.insert("end", f"・ライブ総時間: {total_time if total_time else '上限なし'} 分\n")
                self.result_textbox.insert("end", f"・リハーサル時間: {rehearsal_time} 分\n")
                
        except Exception as e:
            self.result_textbox.delete("1.0", "end")
            messagebox.showerror("実行エラー", f"選出処理中にエラーが発生しました:\n{str(e)}")

    def register_band(self):
        """バンド登録画面を表示 (タブ切り替え・一括一覧表示＆ライブ名紐付け版)"""
        # ライブ情報の読み込み
        LIVE_JSON_PATH = self.get_config_path('live_info.json')
        existing_lives = {}
        if os.path.exists(LIVE_JSON_PATH):
            try:
                with open(LIVE_JSON_PATH, 'r', encoding='utf-8') as f:
                    existing_lives = json.load(f)
            except Exception:
                pass

        if not existing_lives:
            messagebox.showerror('エラー', '登録済みのライブ情報がありません。\n先に「ライブ情報の登録・編集」からライブを作成してください。')
            return

        self.clear()

        # 上部に切り替え用のタブビューを作成
        tabview = ctk.CTkTabview(self.main_frame)
        tabview.pack(fill="both", expand=True, padx=0, pady=0)

        tab_import = tabview.add("📥 新規一括インポート")
        tab_manage = tabview.add("📝 登録済みバンドの管理")
        self.setup_band_selection_tab(tabview)

        # 【タブ1】 新規一括インポート 処理群
        
        def show_setup_screen(parent_tab):
            """STEP 1: ライブの選択とExcelファイルの読み込み画面"""
            for widget in parent_tab.winfo_children():
                widget.destroy()

            ctk.CTkLabel(parent_tab, text='🎤 バンド応募データの一括インポート', font=config.FONT_TITLE).pack(pady=15, anchor="w")

            form_frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
            form_frame.pack(pady=10, fill='x', padx=10)

            # 1. ライブ名選択
            ctk.CTkLabel(form_frame, text='対象のライブを選択:', font=config.FONT_LABEL_BUTTON).pack(anchor='w', pady=5)
            live_combo = ctk.CTkComboBox(form_frame, values=list(existing_lives.keys()), width=300, font=(FONT_NAME, 16))
            live_combo.pack(anchor='w', pady=(0, 15))

            # 2. ファイル選択
            ctk.CTkLabel(form_frame, text='応募フォームのExcelファイル:', font=config.FONT_LABEL_BUTTON).pack(anchor='w', pady=5)
            file_path_var = tk.StringVar()
            
            file_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            file_frame.pack(anchor='w', fill='x')
            
            file_entry = ctk.CTkEntry(file_frame, textvariable=file_path_var, width=350, font=(FONT_NAME, 16), state='disabled')
            file_entry.pack(side='left', padx=(0, 10))

            def select_file():
                f_path = filedialog.askopenfilename(title='応募バンド情報のExcelを選択', filetypes=[('Excelファイル', '*.xlsx;*.xls')])
                if f_path:
                    file_path_var.set(f_path)
            
            btn_file = ctk.CTkButton(file_frame, text='ファイルを選択', width=120, fg_color='#80d4ff', text_color='black', font=(FONT_NAME, 16), command=select_file)
            btn_file.pack(side='left')

            # 3. 実行ボタン
            def process_excel():
                target_live = live_combo.get()
                target_file = file_path_var.get()
                if not target_live or not target_file:
                    messagebox.showerror('エラー', 'ライブとファイルの両方を選択してください。')
                    return
                parse_and_match(target_live, target_file, parent_tab)

            btn_next = ctk.CTkButton(parent_tab, text='🚀 データの読み込みを開始', font=config.FONT_LABEL_BUTTON, fg_color='#bfff80', text_color='black', width=300, height=45, command=process_excel)
            btn_next.pack(pady=40)
            
            # キャンセルボタン（左下に配置）
            btn_top = ctk.CTkButton(parent_tab, text='キャンセル', width=120, fg_color='#ff0000', text_color='white', font=(FONT_NAME, 16), command=self.show_top)
            btn_top.place(relx=0.0, rely=1.0, anchor='sw', x=25, y=-21)

        def parse_and_match(live_name, file_path, parent_tab):
            """STEP 2: Excelのパースと自動名寄せ処理"""
            live_data = existing_lives[live_name]
            try:
                df_all = pd.read_excel(file_path)
                df_band = df_all.iloc[:, 2:]
                
                df_roster = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=1)
                roster_names = list(df_roster['氏名'].dropna().astype(str))
            except Exception as e:
                messagebox.showerror('エラー', f'ファイルの読み込みに失敗しました:\n{e}')
                return

            parsed_bands = []

            for idx, row in df_band.iterrows():
                band_name = str(row.iloc[0])
                play_time = str(row.iloc[1]) if len(row) > 1 else ''
                members_raw = str(row.iloc[2]) if len(row) > 2 else ''
                dates_raw = str(row.iloc[3]) if len(row) > 3 else ''

                n_val = o_val = p_val = q_val = ''
                opt_cols1 = [i for i, col in enumerate(row.index) if '[opt1]' in str(col)]
                if opt_cols1: n_val = str(row.iloc[opt_cols1[0]])
                opt_cols2 = [i for i, col in enumerate(row.index) if '[opt2]' in str(col)]
                if opt_cols2: o_val = str(row.iloc[opt_cols2[0]])
                opt_cols3 = [i for i, col in enumerate(row.index) if '[opt3]' in str(col)]
                if opt_cols3: p_val = str(row.iloc[opt_cols3[0]])
                
                for i, col in enumerate(row.index[4:], 4):
                    if not any(f'[opt{n}]' in str(col) for n in range(1, 4)):
                        q_val = str(row.iloc[i])
                        break

                members_str = re.sub(r'[ \u3000]', '', members_raw)
                member_lines = [line for line in members_str.splitlines() if line.strip()]
                matched_members = []
                
                for mline in member_lines:
                    best_match, best_score = None, 0
                    for name in roster_names:
                        score = difflib.SequenceMatcher(None, mline, name).ratio()
                        if score > best_score:
                            best_score, best_match = score, name
                    if best_score >= 0.3:
                        matched_members.append(best_match)

                parsed_bands.append({
                    'band_name': band_name,
                    'members_raw': members_raw,
                    'matched_members': matched_members,
                    'play_time': play_time,
                    'dates_raw': dates_raw,
                    'options': [n_val, o_val, p_val, q_val]
                })

            show_list_screen(parsed_bands, live_name, live_data, roster_names, parent_tab)

        def convert_perform_dates(perform_date_str, live_data):
            """希望日[1]などを実際の日付に変換（[0]なら全日程）"""
            schedules = {str(s['day']): s['date'] for s in live_data.get('schedules', [])}
            tokens = re.findall(r'\[\d+\]', str(perform_date_str))
            if not tokens:
                return ''
            
            out_dates = []
            for tok in tokens:
                num = tok.strip('[]')
                if num == '0':
                    out_dates.extend([date for date in schedules.values() if date])
                elif num in schedules:
                    out_dates.append(schedules[num])
            
            return ';'.join(dict.fromkeys(out_dates))

        def show_list_screen(parsed_bands, live_name, live_data, roster_names, parent_tab):
            """STEP 3: 読み込み結果の一覧表示と手動修正画面"""
            for widget in parent_tab.winfo_children():
                widget.destroy()
            
            header_text = f'📋 バンド登録内容確認 - 対象: {live_name} (全{len(parsed_bands)}バンド)'
            ctk.CTkLabel(parent_tab, text=header_text, font=config.FONT_TITLE).pack(pady=(15, 5), anchor="w")
            ctk.CTkLabel(parent_tab, text='バンドメンバー自動判定の結果です。漏れや間違いがある場合は「修正」ボタンから手動で追加してください。', font=config.FONT_SUBTITLE, text_color='gray').pack(anchor="w", pady=(0, 10))

            # 下部固定ボタンと被らないよう、スクロール領域の下マージン(pady)を多めに確保
            scroll_frame = ctk.CTkScrollableFrame(parent_tab)
            scroll_frame.pack(fill='both', expand=True, padx=5, pady=(5, 65))

            # バンド一覧の描画
            for b_data in parsed_bands:
                row_frame = ctk.CTkFrame(scroll_frame, fg_color=("gray90", "gray15"))
                row_frame.pack(fill='x', pady=4, padx=5, ipady=5)

                # バンド名 (縦並びに合わせて上揃え anchor='n')
                name_lbl = ctk.CTkLabel(row_frame, text=b_data['band_name'], font=(FONT_NAME, 14, 'bold'), width=360, anchor='w')
                name_lbl.pack(side='left', padx=10, anchor='n', pady=6, expand=False)

                # メンバー表示（一人一行で縦に並べる: \n で結合し justify='left'）
                members_txt = "\n".join(b_data['matched_members']) if b_data['matched_members'] else "（メンバーなし・要確認）"
                mem_lbl = ctk.CTkLabel(row_frame, text=members_txt, font=(FONT_NAME, 14), anchor='w', justify='left')
                mem_lbl.pack(side='left', padx=10, fill='x', expand=True, anchor='n', pady=6)

                # 修正ボタン (上揃え anchor='n')
                def open_edit_popup(current_band=b_data, update_label=mem_lbl):
                    popup = ctk.CTkToplevel(self.master)
                    popup.title(f"メンバー手動修正: {current_band['band_name']}")
                    popup.resizable(False, False)
                    popup.geometry("600x480")
                    popup.attributes("-topmost", True)
                    popup.grab_set()

                    ctk.CTkLabel(popup, text='元の応募テキスト:', font=config.FONT_LABEL_BUTTON).pack(pady=(10, 0), anchor='w', padx=15)
                    ctk.CTkLabel(popup, text=current_band['members_raw'], font=(FONT_NAME, 14), justify='left', fg_color=("gray85", "gray25"), corner_radius=5).pack(fill='x', padx=15, pady=5, ipady=5)

                    ctk.CTkLabel(popup, text='メンバー設定 (最大10名):', font=config.FONT_LABEL_BUTTON).pack(pady=(10, 0), anchor='w', padx=15)

                    edit_scroll = ctk.CTkScrollableFrame(popup, height=180)
                    edit_scroll.pack(fill='both', expand=True, padx=15, pady=5)

                    combos = []
                    for i in range(10):
                        cb = ctk.CTkComboBox(edit_scroll, values=[''] + roster_names, width=200, font=(FONT_NAME, 16))
                        cb.pack(pady=4, anchor='w', padx=10)
                        if i < len(current_band['matched_members']):
                            cb.set(current_band['matched_members'][i])
                        else:
                            cb.set('')
                        combos.append(cb)

                    def save_popup():
                        new_members = []
                        for cb in combos:
                            val = cb.get()
                            if val and val not in new_members:
                                new_members.append(val)
                        
                        current_band['matched_members'] = new_members
                        # 反映後の文字も縦に並ぶよう修正
                        new_text = "\n".join(new_members) if new_members else "（メンバーなし・要確認）"
                        update_label.configure(text=new_text)
                        
                        popup.grab_release()
                        popup.destroy()

                    btn_save_pop = ctk.CTkButton(popup, text='決定して閉じる', font=config.FONT_LABEL_BUTTON, fg_color='#bfff80', text_color='black', command=save_popup)
                    btn_save_pop.pack(pady=15)

                # クロージャ対策を施したインポート除外（削除）コマンドの生成
                def make_import_delete_cmd(target_data=b_data):
                    return lambda: delete_import_band(target_data)

                def delete_import_band(target_data):
                    if messagebox.askyesno('確認', f'このバンド「{target_data["band_name"]}」をインポート対象から除外しますか？'):
                        parsed_bands.remove(target_data) # リストから削除
                        # 件数表示も含めて画面全体をリフレッシュ（再描画）
                        show_list_screen(parsed_bands, live_name, live_data, roster_names, parent_tab)

                # 削除ボタンをコンテナの右側に配置
                btn_del = ctk.CTkButton(row_frame, text='× 削除', width=70, font=(FONT_NAME, 16), fg_color='#ff8080', text_color='black', command=make_import_delete_cmd())
                btn_del.pack(side='right', padx=10, anchor='n', pady=6)

                btn_edit = ctk.CTkButton(row_frame, text='✏ 修正', width=70, font=(FONT_NAME, 16), fg_color='#ffd480', text_color='black', command=open_edit_popup)
                btn_edit.pack(side='right', padx=5, anchor='n', pady=6)

            # Excelへの一括書き込み処理
            def register_all_to_excel():
                try:
                    wb = openpyxl.load_workbook(FILE_PATH)
                    sheet_name = '登録済みバンド'
                    if sheet_name not in wb.sheetnames:
                        ws = wb.create_sheet(sheet_name)
                    else:
                        ws = wb[sheet_name]

                    row_idx = 1
                    while ws.cell(row=row_idx, column=1).value is not None:
                        row_idx += 1
                    
                    for b_data in parsed_bands:
                        mem_list = b_data['matched_members'].copy()
                        while len(mem_list) < 10:
                            mem_list.append('')
                            
                        mapped_dates = convert_perform_dates(b_data['dates_raw'], live_data)
                        
                        band_row = [b_data['band_name']]
                        band_row.extend(mem_list)
                        band_row.append(b_data['play_time'])
                        band_row.append(mapped_dates)
                        band_row.extend(b_data['options'])
                        
                        while len(band_row) < 17:
                            band_row.append('')
                            
                        band_row.append(0)           # 18列目: 選出ステータス
                        band_row.append(live_name)   # 19列目: 対象ライブ名

                        for col, val in enumerate(band_row, 1):
                            ws.cell(row=row_idx, column=col).value = val
                        
                        row_idx += 1

                    wb.save(FILE_PATH)
                    try:
                        self.settings['last_startup'] = __import__('datetime').date.today().isoformat()
                        self.save_settings()
                    except Exception:
                        pass            
                    messagebox.showinfo('一括登録完了', f'計 {len(parsed_bands)} バンドを「{live_name}」として登録しました。')
                    self.show_top()
                except Exception as e:
                    messagebox.showerror('保存エラー', f'Excel保存に失敗しました:\n{e}')

            # 登録実行ボタン（右下に配置）
            btn_register = ctk.CTkButton(parent_tab, text='✨ この内容で全て登録', font=config.FONT_LABEL_BUTTON, fg_color='#00ff62', text_color='black', height=40, command=register_all_to_excel)
            btn_register.place(relx=1.0, rely=1.0, anchor='se', x=-25, y=-21)

            # キャンセルボタン（左下に配置）
            btn_cancel = ctk.CTkButton(parent_tab, text='キャンセル', font=(FONT_NAME, 16), fg_color='#ff0000', text_color='white', width=120, command=self.show_top)
            btn_cancel.place(relx=0.0, rely=1.0, anchor='sw', x=25, y=-21)

        # 【タブ2】 登録済みバンドの管理 処理群
        
        def show_management_screen(parent_tab):
            """STEP 1: 登録済みバンドの抽出と編集・削除画面"""
            for widget in parent_tab.winfo_children():
                widget.destroy()

            ctk.CTkLabel(parent_tab, text='📝 登録済みバンドの管理（編集・削除）', font=config.FONT_TITLE).pack(pady=15, anchor="w")

            filter_frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
            filter_frame.pack(pady=5, fill='x', padx=10)

            ctk.CTkLabel(filter_frame, text='表示するライブを選択:', font=config.FONT_LABEL_BUTTON).pack(side='left', padx=(0, 10))
            live_selector = ctk.CTkComboBox(filter_frame, values=list(existing_lives.keys()), width=250, font=(FONT_NAME, 16))
            live_selector.pack(side='left', padx=5)

            # リスト描画用のコンテナフレーム
            list_container = ctk.CTkFrame(parent_tab, fg_color="transparent")
            list_container.pack(fill='both', expand=True, padx=5, pady=(10, 65))

            def refresh_managed_bands(*args):
                """選択されたライブに紐づくバンドを再読み込みして描画"""
                for widget in list_container.winfo_children():
                    widget.destroy()

                selected_live = live_selector.get()
                if not selected_live:
                    return

                try:
                    wb = openpyxl.load_workbook(FILE_PATH, data_only=True)
                    if '登録済みバンド' not in wb.sheetnames:
                        ctk.CTkLabel(list_container, text='登録されているバンドはありません。', font=(FONT_NAME, 16)).pack(pady=20)
                        return
                    ws = wb['登録済みバンド']
                except Exception as e:
                    ctk.CTkLabel(list_container, text=f'Excelの読み込みに失敗しました: {e}', font=(FONT_NAME, 16), text_color='red').pack(pady=20)
                    return

                managed_scroll = ctk.CTkScrollableFrame(list_container)
                managed_scroll.pack(fill='both', expand=True, padx=0, pady=0)

                # メンバー再編集用の名簿データ取得
                try:
                    df_roster = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=1)
                    roster_names = list(df_roster['氏名'].dropna().astype(str))
                except Exception:
                    roster_names = []

                has_bands = False
                
                # Excelの全行を走査して対象ライブのデータを抽出
                for r_idx in range(1, ws.max_row + 1):
                    b_name = ws.cell(row=r_idx, column=1).value
                    l_name = ws.cell(row=r_idx, column=19).value # 19列目がライブ名

                    if b_name is None or l_name != selected_live:
                        continue

                    has_bands = True
                    
                    # メンバー10人分の枠から登録名を取得
                    m_list = []
                    for c_idx in range(2, 12):
                        val = ws.cell(row=r_idx, column=c_idx).value
                        if val:
                            m_list.append(str(val))

                    b_frame = ctk.CTkFrame(managed_scroll, fg_color=("gray90", "gray15"))
                    b_frame.pack(fill='x', pady=4, padx=5, ipady=5)

                    # バンド名
                    ctk.CTkLabel(b_frame, text=str(b_name), font=(FONT_NAME, 14, 'bold'), width=360, anchor='w').pack(side='left', padx=10, anchor='n', pady=6, expand=False)

                    # メンバー表示（一人一行で縦に並べる）
                    m_txt = "\n".join(m_list) if m_list else "（メンバーなし）"
                    ctk.CTkLabel(b_frame, text=m_txt, font=(FONT_NAME, 14), anchor='w', justify='left').pack(side='left', padx=10, fill='x', expand=True, anchor='n', pady=6)

                    # クロージャ対策を施した削除/編集コマンドの生成
                    def make_delete_cmd(target_row=r_idx, name=b_name):
                        return lambda: delete_band(target_row, name)

                    def make_edit_cmd(target_row=r_idx, name=b_name, current_m=m_list):
                        return lambda: open_manage_edit_popup(target_row, name, current_m)

                    def delete_band(target_row, name):
                        if messagebox.askyesno('確認', f'本当にバンド「{name}」を削除しますか？'):
                            try:
                                edit_wb = openpyxl.load_workbook(FILE_PATH)
                                edit_ws = edit_wb['登録済みバンド']
                                edit_ws.delete_rows(target_row) # 該当行を丸ごと削除
                                edit_wb.save(FILE_PATH)
                                messagebox.showinfo('成功', f'「{name}」を削除しました。')
                                refresh_managed_bands() # 画面リフレッシュ
                            except Exception as e:
                                messagebox.showerror('エラー', f'削除に失敗しました: {e}')

                    def open_manage_edit_popup(target_row, name, current_m):
                        popup = ctk.CTkToplevel(self.master)
                        popup.title(f"バンド編集: {name}")
                        popup.geometry("500x520")
                        popup.attributes("-topmost", True)
                        popup.grab_set()

                        ctk.CTkLabel(popup, text=f'🎤 バンド名: {name}', font=config.FONT_LABEL_BUTTON).pack(pady=10, anchor='w', padx=15)
                        
                        try:
                            p_time = ws.cell(row=target_row, column=12).value or ''
                            p_date = ws.cell(row=target_row, column=13).value or ''
                        except Exception:
                            p_time = p_date = ''

                        ctk.CTkLabel(popup, text='演奏時間:', font=(FONT_NAME, 14)).pack(anchor='w', padx=15)
                        time_entry = ctk.CTkEntry(popup, font=(FONT_NAME, 16), width=200)
                        time_entry.pack(anchor='w', padx=15, pady=2)
                        time_entry.insert(0, str(p_time))

                        ctk.CTkLabel(popup, text='出演日:', font=(FONT_NAME, 14)).pack(anchor='w', padx=15)
                        date_entry = ctk.CTkEntry(popup, font=(FONT_NAME, 16), width=200)
                        date_entry.pack(anchor='w', padx=15, pady=2)
                        date_entry.insert(0, str(p_date))

                        ctk.CTkLabel(popup, text='メンバー設定 (最大10名):', font=config.FONT_LABEL_BUTTON).pack(pady=(10, 0), anchor='w', padx=15)
                        
                        edit_scroll = ctk.CTkScrollableFrame(popup, height=180)
                        edit_scroll.pack(fill='both', expand=True, padx=15, pady=5)

                        combos = []
                        for i in range(10):
                            cb = ctk.CTkComboBox(edit_scroll, values=[''] + roster_names, width=200, font=(FONT_NAME, 16))
                            cb.pack(pady=4, anchor='w', padx=10)
                            if i < len(current_m):
                                cb.set(current_m[i])
                            else:
                                cb.set('')
                            combos.append(cb)

                        def save_managed_edit():
                            new_members = []
                            for cb in combos:
                                val = cb.get()
                                if val and val not in new_members:
                                    new_members.append(val)
                            
                            while len(new_members) < 10:
                                new_members.append('')

                            try:
                                edit_wb = openpyxl.load_workbook(FILE_PATH)
                                edit_ws = edit_wb['登録済みバンド']
                                
                                # メンバー上書き (2~11列目)
                                for idx, m_name in enumerate(new_members, 2):
                                    edit_ws.cell(row=target_row, column=idx).value = m_name
                                
                                # 演奏時間(12列目)・出演日(13列目)の上書き
                                edit_ws.cell(row=target_row, column=12).value = time_entry.get()
                                edit_ws.cell(row=target_row, column=13).value = date_entry.get()

                                edit_wb.save(FILE_PATH)
                                messagebox.showinfo('成功', 'バンド情報を更新しました。')
                                popup.grab_release()
                                popup.destroy()
                                refresh_managed_bands() # 画面リフレッシュ
                            except Exception as e:
                                messagebox.showerror('エラー', f'更新に失敗しました: {e}')

                        btn_save_pop = ctk.CTkButton(popup, text='💾 変更を保存', font=config.FONT_LABEL_BUTTON, fg_color='#bfff80', text_color='black', command=save_managed_edit)
                        btn_save_pop.pack(pady=15)

                    # 右端配置ボタン（削除と編集）
                    btn_del = ctk.CTkButton(b_frame, text='× 削除', width=70, font=(FONT_NAME, 16), fg_color='#ff8080', text_color='black', command=make_delete_cmd())
                    btn_del.pack(side='right', padx=10, anchor='n', pady=6)

                    btn_edt = ctk.CTkButton(b_frame, text='✏️ 編集', width=70, font=(FONT_NAME, 16), fg_color='#ffd480', text_color='black', command=make_edit_cmd())
                    btn_edt.pack(side='right', padx=5, anchor='n', pady=6)

                if not has_bands:
                    ctk.CTkLabel(list_container, text='選択されたライブに登録されているバンドはありません。', font=(FONT_NAME, 16)).pack(pady=20)

            live_selector.configure(command=refresh_managed_bands)
            if list(existing_lives.keys()):
                live_selector.set(list(existing_lives.keys())[0])
                refresh_managed_bands()

            # キャンセルボタン（左下に配置）
            btn_manage_back = ctk.CTkButton(parent_tab, text='キャンセル', width=120, fg_color='#ff0000', text_color='white', font=(FONT_NAME, 16), command=self.show_top)
            btn_manage_back.place(relx=0.0, rely=1.0, anchor='sw', x=25, y=-21)


        # 各タブの初期描画を実行
        show_setup_screen(tab_import)
        show_management_screen(tab_manage)

    def _convert_perform_dates(self, perform_date_str):
        """希望日[1]などを実際の日付に変換（[0]なら全日程）"""
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

    def clear_registered_bands(self):
        """登録済みバンド情報をすべて削除（現在未使用）"""
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
        
        btn_calc = ctk.CTkButton(frm, text='<期間計算へ>', font=(FONT_NAME, 11), fg_color='#80d4ff', text_color='black', width=90)
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
        ctk.CTkLabel(self.main_frame, text='システム環境設定', font=config.FONT_TITLE).pack(pady=20, anchor="w")
        
        btn_excel = ctk.CTkButton(self.main_frame, text='📁 Excelデータソースの設定', font=(FONT_NAME, 16), text_color='white', width=220, height=42, command=self.show_excel_file_settings, fg_color="#00bb44")
        btn_excel.pack(pady=10, anchor="w")
        
        btn_op = ctk.CTkButton(self.main_frame, text='💡 操作支援・ガイド設定', font=(FONT_NAME, 16), text_color='white', width=220, height=42, command=self.show_operation_support_settings, fg_color="#35cbfd")
        btn_op.pack(pady=10, anchor="w")
        
        btn_top = ctk.CTkButton(self.main_frame, text='トップに戻る', width=120, fg_color='#ff0000', text_color='white', font=(FONT_NAME, 16), command=self.show_top)
        btn_top.place(relx=0.0, rely=1.0, anchor='sw', x=25, y=-21)

    def show_excel_file_settings(self):
        settings_win = ctk.CTkToplevel(self.master)
        settings_win.title('Excelファイルの設定')
        settings_win.geometry('420x220')
        settings_win.attributes("-topmost", True)
        
        ctk.CTkLabel(settings_win, text='Excelターゲットパス設定', font=ctk.CTkFont(family=FONT_NAME, size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(settings_win, text='※アプリと同じディレクトリ内の相対パス、またはフルパスを指定', font=config.FONT_SUBTITLE, text_color='gray').pack(pady=2)
        
        file_var = tk.StringVar(value=globals().get('FILE_PATH', 'attend_data.xlsx'))
        entry = ctk.CTkEntry(settings_win, textvariable=file_var, font=(FONT_NAME, 16), width=320)
        entry.pack(pady=10)

        def save_file_path():
            new_path = file_var.get().strip()
            if new_path:
                globals()['FILE_PATH'] = new_path
                messagebox.showinfo('設定', f'ターゲットファイルを「{new_path}」に変更しました。', parent=settings_win)
                settings_win.destroy()
            else:
                messagebox.showerror('エラー', '有効なファイル名を入力してください。', parent=settings_win)

        btn_save = ctk.CTkButton(settings_win, text='適用して保存', font=config.FONT_LABEL_BUTTON, command=save_file_path, width=120, fg_color='#bfff80', text_color='black')
        btn_save.pack(pady=15)

    def show_operation_support_settings(self):
        settings_win = ctk.CTkToplevel(self.master)
        settings_win.title('操作支援の設定')
        settings_win.geometry('450x220')
        settings_win.attributes("-topmost", True)
        
        ctk.CTkLabel(settings_win, text='操作支援・ナビゲーションシステム', font=ctk.CTkFont(family=FONT_NAME, size=16, weight='bold')).pack(pady=12)
        
        op_var = tk.BooleanVar(value=self.settings.get('operation_support', True))
        chk = ctk.CTkCheckBox(settings_win, text='ボタンホバー時の操作支援（ツールチップ）を有効化', variable=op_var, font=(FONT_NAME, 16))
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

        btn_save = ctk.CTkButton(btn_frame_ops, text='設定を保存', font=config.FONT_LABEL_BUTTON, command=save_op_setting, width=110, fg_color='#bfff80', text_color='black')
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

        btn_rerun = ctk.CTkButton(btn_frame_ops, text='チュートリアル再表示', font=(FONT_NAME, 16), command=rerun_walkthrough, width=150, fg_color='#ffd480', text_color='black')
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