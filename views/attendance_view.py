import datetime, re, math, openpyxl
import pandas as pd
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from tkcalendar import Calendar

from views.my_parts import CalendarInput, ModernTile
import attendance_calculation as ac
import config

class AttendanceView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self.file_path = self.app.settings.get('excel_file_path', config.FILE_PATH)

        self.show_attendance_date_select()

    def clear_frame(self):
        """フレーム内のウィジェットをすべて削除"""
        for widget in self.winfo_children():
            widget.destroy()

    def show_attendance_date_select(self):
        self.clear_frame()

        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(padx=0, pady=0, fill='x')
        ctk.CTkLabel(title_frame, text='', font=config.FONT_ICON_TITLE).pack(side='left', pady=(17, 13), anchor="w")
        ctk.CTkLabel(title_frame, text='出欠管理・確認', font=config.FONT_TITLE).pack(side='left', padx=10, pady=15, anchor="w")

        # 出席をとる日付を選択するタイル
        entry_attendance_frame = ModernTile(
            self, 
            title="出席をとる", 
            description="出席をとる日付を選択します。過去・別日の出席をとる場合は、日付を変更してください。", 
            left_icon=""
            )
        entry_attendance_frame.pack(padx=0, pady=(25, 0), fill="x")
        ctk.CTkLabel(entry_attendance_frame.container(), text='出席をとる日付', font=(config.FONT_NAME, 16)).pack(side='left', padx=0, pady=5)
        now = datetime.now().strftime("%#m/%#d")
        date_entry = CalendarInput(entry_attendance_frame.container(), app_ref=self.app, date_pattern="%#m/%#d")
        date_entry.pack(side='left', padx=5, pady=5)
        date_entry.set(now)
        btn_start = ctk.CTkButton(entry_attendance_frame.container(), text='出席をとる', width=140, height=30, fg_color=config.COLOR_BUTTON_BLUE, hover_color=config.HOVER_COLOR_BUTTON_BLUE, text_color=("white", "black"), font=(config.FONT_NAME, 14), command=lambda: self.start_attendance(date_entry.get().strip()))
        btn_start.pack(padx=0, pady=5, side='right')

        # 出欠状況を確認するタイル
        check_attendance_frame = ModernTile(
            self, 
            title="出欠状況を確認する", 
            description="期間を選択して出欠状況をテキストファイルで出力します。", 
            left_icon=""
            )
        check_attendance_frame.pack(padx=0, pady=(5, 0), fill="x")

        date_frame = ctk.CTkFrame(check_attendance_frame.container(), fg_color=("gray90", "gray20"))
        date_frame.pack(padx=0, pady=5, fill="x")
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

        period_entry_frame = ctk.CTkFrame(date_frame, fg_color="transparent")
        period_entry_frame.pack(padx=0, pady=(5, 0), fill="x")
        ctk.CTkLabel(period_entry_frame, text='開始日:', font=(config.FONT_NAME, 16)).pack(padx=10, pady=5, side='left')
        start_combo = ctk.CTkComboBox(period_entry_frame, font=(config.FONT_NAME, 16), dropdown_font=(config.FONT_NAME, 12), width=130, values=date_candidates_start, command=update_end_dates)
        start_combo.pack(padx=5, pady=5, side='left')
        ctk.CTkLabel(period_entry_frame, text='終了日:', font=(config.FONT_NAME, 16)).pack(padx=10, pady=5, side='left')
        end_combo = ctk.CTkComboBox(period_entry_frame, font=(config.FONT_NAME, 16), dropdown_font=(config.FONT_NAME, 12), width=130, values=date_candidates_end)
        end_combo.pack(padx=5, pady=5, side='left')

        info_frame = ctk.CTkFrame(date_frame, fg_color="transparent")
        info_frame.pack(pady=(0, 5), anchor="w")
        ctk.CTkLabel(info_frame, text='', font=config.FONT_ICON_TITLE).pack(padx=(10, 5), side='left', anchor="w")
        ctk.CTkLabel(info_frame, text='開始日と終了日を同じ日付に設定すると、その日の出欠状況のみを確認できます。', font=(config.FONT_NAME, 14), anchor="w", justify="left").pack(padx=0, pady=0, side='left')

        btn_check = ctk.CTkButton(check_attendance_frame.container(), text='出欠状況を出力', width=140, height=30, fg_color=config.COLOR_BUTTON_GRAY, hover_color=config.HOVER_COLOR_BUTTON_GRAY, text_color=("black", "white"), font=(config.FONT_NAME, 14), command=lambda: ac.calculate_rate_and_export(start_combo.get(), end_combo.get(), self.file_path, config.SHEET_NAME))
        btn_check.pack(padx=0, pady=5, side='right')        

    def start_attendance(self, date):
        self.df = pd.read_excel(self.file_path, sheet_name=config.SHEET_NAME, header=1, index_col=None)
        self.df = self.df.loc[:, ~self.df.columns.str.contains('^Unnamed')]
        self.date = date
        if date not in self.df.columns:
            self.df[date] = ''
        self.df[date] = self.df[date].astype(object)
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
        
        faculty_dict = {
            'T': '工学部',
            'S': '理学部',
            'H': '環境人間学部',
            }

        info = f'No. {self.current_idx+1} / 全 {len(self.df)} 名\n氏名: {name}\n学籍番号: {student_id}\n学年: {grade}  学部: {faculty_dict.get(faculty, faculty)}\n対象日: {self.date}'
        ctk.CTkLabel(self, text=info, font=ctk.CTkFont(family=config.FONT_NAME, size=16, weight='bold'), justify='left', anchor="w").pack(pady=15, fill="x")

        mark_defs = [
            ('出席', '〇 出席', config.COLOR_BUTTON_GREEN, config.HOVER_COLOR_BUTTON_GREEN),
            ('連絡あり', '△ 連絡あり欠席', config.COLOR_BUTTON_YELLOW, config.HOVER_COLOR_BUTTON_YELLOW),
            ('無断欠席', '× 無断欠席', config.COLOR_BUTTON_RED, config.HOVER_COLOR_BUTTON_RED),
            ('オ', 'オンライン', "gray50", ("gray60", "gray40")),
            ('忌引', '忌引き等', "gray50", ("gray60", "gray40")),
        ]
        
        btn_frame1 = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame1.pack(pady=5)
        btn_frame2 = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame2.pack(pady=5)
        
        for mark, label, color, hover_color in mark_defs[:3]:
            b = ctk.CTkButton(btn_frame1, text=label, width=140, height=40, fg_color=color, hover_color=hover_color, text_color='black', font=(config.FONT_NAME, 14, 'bold'), command=lambda m=mark: self.set_attendance(m))
            b.pack(side='left', padx=6)
            
        for mark, label, color, hover_color in mark_defs[3:]:
            b2 = ctk.CTkButton(btn_frame2, text=label, width=140, height=40, fg_color=color, hover_color=hover_color, text_color='black', font=(config.FONT_NAME, 14, 'bold'), command=lambda m=mark: self.set_attendance(m))
            b2.pack(side='left', padx=6)

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(pady=20)
        
        btn_prev = ctk.CTkButton(nav_frame, text='◀ 前の人へ', fg_color=config.COLOR_BUTTON_ORANGE, hover_color=config.HOVER_COLOR_BUTTON_ORANGE, text_color='black', font=(config.FONT_NAME, 14, 'bold'), command=self.prev_person)
        btn_prev.pack(side='left', padx=10)
        
        btn_next_nav = ctk.CTkButton(nav_frame, text='次の人へ ▶', fg_color=config.COLOR_BUTTON_GREEN, hover_color=config.HOVER_COLOR_BUTTON_GREEN, text_color='black', font=(config.FONT_NAME, 14, 'bold'), command=self.next_person)
        btn_next_nav.pack(side='left', padx=10)

        btn_top = ctk.CTkButton(self, text='保存して終了', width=120, fg_color=config.COLOR_BUTTON_RED, hover_color=config.HOVER_COLOR_BUTTON_RED, text_color='white', font=(config.FONT_NAME, 14), command=self.save_and_back_to_top)
        btn_top.place(relx=0.0, rely=1.0, anchor='sw', x=25, y=-21)

    def set_attendance(self, mark):
        self.df[self.date] = self.df[self.date].astype(object)
        self.df.at[self.current_idx, self.date] = str(mark)
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
            wb = openpyxl.load_workbook(self.file_path)
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
                cell.value = row[self.date]
            wb.save(self.file_path)
            messagebox.showinfo('保存完了', 'Excelファイルを保存しました。')
        except Exception as e:
            messagebox.showerror('保存エラー', f'Excel保存に失敗しました: {e}')
        self.app.show_top()