import json, os, difflib, re, openpyxl
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import pandas as pd
import config
import attendance_calculation as ac
import band_selection as bs

class BandView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        self.show_band_input()

    def clear_frame(self):
        """フレーム内のウィジェットをすべて削除"""
        for widget in self.winfo_children():
            widget.destroy()

    def show_band_input(self):
        self.clear_frame()
        
        LIVE_JSON_PATH = self.app.get_config_path('live_info.json')
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

        # 上部に切り替え用のタブビューを作成
        tabview = ctk.CTkTabview(self, anchor="nw")
        tabview.pack(fill="both", expand=True, padx=0, pady=0)

        self.show_setup_screen(tabview, existing_lives)
        self.show_management_screen(tabview, existing_lives)
        self.setup_band_selection_tab(tabview, existing_lives)

    # タブ表示
    def show_setup_screen(self, tabview, existing_lives):
        """ライブの選択とExcelファイルの読み込み画面"""
        tab = tabview.add("📥 新規一括インポート")

        ctk.CTkLabel(tab, text='🎤 バンド応募データの一括インポート', font=config.FONT_TITLE).pack(pady=15, anchor="w")

        form_frame = ctk.CTkFrame(tab, fg_color="transparent")
        form_frame.pack(pady=5, fill='x', padx=10)

        # 1. ライブ名選択
        ctk.CTkLabel(form_frame, text='対象のライブを選択:', font=config.FONT_LABEL_BUTTON).pack(anchor='w', pady=0)
        live_combo = ctk.CTkComboBox(form_frame, values=list(existing_lives.keys()), width=300, font=(config.FONT_NAME, 16))
        live_combo.pack(anchor='w', pady=(0, 15))

        # 2. ファイル選択
        ctk.CTkLabel(form_frame, text='応募フォームのExcelファイル:', font=config.FONT_LABEL_BUTTON).pack(anchor='w', pady=5)
        file_path_var = tk.StringVar()
            
        file_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        file_frame.pack(anchor='w', fill='x')
            
        file_entry = ctk.CTkEntry(file_frame, textvariable=file_path_var, width=350, font=(config.FONT_NAME, 16), state='disabled')
        file_entry.pack(side='left', padx=(0, 10))

        def select_file():
            f_path = filedialog.askopenfilename(title='応募バンド情報のExcelを選択', filetypes=[('Excelファイル', '*.xlsx;*.xls')])
            if f_path:
                file_path_var.set(f_path)
            
        btn_file = ctk.CTkButton(file_frame, text='ファイルを選択', width=120, fg_color='#80d4ff', text_color='black', font=(config.FONT_NAME, 16), command=select_file)
        btn_file.pack(side='left')

        # 3. 実行ボタン
        def process_excel():
            target_live = live_combo.get()
            target_file = file_path_var.get()
            if not target_live or not target_file:
                messagebox.showerror('エラー', 'ライブとファイルの両方を選択してください。')
                return
            self.parse_and_match(target_live, target_file, tab, existing_lives)

        btn_next = ctk.CTkButton(tab, text='🚀 データの読み込みを開始', font=config.FONT_LABEL_BUTTON, fg_color='#bfff80', text_color='black', width=300, height=45, command=process_excel)
        btn_next.pack(pady=40)

    def show_management_screen(self, tabview, existing_lives):
        """STEP 1: 登録済みバンドの抽出と編集・削除画面"""
        tab = tabview.add("📝 登録済みバンドの管理")

        ctk.CTkLabel(tab, text='📝 登録済みバンドの管理（編集・削除）', font=config.FONT_TITLE).pack(pady=15, anchor="w")

        filter_frame = ctk.CTkFrame(tab, fg_color="transparent")
        filter_frame.pack(pady=5, fill='x', padx=10)

        ctk.CTkLabel(filter_frame, text='表示するライブを選択:', font=config.FONT_LABEL_BUTTON).pack(side='left', padx=(0, 10))
        live_selector = ctk.CTkComboBox(filter_frame, values=list(existing_lives.keys()), width=250, font=(config.FONT_NAME, 16))
        live_selector.pack(side='left', padx=5)

        # リスト描画用のコンテナフレーム
        list_container = ctk.CTkFrame(tab, fg_color="transparent")
        list_container.pack(fill='both', expand=True, padx=5, pady=10)

        def refresh_managed_bands(*args):
            """選択されたライブに紐づくバンドを再読み込みして描画"""
            for widget in list_container.winfo_children():
                widget.destroy()

            selected_live = live_selector.get()
            if not selected_live:
                return

            try:
                wb = openpyxl.load_workbook(config.FILE_PATH, data_only=True)
                if '登録済みバンド' not in wb.sheetnames:
                    ctk.CTkLabel(list_container, text='登録されているバンドはありません。', font=(config.FONT_NAME, 16)).pack(pady=20)
                    return
                ws = wb['登録済みバンド']
            except Exception as e:
                ctk.CTkLabel(list_container, text=f'Excelの読み込みに失敗しました: {e}', font=(config.FONT_NAME, 16), text_color='red').pack(pady=20)
                return

            managed_scroll = ctk.CTkScrollableFrame(list_container)
            managed_scroll.pack(fill='both', expand=True, padx=0, pady=0)

            # メンバー再編集用の名簿データ取得
            try:
                df_roster = pd.read_excel(config.FILE_PATH, sheet_name=config.SHEET_NAME, header=1)
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
                ctk.CTkLabel(b_frame, text=str(b_name), font=(config.FONT_NAME, 14, 'bold'), width=360, anchor='w').pack(side='left', padx=10, anchor='n', pady=6, expand=False)

                # メンバー表示（一人一行で縦に並べる）
                m_txt = "\n".join(m_list) if m_list else "（メンバーなし）"
                ctk.CTkLabel(b_frame, text=m_txt, font=(config.FONT_NAME, 14), anchor='w', justify='left').pack(side='left', padx=10, fill='x', expand=True, anchor='n', pady=6)

                # クロージャ対策を施した削除/編集コマンドの生成
                def make_delete_cmd(target_row=r_idx, name=b_name):
                    return lambda: delete_band(target_row, name)

                def make_edit_cmd(target_row=r_idx, name=b_name, current_m=m_list):
                    return lambda: open_manage_edit_popup(target_row, name, current_m)

                def delete_band(target_row, name):
                    if messagebox.askyesno('確認', f'本当にバンド「{name}」を削除しますか？'):
                        try:
                            edit_wb = openpyxl.load_workbook(config.FILE_PATH)
                            edit_ws = edit_wb['登録済みバンド']
                            edit_ws.delete_rows(target_row) # 該当行を丸ごと削除
                            edit_wb.save(config.FILE_PATH)
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

                    ctk.CTkLabel(popup, text='演奏時間:', font=(config.FONT_NAME, 14)).pack(anchor='w', padx=15)
                    time_entry = ctk.CTkEntry(popup, font=(config.FONT_NAME, 16), width=200)
                    time_entry.pack(anchor='w', padx=15, pady=2)
                    time_entry.insert(0, str(p_time))

                    ctk.CTkLabel(popup, text='出演日:', font=(config.FONT_NAME, 14)).pack(anchor='w', padx=15)
                    date_entry = ctk.CTkEntry(popup, font=(config.FONT_NAME, 16), width=200)
                    date_entry.pack(anchor='w', padx=15, pady=2)
                    date_entry.insert(0, str(p_date))

                    ctk.CTkLabel(popup, text='メンバー設定 (最大10名):', font=config.FONT_LABEL_BUTTON).pack(pady=(10, 0), anchor='w', padx=15)
                    
                    edit_scroll = ctk.CTkScrollableFrame(popup, height=180)
                    edit_scroll.pack(fill='both', expand=True, padx=15, pady=5)

                    combos = []
                    for i in range(10):
                        cb = ctk.CTkComboBox(edit_scroll, values=[''] + roster_names, width=200, font=(config.FONT_NAME, 16))
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
                            edit_wb = openpyxl.load_workbook(config.FILE_PATH)
                            edit_ws = edit_wb['登録済みバンド']
                            
                            # メンバー上書き (2~11列目)
                            for idx, m_name in enumerate(new_members, 2):
                                edit_ws.cell(row=target_row, column=idx).value = m_name
                            
                            # 演奏時間(12列目)・出演日(13列目)の上書き
                            edit_ws.cell(row=target_row, column=12).value = time_entry.get()
                            edit_ws.cell(row=target_row, column=13).value = date_entry.get()

                            edit_wb.save(config.FILE_PATH)
                            messagebox.showinfo('成功', 'バンド情報を更新しました。')
                            popup.grab_release()
                            popup.destroy()
                            refresh_managed_bands() # 画面リフレッシュ
                        except Exception as e:
                            messagebox.showerror('エラー', f'更新に失敗しました: {e}')

                    btn_save_pop = ctk.CTkButton(popup, text='💾 変更を保存', font=config.FONT_LABEL_BUTTON, fg_color='#bfff80', text_color='black', command=save_managed_edit)
                    btn_save_pop.pack(pady=15)

                # 右端配置ボタン（削除と編集）
                btn_del = ctk.CTkButton(b_frame, text='× 削除', width=70, font=(config.FONT_NAME, 16), fg_color='#ff8080', text_color='black', command=make_delete_cmd())
                btn_del.pack(side='right', padx=10, anchor='n', pady=6)

                btn_edt = ctk.CTkButton(b_frame, text='✏️ 編集', width=70, font=(config.FONT_NAME, 16), fg_color='#ffd480', text_color='black', command=make_edit_cmd())
                btn_edt.pack(side='right', padx=5, anchor='n', pady=6)

            if not has_bands:
                ctk.CTkLabel(list_container, text='選択されたライブに登録されているバンドはありません。', font=(config.FONT_NAME, 16)).pack(pady=20)

        live_selector.configure(command=refresh_managed_bands)
        if list(existing_lives.keys()):
            live_selector.set(list(existing_lives.keys())[0])
            refresh_managed_bands()

    def setup_band_selection_tab(self, tabview, existing_lives):
        """バンド選出タブを追加し、UIを構築する"""
        # 1. 新しいタブ「バンド選出」を追加
        tab = tabview.add("バンド選出")
        
        # タイトル
        ctk.CTkLabel(tab, text="🎸 バンド選出 条件設定", font=config.FONT_TITLE).pack(pady=15, anchor="w")
        
        # 全体フレーム（すべてpackで配置）
        scroll_frame = ctk.CTkFrame(tab, fg_color="transparent")
        scroll_frame.pack(pady=5, fill='x', padx=10)
        
        # 各行のラベル幅を「300ピクセル」に固定し、入力欄の左端を綺麗に揃える
        LBL_WIDTH = 300

        date_frame = ctk.CTkFrame(scroll_frame)
        date_frame.pack(pady=0, fill="x", padx=0)
        date_candidates_start = self.app.get_available_dates()
        date_candidates_end = self.app.get_available_dates()

        def update_end_dates(event):
            """開始日が選択されたら、終了日の候補を更新する"""
            selected_start = self.start_combo.get()
            if selected_start in date_candidates_start:
                start_index = date_candidates_start.index(selected_start)
                new_end_dates = date_candidates_start[start_index:]
                self.end_combo.configure(values=new_end_dates)
                if self.end_combo.get() not in new_end_dates:
                    self.end_combo.set(new_end_dates[0] if new_end_dates else '')

        def update_max_time(event):
            """ライブ名が変更されたら、ライブ総時間を更新する"""
            selected_live = self.live_combo.get()
            if selected_live in existing_lives:
                total_minutes = 0
                schedules = existing_lives[selected_live].get('schedules', [])
                for sched in schedules:
                    start_str = sched.get('start')
                    end_str = sched.get('end')
                    if start_str and end_str:
                        start_time = pd.to_datetime(start_str, format='%H:%M')
                        end_time = pd.to_datetime(end_str, format='%H:%M')
                        duration = end_time - start_time
                        total_minutes += duration.total_seconds() / 60
                self.entry_total_time.delete(0, 'end')
                self.entry_total_time.insert(0, str(int(total_minutes)))

        ctk.CTkLabel(date_frame, text='出席率計算 開始日:', font=(config.FONT_NAME, 16)).pack(side='left', padx=10, pady=6)
        self.start_combo = ctk.CTkComboBox(date_frame, font=(config.FONT_NAME, 16), width=130, values=date_candidates_start, command=update_end_dates)
        self.start_combo.pack(side='left', padx=5, pady=6)
        
        ctk.CTkLabel(date_frame, text='出席率計算 終了日:', font=(config.FONT_NAME, 16)).pack(side='left', padx=10, pady=6)
        self.end_combo = ctk.CTkComboBox(date_frame, font=(config.FONT_NAME, 16), width=130, values=date_candidates_end)
        self.end_combo.pack(side='left', padx=5, pady=6)
        
        ctk.CTkLabel(date_frame, text='ⓘ', font=(config.FONT_NAME, 18)).pack(side='left', anchor="w", padx=(15, 5))
        ctk.CTkLabel(date_frame, text='開始日と終了日を同じ日付に設定すると\nその日の出欠状況のみ選出に使用します。', font=(config.FONT_NAME, 14), anchor="w", justify="left").pack(side='left', padx=0)
        
        # ライブを選択
        row_live = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row_live.pack(fill="x", pady=6, padx=10)
        lbl_live = ctk.CTkLabel(row_live, text="🎤 ライブを選択:", font=(config.FONT_NAME, 16), width=LBL_WIDTH, anchor="w")
        lbl_live.pack(side="left")
        self.live_combo = ctk.CTkComboBox(row_live, font=(config.FONT_NAME, 16), width=180, values=list(existing_lives.keys()), command=update_max_time)
        self.live_combo.pack(side="left", padx=5)
        
        # 募集バンド数
        row_bands = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row_bands.pack(fill="x", pady=6, padx=10)
        lbl_bands = ctk.CTkLabel(row_bands, text="👥 募集バンド数 (空欄で上限なし):", font=(config.FONT_NAME, 16), width=LBL_WIDTH, anchor="w")
        lbl_bands.pack(side="left")
        self.entry_max_bands = ctk.CTkEntry(row_bands, width=180, font=(config.FONT_NAME, 14))
        self.entry_max_bands.pack(side="left", padx=5)
        
        # ライブの総時間
        row_time = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row_time.pack(fill="x", pady=6, padx=10)
        lbl_time = ctk.CTkLabel(row_time, text="⏳ ライブの総時間 (分・空欄で上限なし):", font=(config.FONT_NAME, 16), width=LBL_WIDTH, anchor="w")
        lbl_time.pack(side="left")
        self.entry_total_time = ctk.CTkEntry(row_time, width=180, font=(config.FONT_NAME, 14))
        self.entry_total_time.pack(side="left", padx=5)

        # リハーサル時間
        row_reh = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row_reh.pack(fill="x", pady=6, padx=10)
        lbl_reh = ctk.CTkLabel(row_reh, text="🔄 リハーサル時間 (分):", font=(config.FONT_NAME, 16), width=LBL_WIDTH, anchor="w")
        lbl_reh.pack(side="left")
        self.entry_rehearsal_time = ctk.CTkEntry(row_reh, width=180, font=(config.FONT_NAME, 14))
        self.entry_rehearsal_time.insert(0, "20")  # デフォルト値 20分
        self.entry_rehearsal_time.pack(side="left", padx=5)
        
        # 選出ボタン
        btn_select = ctk.CTkButton(
            scroll_frame, 
            text="✨ この条件でバンドを選出する", 
            font=config.FONT_LABEL_BUTTON, 
            fg_color="#00ff62", 
            text_color="black", 
            height=40,
            command=self.execute_band_selection
        )
        btn_select.pack(pady=20, padx=10, fill="x")
        
        # 結果表示エリア
        result_header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        result_header_frame.pack(fill="x", pady=0, padx=0)
        
        result_lbl = ctk.CTkLabel(result_header_frame, text="📋 選出結果出力", font=config.FONT_LABEL_BUTTON)
        result_lbl.pack(pady=5, anchor="w", padx=10, side="left")

        copy_btn = ctk.CTkButton(result_header_frame, text="📋 結果をクリップボードにコピー", font=(config.FONT_NAME, 14), fg_color="#80d4ff", text_color="black", command=self.copy_result_to_clipboard)
        copy_btn.pack(pady=5, padx=10, side="left")

        self.result_textbox = ctk.CTkTextbox(scroll_frame, height=250, font=(config.FONT_NAME, 14))
        self.result_textbox.pack(fill="both", expand=True, pady=5, padx=10)

    # 各種機能
    def parse_and_match(self, live_name, file_path, parent_tab, existing_lives):
        """Excelのパースと自動名寄せ処理"""
        live_data = existing_lives[live_name]
        try:
            df_all = pd.read_excel(file_path)
            df_band = df_all.iloc[:, 2:]
                
            df_roster = pd.read_excel(config.FILE_PATH, sheet_name=config.SHEET_NAME, header=1)
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

        self.show_list_screen(parsed_bands, live_name, live_data, roster_names, parent_tab)

    def convert_perform_dates(self, perform_date_str, live_data):
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

    def show_list_screen(self, parsed_bands, live_name, live_data, roster_names, parent_tab):
        """読み込み結果の一覧表示と手動修正画面"""
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
            name_lbl = ctk.CTkLabel(row_frame, text=b_data['band_name'], font=(config.FONT_NAME, 14, 'bold'), width=360, anchor='w')
            name_lbl.pack(side='left', padx=10, anchor='n', pady=6, expand=False)

            # メンバー表示（一人一行で縦に並べる: \n で結合し justify='left'）
            members_txt = "\n".join(b_data['matched_members']) if b_data['matched_members'] else "（メンバーなし・要確認）"
            mem_lbl = ctk.CTkLabel(row_frame, text=members_txt, font=(config.FONT_NAME, 14), anchor='w', justify='left')
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
                ctk.CTkLabel(popup, text=current_band['members_raw'], font=(config.FONT_NAME, 14), justify='left', fg_color=("gray85", "gray25"), corner_radius=5).pack(fill='x', padx=15, pady=5, ipady=5)

                ctk.CTkLabel(popup, text='メンバー設定 (最大10名):', font=config.FONT_LABEL_BUTTON).pack(pady=(10, 0), anchor='w', padx=15)

                edit_scroll = ctk.CTkScrollableFrame(popup, height=180)
                edit_scroll.pack(fill='both', expand=True, padx=15, pady=5)

                combos = []
                for i in range(10):
                    cb = ctk.CTkComboBox(edit_scroll, values=[''] + roster_names, width=200, font=(config.FONT_NAME, 16))
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
                    self.show_list_screen(parsed_bands, live_name, live_data, roster_names, parent_tab)

            # 削除ボタンをコンテナの右側に配置
            btn_del = ctk.CTkButton(row_frame, text='× 削除', width=70, font=(config.FONT_NAME, 16), fg_color='#ff8080', text_color='black', command=make_import_delete_cmd())
            btn_del.pack(side='right', padx=10, anchor='n', pady=6)

            btn_edit = ctk.CTkButton(row_frame, text='✏ 修正', width=70, font=(config.FONT_NAME, 16), fg_color='#ffd480', text_color='black', command=open_edit_popup)
            btn_edit.pack(side='right', padx=5, anchor='n', pady=6)

        # Excelへの一括書き込み処理
        def register_all_to_excel():
            try:
                wb = openpyxl.load_workbook(config.FILE_PATH)
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
                        
                    mapped_dates = self.convert_perform_dates(b_data['dates_raw'], live_data)
                    
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

                wb.save(config.FILE_PATH)
                try:
                    self.app.settings['last_startup'] = __import__('datetime').date.today().isoformat()
                    self.app.save_settings()
                except Exception:
                    pass            
                messagebox.showinfo('一括登録完了', f'計 {len(parsed_bands)} バンドを「{live_name}」として登録しました。')
                self.app.show_top()
            except Exception as e:
                messagebox.showerror('保存エラー', f'Excel保存に失敗しました:\n{e}')

        # 登録実行ボタン（右下に配置）
        btn_register = ctk.CTkButton(parent_tab, text='✨ この内容で全て登録', font=config.FONT_LABEL_BUTTON, fg_color='#00ff62', text_color='black', height=40, command=register_all_to_excel)
        btn_register.place(relx=1.0, rely=1.0, anchor='se', x=-25, y=-21)

        # キャンセルボタン（左下に配置）
        btn_cancel = ctk.CTkButton(parent_tab, text='キャンセル', font=(config.FONT_NAME, 16), fg_color='#ff0000', text_color='white', width=120, command=self.show_band_input)
        btn_cancel.place(relx=0.0, rely=1.0, anchor='sw', x=25, y=-21)

    def execute_band_selection(self):
        """UIの入力値を解析し、ac.calculate_attendance_rateとbs.select_bandsを実行する"""
        start_date = self.start_combo.get()
        end_date = self.end_combo.get()
        live_name = self.live_combo.get()

        # 期間は必須バリデーション
        if not start_date or not end_date:
            messagebox.showwarning("入力エラー", "出席率計算の期間（開始日・終了日）を選択してください。")
            return
        period = f"{start_date}～{end_date}"

        # 指定期間の出席率計算
        ac.calculate_attendance_rate(start_date, end_date, config.FILE_PATH, config.SHEET_NAME)
            
        # 募集バンド数（未入力時は上限なし -> 9999）
        max_bands_val = self.entry_max_bands.get().strip()
        max_bands = int(max_bands_val) if max_bands_val else 9999
        
        # ライブ総時間（未入力時は上限なし -> 999999）
        total_time_val = self.entry_total_time.get().strip()
        total_time = int(total_time_val) if total_time_val else 999999
        
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
                    period=period,
                    slots=max_bands,
                    total_time=total_time,
                    change_time=rehearsal_time,
                    file_path=config.FILE_PATH,
                    live_name=live_name
                )
                
                self.result_textbox.delete("1.0", "end")
                if results:
                    # 戻り値は文字列
                    self.result_textbox.insert("end", results)
                else:
                    self.result_textbox.insert("end", "❌ 条件に一致する、または選出枠に入るバンドが見つかりませんでした。")
                
        except Exception as e:
            self.result_textbox.delete("1.0", "end")
            messagebox.showerror("実行エラー", f"選出処理中にエラーが発生しました:\n{str(e)}")

    def copy_result_to_clipboard(self):
        """結果テキストをクリップボードにコピー"""
        result_text = self.result_textbox.get("1.0", "end").strip()
        if result_text:
            self.master.clipboard_clear()
            self.master.clipboard_append(result_text)
            messagebox.showinfo("コピー完了", "選出結果をクリップボードにコピーしました。")
        else:
            messagebox.showwarning("コピー失敗", "コピーする内容がありません。")