# 2026年7月5日更新 (CustomTkinterモダンデザイン版)

import datetime, os, sys
import tkinter as tk
from tkinter import messagebox, filedialog
import tkinter.font as tkfont
import customtkinter as ctk
import pandas as pd

import config
from views.sidebar import SidebarFrame
from views.top_view import MainView
from views.attendance_view import AttendanceView
from views.live_view import LiveView
from views.band_view import BandView
from views.timetable_view import TimetableView

FILE_PATH = config.FILE_PATH
SHEET_NAME = config.SHEET_NAME
FONT_NAME = config.FONT_NAME

# アプリ全体のテーマカラー設定
ctk.set_appearance_mode(config.APP_MODE)  # デフォルトは"System"
ctk.set_default_color_theme(config.APP_COLOR)  # "blue", "green", "dark-blue"

class AttendanceApp:
    def __init__(self, master):
        self.master = master
        master.title('ロック部 出席管理')
        master.geometry('1150x680')
        master.minsize(1150, 680)
        
        # ウィンドウの×ボタンに確認ダイアログを設定
        try:
            self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        except Exception:
            pass
            
        # 設定読み込み（操作支援など）
        self.load_settings()
        appearance_mode = self.settings.get('appearance_mode', config.APP_MODE)
        try:
            ctk.set_appearance_mode(appearance_mode)
        except Exception:
            ctk.set_appearance_mode(config.APP_MODE)

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
        self.top_view = MainView(self.main_frame, app=self)

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
        """タイムテーブル作成画面を表示"""
        self.clear()
        self.timetable_view = TimetableView(self.main_frame, app=self)
        self.timetable_view.pack(fill='both', expand=True)

    def show_settings(self):
        """システム設定画面を表示"""
        self.clear()
        ctk.CTkLabel(self.main_frame, text='システム環境設定', font=config.FONT_TITLE).pack(pady=20, anchor="w")
        
        excel_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        excel_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(excel_frame, text='Excelデータソースの設定', font=config.FONT_LABEL_BUTTON).pack(pady=(5, 0), anchor="w")
        ctk.CTkLabel(excel_frame, text='出欠情報が格納されたExcelファイルを指定します。', font=config.FONT_SUBTITLE, text_color='gray').pack(pady=(0, 5), anchor="w")
        
        if FILE_PATH:
            file_path_var = tk.StringVar(value=FILE_PATH)
        else:
            file_path_var = tk.StringVar()
            
        file_frame = ctk.CTkFrame(excel_frame, fg_color="transparent")
        file_frame.pack(anchor='w', fill='x')
            
        file_entry = ctk.CTkEntry(file_frame, textvariable=file_path_var, width=350, font=(config.FONT_NAME, 16), state='disabled')
        file_entry.pack(side='left', padx=(0, 10))

        def select_file():
            f_path = filedialog.askopenfilename(title='出欠情報が格納されたExcelを選択', filetypes=[('Excelファイル', '*.xlsx;*.xls')])
            if f_path:
                file_path_var.set(f_path)
                globals()['FILE_PATH'] = f_path
            
        btn_file = ctk.CTkButton(file_frame, text='ファイルを選択', width=120, fg_color='#80d4ff', text_color='black', font=(config.FONT_NAME, 16), command=select_file)
        btn_file.pack(side='left')
        
        appearance_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        appearance_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(appearance_frame, text='外観設定', font=config.FONT_LABEL_BUTTON).pack(pady=5, anchor="w")
        
        mode = {"システム": "System", "ダーク": "Dark", "ライト": "Light"}
        def change_appearance(choice):
            try:
                ctk.set_appearance_mode(mode[choice])
                self.settings['appearance_mode'] = mode[choice]
                self.save_settings()
            except Exception:
                pass
        
        appearance_mode = self.settings.get('appearance_mode', config.APP_MODE)
        appearance_key = [k for k, v in mode.items() if v == appearance_mode]
        appearance_combo = ctk.CTkComboBox(appearance_frame, values=list(mode.keys()), font=(config.FONT_NAME, 16), width=120, command=change_appearance)
        appearance_combo.set(appearance_key[0] if appearance_key else "")
        appearance_combo.pack(pady=5, anchor="w")

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