import json, re, os
import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry, Calendar
import config

class LiveView(ctk.CTkFrame):
    def __init__(self, master, app, default_live_name=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self.default_live_name = default_live_name

        self.show_live_input()

    def clear_frame(self):
        """フレーム内のウィジェットをすべて削除"""
        for widget in self.winfo_children():
            widget.destroy()

    def show_live_input(self):
        self.clear_frame()
        
        # ライブ情報を保存するJSONファイルのパス
        LIVE_JSON_PATH = self.app.get_config_path('live_info.json')
        existing_lives = {}
        
        # 既存のJSONデータが存在すれば読み込む
        if os.path.exists(LIVE_JSON_PATH):
            try:
                with open(LIVE_JSON_PATH, 'r', encoding='utf-8') as f:
                    existing_lives = json.load(f)
            except Exception:
                pass
        
        # ヘッダー
        ctk.CTkLabel(self, text='📅 ライブ情報の登録・編集', font=config.FONT_TITLE).pack(pady=(15, 5), anchor="w")
        ctk.CTkLabel(self, text='ライブ名と日程を登録します。既存のライブを選択して編集も可能です。', font=config.FONT_SUBTITLE, text_color='gray50').pack(pady=(0, 5), anchor="w")

        # ライブ名 入力エリア（コンボボックスで既存データの呼び出し対応）
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(pady=10, fill='x', padx=10)
        
        ctk.CTkLabel(name_frame, text='ライブ名を入力して新規作成するか選択して編集:', font=config.FONT_LABEL_BUTTON).pack(side='left', padx=0)
        
        # 既存のライブ名をリストアップ
        live_names_list = list(existing_lives.keys())
        
        schedule_rows = [] # 追加された日程行のウィジェットを管理するリスト
        
        def on_live_select(choice):
            """プルダウンから既存ライブを選んだら、日程リストを復元する"""
            if choice in existing_lives:
                # 現在の入力行をすべて削除
                for r in schedule_rows.copy():
                    r['frame'].destroy()
                schedule_rows.clear()
                
                # 既存データから行を再生成
                for sch in existing_lives[choice].get('schedules', []):
                    add_date_row(date_val=sch.get('date', ''), start_val=sch.get('start', ''), end_val=sch.get('end', ''))

        def delete_live():
            """選択中のライブ情報を削除する"""
            live_name = live_name_combo.get().strip()
            if live_name in existing_lives:
                confirm = messagebox.askyesno("確認", f"「{live_name}」の情報を削除してもよろしいですか？")
                if confirm:
                    del existing_lives[live_name]
                    try:
                        with open(LIVE_JSON_PATH, 'w', encoding='utf-8') as f:
                            json.dump(existing_lives, f, ensure_ascii=False, indent=4)
                        messagebox.showinfo("削除完了", f"「{live_name}」の情報を削除しました。")
                        self.show_live_input()  # 再描画
                    except Exception as ex:
                        messagebox.showerror("削除エラー", f"JSONファイルへの書き込みに失敗しました:\n{ex}")
            else:
                messagebox.showerror("エラー", "削除対象のライブが存在しません。")

        live_name_combo = ctk.CTkComboBox(
            name_frame, 
            values=live_names_list if live_names_list else [""], 
            font=(config.FONT_NAME, 16),
            dropdown_font=(config.FONT_NAME, 12),
            width=300,
            command=on_live_select
        )
        if self.default_live_name and self.default_live_name in live_names_list:
            live_name_combo.set(self.default_live_name) # 初期値は指定されたライブ名
        else:
            live_name_combo.set("") # 初期値は空
        live_name_combo.pack(side='left', padx=10)
        
        delete_btn = ctk.CTkButton(name_frame, text="ライブを削除", font=(config.FONT_NAME, 14), width=80, fg_color=config.COLOR_BUTTON_RED, hover_color=config.HOVER_COLOR_BUTTON_RED, command=delete_live)
        delete_btn.pack(side='left', padx=5)

        # 日程設定エリア（複数日対応・スクロール可能・時刻選択式）
        ctk.CTkLabel(self, text='日程設定（開始・終了時刻）', font=config.FONT_LABEL_BUTTON).pack(pady=(15, 5), anchor="w", padx=10)
        
        # スクロール可能なフレームを使用（日程が増えても大丈夫なように）
        schedule_frame = ctk.CTkScrollableFrame(self, height=250)
        schedule_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 15分刻みの時刻リストを生成 (07:00 〜 20:45)
        time_options = [f"{h:02d}:{m:02d}" for h in range(7,21) for m in (0, 30)]

        def add_date_row(date_val="", start_val="", end_val=""):
            """日程入力行を1行追加する関数"""
            row = ctk.CTkFrame(schedule_frame)
            row.pack(fill='x', pady=5, padx=5)
            
            # 日数ラベル
            lbl_num = ctk.CTkLabel(row, text=f"{len(schedule_rows)+1}日目:", font=config.FONT_LABEL_BUTTON, width=50, anchor="w")
            lbl_num.pack(side='left', padx=(5, 10))
            
            # 日付
            ctk.CTkLabel(row, text="日付:", font=(config.FONT_NAME, 16)).pack(side='left')
            date_entry = ctk.CTkEntry(row, width=110, font=(config.FONT_NAME, 16), placeholder_text="YYYY-MM-DD")
            if date_val:
                date_entry.insert(0, date_val)
            date_entry.pack(side='left', padx=5)
            
            # カレンダー機能
            def open_calendar():
                try:
                    cal_win = ctk.CTkToplevel(self.master)
                    cal_win.title("日付を選択")
                    icon_path = self.app.get_config_path('rock_icon.ico')
                    cal_win.after(200, lambda: cal_win.iconbitmap(icon_path))
                    cal_win.grab_set()
                    cal = Calendar(cal_win, selectmode='day', date_pattern='yyyy-mm-dd', font=(config.FONT_NAME, 12))
                    cal.pack(padx=15, pady=15)
                    
                    def set_date():
                        date_entry.delete(0, 'end')
                        date_entry.insert(0, cal.get_date())
                        cal_win.destroy()
                        
                    ctk.CTkButton(cal_win, text='決定', font=config.FONT_LABEL_BUTTON, fg_color=config.COLOR_BUTTON_YELLOWGREEN, hover_color=config.HOVER_COLOR_BUTTON_YELLOWGREEN, text_color="black", command=set_date).pack(side='bottom', pady=10)
                except Exception:
                    messagebox.showinfo("お知らせ", "tkcalendarモジュールがインストールされていません。手入力してください。")

            btn_cal = ctk.CTkButton(row, text="📅", width=30, fg_color="gray50", hover_color=("gray60", "gray40"), text_color="black", command=open_calendar)
            btn_cal.pack(side='left', padx=(0, 15))
            
            # 開演時刻（コンボボックス）
            ctk.CTkLabel(row, text="開始:", font=(config.FONT_NAME, 16)).pack(side='left')
            start_combo = ctk.CTkComboBox(row, values=time_options, width=80, font=(config.FONT_NAME, 16), dropdown_font=(config.FONT_NAME, 12))
            start_combo.set(start_val if start_val else "10:00")
            start_combo.pack(side='left', padx=5)
            
            # 終演時刻（コンボボックス）
            ctk.CTkLabel(row, text="終了:", font=(config.FONT_NAME, 16)).pack(side='left', padx=(10, 0))
            end_combo = ctk.CTkComboBox(row, values=time_options, width=80, font=(config.FONT_NAME, 16), dropdown_font=(config.FONT_NAME, 12))
            end_combo.set(end_val if end_val else "18:00")
            end_combo.pack(side='left', padx=5)
            
            # 削除ボタン
            def remove_row():
                row.destroy()
                schedule_rows.remove(row_data)
                # 残った行の「◯日目」の数字を振り直す
                for idx, r_data in enumerate(schedule_rows):
                    r_data['lbl'].configure(text=f"{idx+1}日目:")
                    
            btn_del = ctk.CTkButton(row, text="削除", font=(config.FONT_NAME, 14), width=50, fg_color=config.COLOR_BUTTON_RED, hover_color=config.HOVER_COLOR_BUTTON_RED, command=remove_row)
            btn_del.pack(side='right', padx=10)
            
            row_data = {"frame": row, "lbl": lbl_num, "date": date_entry, "start": start_combo, "end": end_combo}
            schedule_rows.append(row_data)

        # 初期状態で1行目を追加
        add_date_row()

        # アクションボタン群（下部）
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15, fill='x', padx=10)
        
        btn_add = ctk.CTkButton(btn_frame, text='➕ 日程を追加', font=config.FONT_LABEL_BUTTON, fg_color=config.COLOR_BUTTON_BLUE, hover_color=config.HOVER_COLOR_BUTTON_BLUE, text_color='black', command=lambda: add_date_row())
        btn_add.pack(side='left', padx=5)

        def save_live_info():
            """入力内容を検証し、JSONファイルとして保存する"""
            live_name = live_name_combo.get().strip()
            
            if live_name == "" or live_name == "ライブ名を入力するか選択":
                messagebox.showerror("エラー", "ライブ名を入力してください。")
                return
            if not schedule_rows:
                messagebox.showerror("エラー", "日程を少なくとも1日以上追加してください。")
                return
                
            schedules = []
            for idx, r_data in enumerate(schedule_rows):
                d = r_data['date'].get().strip()
                s = r_data['start'].get().strip()
                e = r_data['end'].get().strip()
                
                if not d or not s or not e:
                    messagebox.showerror("エラー", f"{idx+1}日目の入力項目に空欄があります。")
                    return
                # 時刻フォーマット（HH:MM または H:MM）のチェック
                if not re.match(r'^\d{1,2}:\d{2}$', s) or not re.match(r'^\d{1,2}:\d{2}$', e):
                    messagebox.showerror("エラー", f"{idx+1}日目の時刻は「HH:MM」形式（例: 13:00）で入力してください。")
                    return
                
                schedules.append({
                    "day": idx + 1,
                    "date": d,
                    "start": s,
                    "end": e
                })
                
            # 既存の辞書に上書き（または新規追加）
            existing_lives[live_name] = {
                "live_name": live_name,
                "schedules": schedules,
                "updated_at": __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # JSONへ書き込み
            try:
                with open(LIVE_JSON_PATH, 'w', encoding='utf-8') as f:
                    json.dump(existing_lives, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("保存完了", f"「{live_name}」の情報を保存しました。")
                self.show_live_input()
            except Exception as ex:
                messagebox.showerror("保存エラー", f"JSONファイルへの保存に失敗しました:\n{ex}")

        btn_save = ctk.CTkButton(btn_frame, text='💾 ライブ情報を保存', font=config.FONT_LABEL_BUTTON, fg_color=config.COLOR_BUTTON_YELLOWGREEN, hover_color=config.HOVER_COLOR_BUTTON_YELLOWGREEN, text_color='black', width=160, height=40, command=save_live_info)
        btn_save.pack(side='right', padx=5)
        
        if live_name_combo.get() and live_name_combo.get() in existing_lives:
            on_live_select(live_name_combo.get())  # 選択時の処理を呼び出して日程を復元