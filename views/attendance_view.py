import datetime, re, math, openpyxl
import pandas as pd
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import config
import attendance_calculation as ac

class AttendanceView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        self.show_attendance_date_select()

    def clear_frame(self):
        """フレーム内のウィジェットをすべて削除"""
        for widget in self.winfo_children():
            widget.destroy()

    def show_attendance_date_select(self):
        self.clear_frame()
        
        ctk.CTkLabel(self, text='👥 出欠管理', font=config.FONT_TITLE).pack(pady=(15, 5), anchor="w")
        ctk.CTkLabel(self, text='出席をとる日付を選択します。', font=config.FONT_SUBTITLE, text_color='gray50').pack(pady=(0, 5), anchor="w")

        btn_today = ctk.CTkButton(
            self, text='📅 今日の出席をとる', width=200, height=45, 
            fg_color='#66ff66', text_color='black', font=config.FONT_LABEL_BUTTON, 
            command=self.start_attendance_today)
        btn_today.pack(pady=10)
        
        btn_other = ctk.CTkButton(
            self, text='📆 過去・別日の出席をとる', width=200, height=45, 
            fg_color='#ff9900', text_color='black', font=config.FONT_LABEL_BUTTON, 
            command=self.start_attendance_otherday)
        btn_other.pack(pady=10)
        
        ctk.CTkLabel(self, text='', font=config.FONT_TITLE).pack(pady=15, anchor="w")
        ctk.CTkLabel(self, text='👥 出欠状況の確認', font=config.FONT_TITLE).pack(pady=(15, 5), anchor="w")
        ctk.CTkLabel(self, text='出欠状況をテキストファイルで出力します。', font=config.FONT_SUBTITLE, text_color='gray50').pack(pady=(0, 5), anchor="w")
        date_frame = ctk.CTkFrame(self)
        date_frame.pack(pady=15, fill="x", padx=10)
        date_candidates_start = self.app.get_available_dates()
        date_candidates_end = self.app.get_available_dates()

        def update_end_dates(event):
            """開始日が選択されたら、終了日の候補を更新する"""
            selected_start = start_combo.get()
            if selected_start in date_candidates_start:
                start_index = date_candidates_start.index(selected_start)
                new_end_dates = date_candidates_start[start_index:]
                end_combo.configure(values=new_end_dates)
                if end_combo.get() not in new_end_dates:
                    end_combo.set(new_end_dates[0] if new_end_dates else '')

        ctk.CTkLabel(date_frame, text='開始日:', font=(config.FONT_NAME, 16)).pack(side='left', padx=10, pady=10)
        start_combo = ctk.CTkComboBox(date_frame, font=(config.FONT_NAME, 16), width=130, values=date_candidates_start, command=update_end_dates)
        start_combo.pack(side='left', padx=5, pady=10)
        
        ctk.CTkLabel(date_frame, text='終了日:', font=(config.FONT_NAME, 16)).pack(side='left', padx=10, pady=10)
        end_combo = ctk.CTkComboBox(date_frame, font=(config.FONT_NAME, 16), width=130, values=date_candidates_end)
        end_combo.pack(side='left', padx=5, pady=10)
        
        ctk.CTkLabel(date_frame, text='ⓘ', font=(config.FONT_NAME, 18)).pack(side='left', anchor="w", padx=(15, 5))
        ctk.CTkLabel(date_frame, text='開始日と終了日を同じ日付に設定すると\nその日の出欠状況のみを確認できます。', font=(config.FONT_NAME, 14), anchor="w", justify="left").pack(side='left', padx=0)
        
        btn_check = ctk.CTkButton(self, text='👁 出欠状況を出力(.txt)', width=200, height=45, fg_color='#4375ff', text_color='white', font=config.FONT_LABEL_BUTTON, command=lambda: ac.calculate_rate_and_export(start_combo.get(), end_combo.get(), config.FILE_PATH, config.SHEET_NAME))
        btn_check.pack(pady=10)

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
        self.df = pd.read_excel(config.FILE_PATH, sheet_name=config.SHEET_NAME, header=1, index_col=None)
        self.df = self.df.loc[:, ~self.df.columns.str.contains('^Unnamed')]
        self.date = date
        if date not in self.df.columns:
            self.df[date] = ''
        self.current_idx = 0
        self.show_attendance_entry()

    def show_attendance_entry(self):
        self.clear_frame()
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
        ctk.CTkLabel(self, text=info, font=ctk.CTkFont(family=config.FONT_NAME, size=16, weight='bold'), justify='left', anchor="w").pack(pady=15, fill="x")

        mark_defs = [
            ('出席', '〇 出席', '#66ff66'),
            ('連絡あり', '△ 連絡あり欠席', '#ffff66'),
            ('無断欠席', '× 無断欠席', '#ff0000'),
            ('オ', 'オンライン', '#cccccc'),
            ('忌引', '忌引き等', '#cccccc'),
        ]
        
        btn_frame1 = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame1.pack(pady=5)
        btn_frame2 = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame2.pack(pady=5)
        
        for mark, label, color in mark_defs[:3]:
            b = ctk.CTkButton(btn_frame1, text=label, width=140, height=40, fg_color=color, text_color='black', font=(config.FONT_NAME, 14, 'bold'), command=lambda m=mark: self.set_attendance(m))
            b.pack(side='left', padx=6)
            
        for mark, label, color in mark_defs[3:]:
            b2 = ctk.CTkButton(btn_frame2, text=label, width=140, height=40, fg_color=color, text_color='black', font=(config.FONT_NAME, 14, 'bold'), command=lambda m=mark: self.set_attendance(m))
            b2.pack(side='left', padx=6)

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(pady=20)
        
        btn_prev = ctk.CTkButton(nav_frame, text='◀ 前の人へ', fg_color='#ff9900', text_color='black', font=(config.FONT_NAME, 14, 'bold'), command=self.prev_person)
        btn_prev.pack(side='left', padx=10)
        
        btn_next_nav = ctk.CTkButton(nav_frame, text='次の人へ ▶', fg_color='#66ff66', text_color='black', font=(config.FONT_NAME, 14, 'bold'), command=self.next_person)
        btn_next_nav.pack(side='left', padx=10)

        btn_top = ctk.CTkButton(self, text='保存して終了', width=120, fg_color='#ff0000', text_color='white', font=(config.FONT_NAME, 14), command=self.save_and_back_to_top)
        btn_top.place(relx=0.0, rely=1.0, anchor='sw', x=25, y=-21)

    def set_attendance(self, mark):
        self.df.at[self.current_idx, self.date] = mark
        self.next_person()

    def prev_person(self):
        if self.current_idx > 0:
            self.current_idx -= 1
        self.show_attendance_entry()

    def next_person(self):
        self.current_idx += 1
        def is_empty_name(idx):
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
            wb = openpyxl.load_workbook(config.FILE_PATH)
            ws = wb[config.SHEET_NAME]
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
            wb.save(config.FILE_PATH)
            messagebox.showinfo('保存完了', 'Excelファイルを保存しました。')
        except Exception as e:
            messagebox.showerror('保存エラー', f'Excel保存に失敗しました: {e}')
        self.app.show_top()