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
from views.band_view import BandView

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
                    ('② 出席率の計算', '開く', self.show_attendance_date_select, '#80d4ff'),
                    ('③ バンド登録', '開く', self.register_band, '#ffff00'),
                    ('④ バンド選出', '開く', self.register_band, '#ffd480'),
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

        btn_check = ctk.CTkButton(grid_frame, text='📊 出欠状況の確認\n(出席率計算)', height=80, fg_color='#80d4ff', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_check.grid(row=0, column=1, padx=15, pady=15, sticky="ew")

        btn_register = ctk.CTkButton(grid_frame, text='🎤 バンドの追加・編集・削除', height=80, command=self.register_band, fg_color='#ffff00', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_register.grid(row=1, column=0, padx=15, pady=15, sticky="ew")
        
        btn_select = ctk.CTkButton(grid_frame, text='🔶 出演バンド選出', height=80, command=self.register_band, fg_color='#ffd480', text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_select.grid(row=1, column=1, padx=15, pady=15, sticky="ew")

        btn_timetable = ctk.CTkButton(grid_frame, text='⏱️ タイムテーブル作成 (別ウィンドウ)', height=80, command=self.make_timetable, fg_color="#d080ff", text_color='black', font=config.FONT_LABEL_BUTTON)
        btn_timetable.grid(row=2, column=0, columnspan=2, padx=15, pady=15, sticky="ew")
        
        # ヘルプモード切り替えボタン
        try:
            if self.settings.get('operation_support', False):
                btn_help_mode = ctk.CTkButton(self.main_frame, text='❓ ヘルプモード開始', width=150, height=35, command=self.toggle_help_mode, fg_color="#4375ff", font=(FONT_NAME, 13, 'bold'))
                btn_help_mode.place(relx=0.0, rely=1.0, anchor='sw', x=20, y=-20)
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

    def register_band(self):
        """バンド登録画面を表示 (タブ切り替え・一括一覧表示＆ライブ名紐付け版)"""
        self.clear()
        self.band_view = BandView(self.main_frame, app=self)
        self.band_view.pack(fill='both', expand=True)

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