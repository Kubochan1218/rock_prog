# 2026年7月5日更新 (CustomTkinterモダンデザイン版)

import os, sys, json
import tkinter as tk
from tkinter import messagebox, filedialog
import tkinter.font as tkfont
import customtkinter as ctk
import pandas as pd

import config
from check_update import UpdateChecker
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
        master.iconbitmap(default='rock_icon.ico')  # アイコン設定（Windows用）

        self.settings = {}
        self.top_showen = True
        
        # ウィンドウの×ボタンに確認ダイアログを設定
        try:
            self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        except Exception:
            pass
            
        # 設定読み込み（操作支援など）
        self.load_settings()
        appearance_mode = self.settings.get('appearance_mode', config.APP_MODE)
        globals()['FILE_PATH'] = self.settings.get('excel_file_path', config.FILE_PATH)
        try:
            ctk.set_appearance_mode(appearance_mode)
        except Exception:
            ctk.set_appearance_mode(config.APP_MODE)

        # アップデートチェック
        update_checker = UpdateChecker()
        check_date = self.settings.get('last_update_check', None)
        if check_date != pd.Timestamp.now().strftime('%Y-%m-%d'): # 前回チェック日と今日の日付が異なる場合のみチェック
            if update_checker.check_for_update():
                if messagebox.askyesno("アップデート確認", f"新しいバージョン {update_checker.latest_version} が利用可能です。\n\nアップデートしますか？"):
                    update_checker.update_from_github()
            self.settings['last_update_check'] = pd.Timestamp.now().strftime('%Y-%m-%d')

        # 全体レイアウト：2カラム構成（左：固定サイドメニュー、右：動的画面）
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        
        # 左側：サイドバーフレーム
        self.sidebar = SidebarFrame(self.master, on_menu_select=self.change_screen, app=self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 右側：メインコンテンツ表示用フレーム
        self.main_frame = ctk.CTkFrame(self.master, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")
        
        self.change_screen("top")

        if not MainView.check_attendance_data_format(self, FILE_PATH):
            launch_converter = messagebox.askyesno(
                "出席データ形式の確認",
                config.UPDATE_LOG,
            )
            if launch_converter:
                converter_path = self.get_config_path('Converter.exe')
                if os.path.exists(converter_path):
                    try:
                        os.startfile(converter_path)
                    except Exception as e:
                        messagebox.showerror("エラー", f"変換ツールの起動に失敗しました:\n{e}")

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
        self.top_view.pack(fill='both', expand=True)
        self.top_showen = True

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
        self.top_showen = False

    def register_live(self, default_live_name=None):
        """ライブ情報の登録・編集画面を表示 (JSON保存・時刻選択版)"""
        self.clear()
        self.live_view = LiveView(self.main_frame, app=self, default_live_name=default_live_name)
        self.live_view.pack(fill='both', expand=True)
        self.top_showen = False

    def register_band(self, default_tab=None, default_live_name=None):
        """バンド登録画面を表示 (タブ切り替え・一括一覧表示＆ライブ名紐付け版)"""
        self.clear()
        self.band_view = BandView(self.main_frame, app=self, default_tab=default_tab, default_live_name=default_live_name)
        self.band_view.pack(fill='both', expand=True)
        self.top_showen = False

    def make_timetable(self, default_live_name=None):
        """タイムテーブル作成画面を表示"""
        self.clear()
        self.timetable_view = TimetableView(self.main_frame, app=self, default_live_name=default_live_name)
        self.timetable_view.pack(fill='both', expand=True)
        self.top_showen = False

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
                self.settings['excel_file_path'] = f_path
                self.save_settings()
            
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
        
        # バージョン情報
        version_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        version_frame.pack(side='bottom', pady=10, fill='x')
        ctk.CTkLabel(version_frame, text=f'ロック部 出席管理 version {config.VERSION}', font=(config.FONT_NAME, 12), text_color='gray').pack(side='left', padx=10, anchor="w")
        ctk.CTkLabel(version_frame, text='© 2026 Rock Club', font=(config.FONT_NAME, 12), text_color='gray').pack(side='right', padx=10, anchor="e")
        self.top_showen = False

    def on_close(self):
        if messagebox.askokcancel('確認', 'アプリを終了しますか？', parent=self.master):
            try:
                self.master.destroy()
                self.save_settings()
            except Exception:
                pass

    def get_config_path(self, filename='settings.json'):
        if getattr(sys, 'frozen', False) or '__compiled__' in globals():
            # Nuitkaの--onefile、またはPyInstallerで実行されている場合
            # sys.executable は「実行されているexeファイル自体の絶対パス」を指します
            base_dir = os.path.abspath(os.getcwd())
        else:
            # 通常のPythonスクリプトとして実行されている場合
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

    def save_settings(self):
        path = self.get_config_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                import json
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror('エラー', f'設定の保存に失敗しました:\n{e}', parent=self.master)

    def is_pinned(self, name):
        """現在のピン止め状態を確認する"""
        settings_path = self.get_config_path('settings.json')
        if not os.path.exists(settings_path):
            return False
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = data.get("quick_access", {}).get("items", [])
                # リストの中に同じ名前があるかチェック
                for item in items:
                    if item.get("name") == name:
                        return True
        except Exception:
            pass
        return False

    def pin_to_quick_access(self, widget, name, fg_color, command_str):
        """指定された機能をクイックアクセスに登録"""
        settings_path = self.get_config_path('settings.json') # パス取得関数に合わせて変更してください

        # JSONの読み込み（ファイルがない場合は初期化）
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {}
        else:
            data = {}

        # 構造の初期化を保証
        if "quick_access" not in data:
            data["quick_access"] = {}
        if "items" not in data["quick_access"]:
            data["quick_access"]["items"] = []

        items = data["quick_access"]["items"]

        # 重複チェック（既に同じ名前が登録されているか）
        for item in items:
            if item.get("name") == name:
                messagebox.showinfo("お知らせ", f"「{name}」は既にピン止めされています。")
                return

        # リストに追加して保存
        items.append({"name": name, "fg_color": fg_color, "command": command_str})
        
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("エラー", f"ピン止めの保存に失敗しました:\n{e}")
        if self.top_showen:
            self.show_top()  # トップ画面を再表示してクイックアクセスを更新

    def delete_from_quick_access(self, widget, name):
        """指定された機能をクイックアクセスから削除"""
        settings_path = self.get_config_path('settings.json')

        # JSONの読み込み（ファイルがない場合は初期化）
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {}
        else:
            data = {}

        # 構造の初期化を保証
        if "quick_access" not in data:
            data["quick_access"] = {}
        if "items" not in data["quick_access"]:
            data["quick_access"]["items"] = []

        items = data["quick_access"]["items"]

        # 指定された名前のアイテムを削除
        new_items = [item for item in items if item.get("name") != name]
        
        if len(new_items) == len(items):
            return

        data["quick_access"]["items"] = new_items
        
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("エラー", f"削除の保存に失敗しました:\n{e}")
        if self.top_showen:
            self.show_top()  # トップ画面を再表示してクイックアクセスを更新

    def bind_pin_menu(self, widget, name, fg_color, command_str):
        """ウィジェットに右クリックメニュー（ピン止め）を付与する汎用メソッド"""
        def show_menu(event):
            # tkinterの標準メニューを作成
            menu = tk.Menu(widget, tearoff=0, font=(FONT_NAME, 11))
            if self.is_pinned(name):
                # 既にピン止めされている場合 → 「解除」メニューを表示
                menu.add_command(
                    label="ピン止めを解除", 
                    command=lambda: self.delete_from_quick_access(widget, name)
                )
            else:
                # まだピン止めされていない場合 → 「ピン止め」メニューを表示
                menu.add_command(
                    label="クイックアクセスにピン止め", 
                    command=lambda: self.pin_to_quick_access(widget, name, fg_color, command_str)
                )
            
            menu.tk_popup(event.x_root, event.y_root)

        # Windows/Linux の右クリック (<Button-3>) にバインド
        widget.bind("<Button-3>", show_menu)
    

if __name__ == '__main__':
    root = ctk.CTk()
    
    app = AttendanceApp(root)
    root.mainloop()