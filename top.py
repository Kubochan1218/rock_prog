import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime
import csv, os, sys, json, shutil
from models import LiveSchedule, BandInfo
from datetime import timedelta

class TopWindow(tk.Toplevel):
    # フィルタ条件の初期化は__init__内で行う
    def get_json_path(self, filename="schedule_data.json", mode="r"):
        import sys
        if hasattr(sys, '_MEIPASS'):
            # PyInstallerでexe化した場合も、常にexeのある場所を参照
            base_dir = os.path.dirname(sys.executable)
        else:
            # スクリプト実行時はtop.pyのあるディレクトリ
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, filename)
    def __init__(self, master=None):
        super().__init__(master)
        self.title("ライブ日程設定")
        self.geometry("840x600")  # order.pyのウィンドウサイズに合わせて拡大
        self.minsize(800, 600)
        self.schedules = []
        self.band_data = self.load_band_infos_from_csv(os.path.join(os.path.dirname(sys.argv[0]), "bands.csv"))
        self.tabs = {}
        self.used_band_names = set()
        self.tab_control = None
        self.order_area = None
        self.top_widgets = []  # トップ画面ウィジェットを管理
        self.filter_options = {'オプション1': '', 'オプション2': '', 'オプション3': ''}  # フィルタ条件
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._last_font_copied = False

    def _ensure_font_file(self, filename, friendly_name="フォント"):
        """アプリフォルダに filename がなければ Windows のフォントフォルダからコピーを試みる。
        成功した場合はコピー先のパスを返す。失敗した場合は None を返す（かつエラーメッセージを表示）。
        """
        app_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(app_dir, filename)
        if os.path.exists(target_path):
            self._last_font_copied = False
            return target_path

        # Windows のフォントディレクトリを探す
        windir = os.environ.get("WINDIR", "C:\\Windows")
        fonts_dir = os.path.join(windir, "Fonts")
        candidates = []
        try:
            for f in os.listdir(fonts_dir):
                if f.lower() == filename.lower() or filename.split('.')[0].lower() in f.lower():
                    candidates.append(os.path.join(fonts_dir, f))
        except Exception:
            candidates = []

        if not candidates:
            messagebox.showerror(f"{friendly_name} コピー失敗", f"{filename} が見つかりません。\nシステムフォントフォルダに {filename} が存在しないようです。", parent=self)
            return None

        # コピーを試みる（成功したらフラグを立てて返す。ダイアログは後で出力完了時にまとめて表示）
        for src in candidates:
            try:
                shutil.copy2(src, target_path)
                self._last_font_copied = True
                return target_path
            except Exception:
                continue

        messagebox.showerror(f"{friendly_name} コピー失敗", f"{filename} のコピーに失敗しました。手動で {filename} をアプリフォルダに置いてください。", parent=self)
        return None

    def on_close(self):
        if messagebox.askokcancel("確認", "変更内容を保存せずにウィンドウを閉じますか？", parent=self):
            self.destroy()

    def create_widgets(self):
        default_font = ("Meiryo", 12)
        frame = tk.LabelFrame(self, text="日程追加", font=default_font)
        frame.pack(pady=10, padx=10, fill=tk.X, anchor="w")
        self.top_widgets.append(frame)

        tk.Label(frame, text="日付：", font=default_font, anchor="w").grid(row=0, column=0, sticky="w")
        self.date_entry = DateEntry(frame, width=12, background='darkblue',
                                    foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd', font=default_font)
        self.date_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        tk.Label(frame, text="開始時刻：", font=default_font, anchor="w").grid(row=1, column=0, sticky="w")
        self.start_time = ttk.Combobox(frame, values=self.time_options(), width=10, state="normal")
        self.start_time.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.start_time.configure(font=default_font)

        tk.Label(frame, text="終了時刻：", font=default_font, anchor="w").grid(row=2, column=0, sticky="w")
        self.end_time = ttk.Combobox(frame, values=self.time_options(), width=10, state="normal")
        self.end_time.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        self.end_time.configure(font=default_font)

        btn_add = tk.Button(frame, text="追加", command=self.add_schedule, font=("Meiryo", 12, "bold"), bg="#e0f7fa")
        btn_add.grid(row=3, column=0, pady=10, sticky="w")
        try:
            self.add_tooltip(btn_add, '日程を追加します')
        except Exception:
            pass

        btn_load = tk.Button(frame, text="読み込み", command=self.load_schedules, bg="#b2dfdb", font=default_font)
        btn_load.grid(row=3, column=1, pady=10, sticky="w")
        try:
            self.add_tooltip(btn_load, '保存済みの日程を読み込みます')
        except Exception:
            pass

        # 引き継ぎボタン追加
        btn_transfer = tk.Button(frame, text="他のPCへ引き継ぎ", command=self.transfer_data, font=("Meiryo", 12, "bold"), bg="#ffe082")
        btn_transfer.grid(row=3, column=2, pady=10, sticky="w")
        try:
            self.add_tooltip(btn_transfer, 'データをデスクトップの引き継ぎフォルダにコピーします')
        except Exception:
            pass

        # 日程リスト表示エリア
        list_frame = tk.LabelFrame(self, text="日程リスト", font=default_font)
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True, anchor="w")
        self.top_widgets.append(list_frame)

        self.listbox = tk.Listbox(list_frame, width=50, height=3, font=("Meiryo", 12, "bold"), selectbackground="#ffe082")
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor="w")

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # ボタンエリア（中央揃え・横並び）
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10, anchor="w")
        self.top_widgets.append(btn_frame)

        btn_edit = tk.Button(btn_frame, text="編集", command=self.edit_schedule, bg="#ffe082", font=default_font, width=5, height=1)
        btn_edit.pack(side=tk.LEFT, padx=8)
        try:
            self.add_tooltip(btn_edit, '選択した日程を編集します')
        except Exception:
            pass

        btn_delete = tk.Button(btn_frame, text="削除", command=self.delete_schedule, bg="lightcoral", font=default_font, width=5, height=1)
        btn_delete.pack(side=tk.LEFT, padx=8)
        try:
            self.add_tooltip(btn_delete, '選択した日程を削除します')
        except Exception:
            pass

        btn_order = tk.Button(btn_frame, text="出演順設定エリアを表示", command=self.show_order_area, bg="lightblue", font=("Meiryo", 12, "bold"), width=20, height=1)
        btn_order.pack(side=tk.LEFT, padx=8)
        try:
            self.add_tooltip(btn_order, '出演順を設定するエリアを表示します')
        except Exception:
            pass

    def show_order_area(self):
        if not self.schedules:
            messagebox.showinfo("出演順設定", "日程を1つ以上追加してください", parent=self)
            return
        # トップ画面（ウィジェット）を非表示
        self.hidden_widgets = []
        for widget in self.top_widgets:
            if widget.winfo_ismapped():
                widget.pack_forget()
                self.hidden_widgets.append(widget)
        # 既存のorder_areaがあれば削除
        if self.order_area:
            self.order_area.destroy()
        self.order_area = tk.Frame(self)
        self.order_area.pack(fill=tk.BOTH, expand=True)
        self.create_order_area()

    def back_to_top(self):
        # 出演順設定エリアを非表示
        if self.order_area:
            self.order_area.destroy()
            self.order_area = None
        # トップ画面（ウィジェット）を再表示（pack_forgetしたものだけ、元の配置で）
        if len(self.top_widgets) >= 3:
            # frame（日程追加）
            self.top_widgets[0].pack(pady=10, padx=10, fill=tk.X, anchor="w")
            # list_frame（日程リスト）
            self.top_widgets[1].pack(pady=10, padx=10, fill=tk.BOTH, expand=True, anchor="w")
            # btn_frame（ボタンエリア）
            self.top_widgets[2].pack(pady=10, anchor="w")
        self.hidden_widgets = []
        self.order_area = None
        # トップ画面（ウィジェット）を再表示（元のpack順で）
        for widget in self.top_widgets:
            widget.pack()

    def create_order_area(self):
        # order.pyのUIを再現
        menu_frame = tk.Frame(self.order_area)
        menu_frame.pack(fill=tk.X, padx=10, pady=3)
        btn_save = tk.Button(menu_frame, text="保存", command=self.save_schedule, font=("Meiryo", 12), width=7, height=1)
        btn_save.pack(side=tk.LEFT, padx=10)
        try:
            self.add_tooltip(btn_save, '現在のタイムテーブルを保存します')
        except Exception:
            pass
        btn_load = tk.Button(menu_frame, text="読み込み", command=self.load_schedule, font=("Meiryo", 12), width=7, height=1)
        btn_load.pack(side=tk.LEFT, padx=10)
        try:
            self.add_tooltip(btn_load, '保存済みのタイムテーブルを読み込みます')
        except Exception:
            pass
        btn_export_pdf = tk.Button(menu_frame, text="PDF出力", command=self.export_pdf, font=("Meiryo", 12), width=8, height=1, bg="#ff417a")
        btn_export_pdf.pack(side=tk.LEFT, padx=10)
        try:
            self.add_tooltip(btn_export_pdf, '現在のタイムテーブルをPDFで出力します')
        except Exception:
            pass
        btn_export_excel = tk.Button(menu_frame, text="Excel出力(おすすめ)", command=self.export_excel, font=("Meiryo", 12), width=16, height=1, bg="#07ca6f")
        btn_export_excel.pack(side=tk.LEFT, padx=10)
        try:
            self.add_tooltip(btn_export_excel, '現在のタイムテーブルをExcelで出力します')
        except Exception:
            pass
        # オプションボタン追加
        btn_option = tk.Button(menu_frame, text="絞り込み", command=self.show_option_dialog, font=("Meiryo", 12), width=8, height=1, bg="#fff9c4")
        btn_option.pack(side=tk.LEFT, padx=10)
        try:
            self.add_tooltip(btn_option, 'バンドの絞り込み条件を設定します')
        except Exception:
            pass
        # 「日程設定に戻る」赤色ボタン
        btn_back = tk.Button(menu_frame, text="日程設定に戻る", command=self.back_to_top, font=("Meiryo", 12, "bold"), width=12, height=1, bg="red", fg="white")
        btn_back.pack(side=tk.RIGHT, padx=10)
        try:
            self.add_tooltip(btn_back, 'トップ画面に戻ります')
        except Exception:
            pass

        self.tab_control = ttk.Notebook(self.order_area)
        self.tab_control.pack(expand=True, fill="both")
        self.tabs = {}
        self.used_band_names = set()  # ここで必ずリセット
        self.create_tabs()

    def show_option_dialog(self):
        win = tk.Toplevel(self)
        win.title("絞り込みオプション")
        win.geometry("320x200")
        labels = ["オプション1", "オプション2", "オプション3"]
        entries = {}
        for i, opt in enumerate(labels):
            tk.Label(win, text=opt, font=("Meiryo", 11)).grid(row=i, column=0, padx=8, pady=8, sticky="e")
            ent = tk.Entry(win, width=18, font=("Meiryo", 11))
            ent.insert(0, self.filter_options.get(opt, ''))
            ent.grid(row=i, column=1, padx=8, pady=8)
            entries[opt] = ent
        def on_ok():
            for opt in labels:
                self.filter_options[opt] = entries[opt].get().strip()
            win.destroy()
            for tab in self.tabs:
                self.refresh_combo(tab)
        def on_clear():
            for opt in labels:
                self.filter_options[opt] = ''
                entries[opt].delete(0, tk.END)
            win.destroy()
            for tab in self.tabs:
                self.refresh_combo(tab)
        btn_ok = tk.Button(win, text="OK", command=on_ok, font=("Meiryo", 11), width=8, bg="#c8e6c9")
        btn_ok.grid(row=4, column=0, pady=12)
        try:
            self.add_tooltip(btn_ok, '絞り込み条件を適用します')
        except Exception:
            pass
        btn_clear = tk.Button(win, text="全解除", command=on_clear, font=("Meiryo", 11), width=8, bg="#ffcdd2")
        btn_clear.grid(row=4, column=1, pady=12)
        try:
            self.add_tooltip(btn_clear, '絞り込み条件を全て解除します')
        except Exception:
            pass

        """
        self.tab_control = ttk.Notebook(self.order_area)
        self.tab_control.pack(expand=True, fill="both")
        self.tabs = {}
        self.used_band_names = set()
        self.create_tabs()
        """

    def load_band_infos_from_csv(self, csv_path):
        band_list = []
        try:
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    name = row["バンド名"].strip()
                    minutes = int(row["演奏時間"].strip())
                    dates_str = row["出演日"].strip()
                    date_list = []
                    for part in dates_str.split(";"):
                        try:
                            date = datetime.strptime(part.strip(), "%Y-%m-%d").date()
                            date_list.append(date)
                        except ValueError:
                            pass
                    # オプション列も格納（stripで空白除去）
                    options = {k: row.get(k, '').strip() for k in ["オプション1", "オプション2", "オプション3"]}
                    other = row.get("その他", '').strip()
                    # available_datesは必ずdate型リストに
                    band = BandInfo(name, minutes, [d for d in date_list if isinstance(d, type(datetime.now().date()))])
                    band.options = options
                    band.other = other
                    band_list.append(band)
        except Exception:
            pass
        return band_list

    def create_tabs(self):
        for sched in self.schedules:
            tab = ttk.Frame(self.tab_control)
            label_text = sched['date'].strftime("%m/%d")
            self.tab_control.add(tab, text=label_text)
            top_frame = tk.Frame(tab)
            top_frame.pack(fill=tk.X, padx=10, pady=5)
            label = tk.Label(top_frame, text="バンドを選択：", font=("Meiryo", 12))
            label.pack(side=tk.LEFT)
            combo = ttk.Combobox(top_frame, width=25, state="readonly")
            combo.pack(side=tk.LEFT, padx=5)
            btn_add = tk.Button(top_frame, text="追加", command=lambda c=combo, t=tab: self.add_band(c, t), font=("Meiryo", 12, "bold"), width=8, height=1, bg="#e0f7fa")
            btn_add.pack(side=tk.LEFT, padx=5)
            btn_special = tk.Button(top_frame, text="特別枠追加", command=lambda t=tab: self.add_special_frame(t), font=("Meiryo", 12), width=12, height=1, bg="#ffe0b2")
            btn_special.pack(side=tk.LEFT, padx=5)
            label_info = tk.Label(top_frame, text="バンド名をクリックして\nバンド情報を表示", font=("Meiryo", 12))
            label_info.pack(side=tk.LEFT, padx=5)
            canvas = tk.Canvas(tab, borderwidth=0, background="#f8f8f8")
            frame_container = tk.Frame(canvas, background="#f8f8f8")
            vsb = tk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            canvas.create_window((0, 0), window=frame_container, anchor="nw")
            def on_frame_configure(event, c=canvas, f=frame_container):
                c.configure(scrollregion=c.bbox("all"))
            frame_container.bind("<Configure>", on_frame_configure)
            available_bands = [b for b in self.band_data if sched['date'] in b.available_dates]
            combo["values"] = [b.name for b in available_bands]  # 初期値を必ずセット
            self.tabs[tab] = {
                "combo": combo,
                "frame": frame_container,
                "bands": [],
                "band_objs": available_bands,
                "canvas": canvas,
                "scrollbar": vsb,
                "tab_label": label_text
            }

    # --- ツールチップ補助 ---
    def add_tooltip(self, widget, text, delay=300):
        """ウィジェットにツールチップを追加（操作支援が有効なときのみ表示）。"""
        def on_enter(event):
            try:
                # TopWindowは親の設定に従う（AttendanceApp が設定している場合）
                parent = self.master
                op = True
                try:
                    op = getattr(parent, 'settings', {}).get('operation_support', True)
                except Exception:
                    op = True
                if not op:
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
            tw = tk.Toplevel(self)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            lbl = tk.Label(tw, text=text, font=("Meiryo", 10), bg='#ffffe0', justify='left', relief='solid', bd=1)
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

    def add_band(self, combo, tab):
        band_name = combo.get()
        if not band_name:
            return
        tab_info = self.tabs[tab]
        if any(b['type']=='band' and b['name']==band_name for b in tab_info["bands"]):
            messagebox.showwarning("重複追加", f"{band_name} はすでに他の日程で追加されています。", parent=self)
            return
        band = self.find_band_by_name(band_name, tab_info["band_objs"])
        if not band:
            messagebox.showerror("エラー", "バンド情報が見つかりません", parent=self)
            return
        tab_info["bands"].append({'type': 'band', 'name': band_name, 'minutes': band.performance_minutes})
        self.used_band_names.add(band_name)
        for t in self.tabs.keys():
            self.refresh_combo(t)
        self.update_band_frames(tab)

    def add_special_frame(self, tab):
        def on_ok():
            kind = var_kind.get()
            try:
                minutes = int(entry_min.get())
            except ValueError:
                messagebox.showerror("エラー", "分数は整数で入力してください", parent=self)
                return
            if kind == 'リハ':
                band_name = combo_band.get().strip()
                if not band_name:
                    messagebox.showerror("エラー", "バンド名を選択してください", parent=self)
                    return
                item = {'type': 'rehearsal', 'name': band_name, 'minutes': minutes}
            elif kind == '休憩':
                item = {'type': 'break', 'minutes': minutes}
            elif kind == '転換':
                item = {'type': 'change', 'minutes': minutes}
            else:
                return
            self.tabs[tab]["bands"].append(item)
            win.destroy()
            self.update_band_frames(tab)
        win = tk.Toplevel(self)
        win.title("特別枠追加")
        win.geometry("300x150")
        tk.Label(win, text="種別").grid(row=0, column=0)
        var_kind = tk.StringVar(value='休憩')
        kinds = ['休憩', '転換', 'リハ']
        combo_kind = ttk.Combobox(win, values=kinds, textvariable=var_kind, state="readonly", width=8, justify='center')
        combo_kind.grid(row=0, column=1, padx=5, pady=2)
        combo_kind.configure(justify='center')
        tk.Label(win, text="分数").grid(row=1, column=0)
        entry_min = tk.Entry(win, width=8, justify='center')
        entry_min.grid(row=1, column=1, padx=5, pady=2)
        tk.Label(win, text="バンド名(リハのみ)").grid(row=2, column=0)
        all_band_names = [b.name for b in self.tabs[tab]['band_objs']]
        combo_band = ttk.Combobox(win, values=all_band_names, state="readonly", width=18, justify='center')
        combo_band.grid(row=2, column=1, padx=5, pady=2)
        combo_band.configure(justify='center')
        btn = tk.Button(win, text="OK", command=on_ok)
        btn.grid(row=3, column=0, columnspan=2, pady=5)
        try:
            self.add_tooltip(btn, '特別枠を追加します')
        except Exception:
            pass
        def on_kind_change(event=None):
            kind = var_kind.get()
            if kind == 'リハ':
                combo_band.config(state='normal')
                combo_band.config(state='readonly')
            else:
                combo_band.set("")
                combo_band.config(state='disabled')
        combo_kind.bind('<<ComboboxSelected>>', on_kind_change)
        # 初期状態反映
        on_kind_change()

    def transfer_data(self):
            # ①インストール有無確認
            result = messagebox.askyesno("確認", "引き継ぎ先のコンピュータに出席管理システムがインストールされていますか？", parent=self)
            if result:
                # ①-1 Yesの場合：編集中データを保存してからデータコピー
                self.save_schedule()  # 日程・出演順データを保存
                import shutil
                import pathlib
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                target_dir = os.path.join(desktop, '【ロック部出席管理】引き継ぎデータ')
                os.makedirs(target_dir, exist_ok=True)
                files = [
                    os.path.join(os.path.dirname(sys.argv[0]), 'attend_data.xlsx'),
                    os.path.join(os.path.dirname(sys.argv[0]), 'bands.csv'),
                    os.path.join(os.path.dirname(sys.argv[0]), 'schedule_data.json'),
                ]
                copied = []
                for f in files:
                    if os.path.exists(f):
                        shutil.copy2(f, target_dir)
                        copied.append(os.path.basename(f))
                msg = f"編集中の日程・出演順データを保存し、引き継ぎデータをデスクトップの『【ロック部出席管理】引き継ぎデータ』フォルダに保存しました。\n\n" \
                      f"引き継ぎ先のコンピュータにこのフォルダごと移動すると引き継ぎが完了します。\n\n" \
                      f"保存ファイル: {', '.join(copied)}"
                messagebox.showinfo("引き継ぎ完了", msg, parent=self)
            else:
                # ①-2 Noの場合：インストール案内
                messagebox.showinfo("案内", "引き継ぎ先のコンピュータにソフトウェアをインストールしてから引き継ぎを行ってください。", parent=self)

    def update_band_frames(self, tab):
        tab_info = self.tabs[tab]
        frame = tab_info["frame"]
        for widget in frame.winfo_children():
            widget.destroy()
        sched = None
        tab_label = tab_info.get("tab_label")
        for s in self.schedules:
            if s['date'].strftime("%m/%d") == tab_label:
                sched = s
                break
        if not sched:
            return
        end_time_limit = datetime.strptime(sched['end'], "%H:%M")
        current_time = datetime.strptime(sched['start'], "%H:%M")
        for idx, item in enumerate(tab_info["bands"]):
            if item['type'] == 'band':
                name = item['name']
                minutes = item['minutes']
                label_text = f"{name}（{minutes}分）"
                # バンド情報取得
                band_info = self.find_band_by_name(name, self.band_data)
                def show_band_info(event, band_info=band_info):
                    if band_info:
                        info = f"バンド名: {band_info.name}\n演奏時間: {band_info.performance_minutes}分\n出演日: {', '.join([d.strftime('%Y-%m-%d') for d in band_info.available_dates])}"
                        # オプション表示
                        if hasattr(band_info, 'options'):
                            for k, v in band_info.options.items():
                                info += f"\n{k}: {v}"
                        # その他表示
                        if hasattr(band_info, 'other') and band_info.other:
                            info += f"\nその他: {band_info.other}"
                        messagebox.showinfo("バンド情報", info, parent=self)
                # ラベル生成後にイベントバインド
            elif item['type'] == 'break':
                name = None
                minutes = item['minutes']
                label_text = f"休憩（{minutes}分）"
            elif item['type'] == 'change':
                name = None
                minutes = item['minutes']
                label_text = f"転換（{minutes}分）"
            elif item['type'] == 'rehearsal':
                name = item['name']
                minutes = item['minutes']
                label_text = f"リハ（{name}）（{minutes}分）"
            else:
                continue
            start_str = current_time.strftime("%H:%M")
            end_time = current_time + timedelta(minutes=minutes)
            end_str = end_time.strftime("%H:%M")
            # 背景色判定
            bg_color = None
            # バンド枠のみ「その他」判定
            if item['type'] == 'band' and band_info is not None:
                other_val = getattr(band_info, 'other', None)
                # nan判定（str型で"nan"やNone、空文字は除外）
                if other_val is not None and str(other_val).lower() != 'nan' and str(other_val).strip() != '':
                    bg_color = '#b2ebf2'  # 水色
            # 超過判定（バンド以外も）
            if bg_color is None and end_time > end_time_limit:
                bg_color = '#fff59d'  # 黄色
            wrapper = tk.Frame(frame, bd=1, relief="solid", padx=5, pady=5, width=776, height=36, bg=bg_color)
            wrapper.pack(fill=tk.X, expand=True, pady=2)
            wrapper.pack_propagate(False)
            label = tk.Label(wrapper, text=f"{start_str}～{end_str} {label_text}", anchor="w", font=("Meiryo", 12, "bold"), bg=bg_color)
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            # バンド枠のみクリックで情報表示
            if item['type'] == 'band':
                label.bind('<Button-1>', show_band_info)
            btn_del = tk.Button(wrapper, text="×", width=3, fg="red", font=("Meiryo", 12))
            btn_del.pack(side=tk.RIGHT)
            btn_down = tk.Button(wrapper, text="↓", width=2, font=("Meiryo", 12))
            btn_down.pack(side=tk.RIGHT, padx=2)
            btn_up = tk.Button(wrapper, text="↑", width=2, font=("Meiryo", 12))
            btn_up.pack(side=tk.RIGHT, padx=2)
            def remove_item(idx=idx):
                removed = tab_info["bands"][idx]
                del tab_info["bands"][idx]
                if removed.get("type") == "band":
                    self.used_band_names.discard(removed["name"])
                    for t in self.tabs:
                        self.refresh_combo(t)
                self.update_band_frames(tab)
            btn_up.config(command=lambda idx=idx: self.move_band(tab, idx, -1))
            btn_down.config(command=lambda idx=idx: self.move_band(tab, idx, 1))
            btn_del.config(command=remove_item)
            if end_time > end_time_limit:
                warn = tk.Label(wrapper, text="時刻超過", fg="black", font=("Meiryo", 10, "bold"), bg='#fff59d')
                warn.pack(side=tk.BOTTOM, fill=tk.X, pady=2)
            current_time = end_time

    def move_band(self, tab, idx, direction):
        tab_info = self.tabs[tab]
        new_idx = idx + direction
        if 0 <= new_idx < len(tab_info["bands"]):
            tab_info["bands"][idx], tab_info["bands"][new_idx] = tab_info["bands"][new_idx], tab_info["bands"][idx]
            self.update_band_frames(tab)

    def refresh_combo(self, tab):
        tab_info = self.tabs[tab]
        used_names = self.used_band_names
        # オプションフィルタ
        def match_option(band):
            for opt, val in self.filter_options.items():
                v = val.strip()
                if v == '':
                    continue  # 空欄はフィルタしない
                band_opt = band.options.get(opt, '').strip() if hasattr(band, 'options') else ''
                if band_opt != v:
                    return False
            return True
        filtered = [b.name for b in tab_info["band_objs"] if b.name not in used_names and match_option(b)]
        # オプション全空欄時は全バンドを候補に
        if all(v.strip() == '' for v in self.filter_options.values()):
            filtered = [b.name for b in tab_info["band_objs"] if b.name not in used_names]
        tab_info["combo"]["values"] = filtered
        if filtered:
            tab_info["combo"].current(0)
        else:
            tab_info["combo"].set("")

    def find_band_by_name(self, name, band_list):
        for b in band_list:
            if b.name == name:
                return b
        return None

    def save_schedule(self):
        data = {
            "schedules": [
                {
                    "date": s['date'].strftime("%Y-%m-%d"),
                    "start_time": s['start'],
                    "end_time": s['end']
                } for s in self.schedules
            ],
            "bands": {
                tabinfo.get("tab_label", str(i)): tabinfo["bands"]
                for i, (tab, tabinfo) in enumerate(self.tabs.items())
            }
        }
        try:
            json_path = self.get_json_path()
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("保存", "スケジュールを保存しました。", parent=self)
        except Exception as e:
                messagebox.showerror("保存エラー", str(e), parent=self)

    def load_schedule(self):
        try:
            json_path = self.get_json_path()
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("読み込みエラー", str(e), parent=self)
            return
        date2tab = {tabinfo.get("tab_label"): tab for tab, tabinfo in self.tabs.items()}
        bands_data = data.get("bands", {})
        self.used_band_names.clear()
        for tab_label, bands in bands_data.items():
            tab = date2tab.get(tab_label)
            if tab:
                self.tabs[tab]["bands"] = bands
        for tab in self.tabs:
            for b in self.tabs[tab]["bands"]:
                if b.get("type") == "band":
                    self.used_band_names.add(b["name"])
        for tab in self.tabs:
            self.refresh_combo(tab)
            self.update_band_frames(tab)
            messagebox.showinfo("読み込み", "スケジュールを読み込みました。", parent=self)

    def export_excel(self):
        try:
            import openpyxl
            from openpyxl.styles import PatternFill, Font, Alignment
        except ImportError:
            messagebox.showerror("Excel出力エラー", "openpyxlライブラリが必要です。\npip install openpyxl でインストールしてください。", parent=self)
            return
        # Excel出力前に Meiryo フォントファイルが必要か確認（なければシステムからコピーを試みる）
        font_file = os.path.join(os.path.dirname(__file__), "meiryo.ttc")
        if not os.path.exists(font_file):
            # コピーに失敗したら処理中止
            if not self._ensure_font_file("meiryo.ttc", "Meiryo"):
                return

        wb = openpyxl.Workbook()
        for tab, tabinfo in self.tabs.items():
            tab_title = tabinfo.get("tab_label")
            safe_title = tab_title.replace("/", "-")
            ws = wb.create_sheet(title=safe_title)
            ws.append(["開始時刻", "～", "終了時刻", "枠の名前"])
            # ヘッダにメイリオフォントを設定
            header_font = Font(name="Meiryo", size=12, bold=True)
            for col in range(1, 5):
                ws.cell(row=ws.max_row, column=col).font = header_font
            for idx, item in enumerate(tabinfo["bands"]):
                sched = None
                for s in self.schedules:
                    if s['date'].strftime("%m/%d") == tabinfo.get("tab_label"):
                        sched = s
                        break
                if not sched:
                    continue
                current_time = datetime.strptime(sched['start'], "%H:%M")
                for i in range(idx):
                    current_time += timedelta(minutes=tabinfo["bands"][i]["minutes"])
                start_str = current_time.strftime("%H:%M")
                end_time = current_time + timedelta(minutes=item["minutes"])
                end_str = end_time.strftime("%H:%M")
                name = item.get("name") if item.get("type") != "break" and item.get("type") != "change" else None
                if item["type"] == "band":
                    row = [start_str, "～", end_str, name]
                    ws.append(row)
                    for col in range(1, 5):
                        ws.cell(row=ws.max_row, column=col).fill = PatternFill(fill_type=None)
                        ws.cell(row=ws.max_row, column=col).font = Font(name="Meiryo", size=11, color="000000")
                else:
                    if item["type"] == "break":
                        disp_name = f"休憩（{item['minutes']}分）"
                    elif item["type"] == "change":
                        disp_name = f"転換（{item['minutes']}分）"
                    elif item["type"] == "rehearsal":
                        disp_name = f"リハ（{item['name']}）（{item['minutes']}分）"
                    else:
                        disp_name = ""
                    row = [start_str, "～", end_str, disp_name]
                    ws.append(row)
                    for col in range(1, 5):
                        ws.cell(row=ws.max_row, column=col).fill = PatternFill(start_color="888888", end_color="888888", fill_type="solid")
                        ws.cell(row=ws.max_row, column=col).font = Font(name="Meiryo", size=11, color="FFFFFF")
                for col in range(1, 5):
                    ws.cell(row=ws.max_row, column=col).alignment = Alignment(horizontal="left", vertical="center")
            ws.column_dimensions["A"].width = 10
            ws.column_dimensions["B"].width = 4
            ws.column_dimensions["C"].width = 10
            ws.column_dimensions["D"].width = 24
        if "Sheet" in wb.sheetnames:
            del wb["Sheet"]
        try:
            wb.save("タイムテーブル.xlsx")
            msg = "タイムテーブル.xlsx を出力しました。"
            if getattr(self, '_last_font_copied', False):
                msg += "\n※フォントファイルコピー済み"
            messagebox.showinfo("Excel出力", msg, parent=self)
            self._last_font_copied = False
        except Exception as e:
            messagebox.showerror("Excel出力エラー", str(e), parent=self)

    def export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.colors import black, white, HexColor
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            font_path = os.path.join(os.path.dirname(__file__), "meiryo.ttc")
            if not os.path.exists(font_path):
                # システムフォントからコピーを試みる
                if not self._ensure_font_file("meiryo.ttc", "Meiryo"):
                    return
            pdfmetrics.registerFont(TTFont("meiryo", font_path))
        except ImportError:
            messagebox.showerror("PDF出力エラー", "reportlabライブラリが必要です。\npip install reportlab でインストールしてください。", parent=self)
            return
        try:
            c = canvas.Canvas("タイムテーブル.pdf", pagesize=A4)
            width, height = A4
            y_start = height - 50
            for tab, tabinfo in self.tabs.items():
                c.setFont("meiryo", 16)
                c.drawString(50, y_start, f"日程: {tabinfo.get('tab_label')}")
                y = y_start - 30
                c.setFont("meiryo", 12)
                for idx, item in enumerate(tabinfo["bands"]):
                    sched = None
                    for s in self.schedules:
                        if s['date'].strftime("%m/%d") == tabinfo.get("tab_label"):
                            sched = s
                            break
                    if not sched:
                        continue
                    current_time = datetime.strptime(sched['start'], "%H:%M")
                    for i in range(idx):
                        current_time += timedelta(minutes=tabinfo["bands"][i]["minutes"])
                    start_str = current_time.strftime("%H:%M")
                    end_time = current_time + timedelta(minutes=item["minutes"])
                    end_str = end_time.strftime("%H:%M")
                    if item["type"] == "band":
                        c.setFillColor(white)
                        c.setStrokeColor(black)
                        c.rect(45, y-2, 340, 22, fill=1, stroke=0)
                        c.setFillColor(black)
                        c.drawString(50, y, start_str)
                        c.drawString(120, y, "～")
                        c.drawString(160, y, end_str)
                        c.drawString(250, y, item["name"])
                    else:
                        if item["type"] == "break":
                            disp_name = f"休憩（{item['minutes']}分）"
                        elif item["type"] == "change":
                            disp_name = f"転換（{item['minutes']}分）"
                        elif item["type"] == "rehearsal":
                            disp_name = f"リハ（{item['name']}）（{item['minutes']}分）"
                        else:
                            disp_name = ""
                        c.setFillColor(HexColor("#888888"))
                        c.setStrokeColor(black)
                        c.rect(45, y-2, 340, 22, fill=1, stroke=0)
                        c.setFillColor(white)
                        c.drawString(50, y, start_str)
                        c.drawString(120, y, "～")
                        c.drawString(160, y, end_str)
                        c.drawString(250, y, disp_name)
                    y -= 24
                y_start = y - 40
                c.showPage()
            c.save()
            msg = "タイムテーブル.pdf を出力しました。"
            if getattr(self, '_last_font_copied', False):
                msg += "\n※フォントファイルコピー済み"
            messagebox.showinfo("PDF出力", msg, parent=self)
            self._last_font_copied = False
        except Exception as e:
            messagebox.showerror("PDF出力エラー", str(e), parent=self)

    def time_options(self):
        return [f"{h:02d}:{m:02d}" for h in range(8, 21) for m in (0, 30)]

    def add_schedule(self):
        date = self.date_entry.get_date()
        start = self.start_time.get()
        end = self.end_time.get()

        # --- フォーマットチェック ---
        if not self.is_valid_time_format(start) or not self.is_valid_time_format(end):
            messagebox.showerror("エラー", "開始時刻・終了時刻はHH:MM形式で入力してください", parent=self)
            return

        # --- 時刻の前後チェック ---
        start_dt = datetime.strptime(start, "%H:%M")
        end_dt = datetime.strptime(end, "%H:%M")
        if end_dt <= start_dt:
            messagebox.showerror("エラー", "終了時刻は開始時刻より後にしてください", parent=self)
            return

        # --- 日付の重複チェック ---
        for s in self.schedules:
            if s['date'] == date:
                messagebox.showwarning("重複", "同じ日付が既に追加されています", parent=self)
                return

        # --- 登録 ---
        self.schedules.append({
            "date": date,
            "start": start,
            "end": end
        })

        self.update_listbox()

    def delete_schedule(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("削除", "削除する日程を選択してください", parent=self)
            return

        index = selected[0]
        del self.schedules[index]
        self.update_listbox()

    def edit_schedule(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("編集", "編集する日程を選択してください", parent=self)
            return
        idx = selected[0]
        s = self.schedules[idx]
        edit_win = tk.Toplevel(self)
        edit_win.title("日程編集")
        edit_win.geometry("300x200")
        tk.Label(edit_win, text="日付：").grid(row=0, column=0, padx=10, pady=10)
        date_entry = DateEntry(edit_win, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        date_entry.set_date(s['date'])
        date_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Label(edit_win, text="開始時刻：").grid(row=1, column=0, padx=10, pady=10)
        start_combo = ttk.Combobox(edit_win, values=self.time_options(), width=10, state="normal")
        start_combo.set(s['start'])
        start_combo.grid(row=1, column=1, padx=10, pady=10)
        tk.Label(edit_win, text="終了時刻：").grid(row=2, column=0, padx=10, pady=10)
        end_combo = ttk.Combobox(edit_win, values=self.time_options(), width=10, state="normal")
        end_combo.set(s['end'])
        end_combo.grid(row=2, column=1, padx=10, pady=10)
        def save_edit():
            new_date = date_entry.get_date()
            new_start = start_combo.get()
            new_end = end_combo.get()
            # フォーマット・前後チェック
            if not self.is_valid_time_format(new_start) or not self.is_valid_time_format(new_end):
                messagebox.showerror("エラー", "開始時刻・終了時刻はHH:MM形式で入力してください", parent=self)
                return
            start_dt = datetime.strptime(new_start, "%H:%M")
            end_dt = datetime.strptime(new_end, "%H:%M")
            if end_dt <= start_dt:
                messagebox.showerror("エラー", "終了時刻は開始時刻より後にしてください", parent=self)
                return
            # 日付重複チェック（自分以外）
            for i, ss in enumerate(self.schedules):
                if i != idx and ss['date'] == new_date:
                    messagebox.showwarning("重複", "同じ日付が既に追加されています", parent=self)
                    return
            # 反映
            self.schedules[idx] = {"date": new_date, "start": new_start, "end": new_end}
            self.update_listbox()
            edit_win.destroy()
        btn_save = tk.Button(edit_win, text="保存", command=save_edit, bg="#e0f7fa", font=("Meiryo", 12, "bold"))
        btn_save.grid(row=3, column=0, columnspan=2, pady=20)

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for s in self.schedules:
            date_str = s['date'].strftime('%Y-%m-%d')
            self.listbox.insert(tk.END, f"{date_str} / {s['start']}～{s['end']}")

    def is_valid_time_format(self, time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False

    def load_schedules(self):
        try:
            json_path = self.get_json_path()
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("読み込みエラー", str(e), parent=self)
            return
        self.schedules.clear()
        for s in data.get("schedules", []):
            try:
                d = datetime.strptime(s["date"], "%Y-%m-%d").date()
                start = s["start_time"] if "start_time" in s else s["start"]
                end = s["end_time"] if "end_time" in s else s["end"]
                self.schedules.append({"date": d, "start": start, "end": end})
            except Exception:
                continue
        self.update_listbox()
        messagebox.showinfo("読み込み", "日程を読み込みました。", parent=self)


# 起動
if __name__ == "__main__":
    app = TopWindow()
    app.mainloop()
