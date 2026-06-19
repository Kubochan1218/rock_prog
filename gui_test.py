import customtkinter as ctk

# 全体のテーマとカラーの設定
ctk.set_appearance_mode("Light")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

class K_OnManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ウィンドウ基本設定
        self.title("ロック部出欠管理システム")
        self.geometry("1100x650")

        # -------------------------------------------------------------
        # 1. グリッド配置の設定（左メニュー用と右コンテンツ用）
        # -------------------------------------------------------------
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # =============================================================
        # 2. 左側：サイドメニュー（ナビゲーション）
        # =============================================================
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)  # 設定ボタンを下に押し下げるため

        # アプリタイトルロゴ風
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🎸 ロック部出欠管理システム", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        # メニューボタン群
        self.btn_dash = ctk.CTkButton(self.sidebar_frame, text="🏠 ダッシュボード", fg_color="gray30", anchor="w")
        self.btn_dash.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_member = ctk.CTkButton(self.sidebar_frame, text="👥 出欠管理", fg_color="transparent", text_color=("gray10", "gray90"), anchor="w")
        self.btn_member.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_live = ctk.CTkButton(self.sidebar_frame, text="📅 ライブ管理", fg_color="transparent", text_color=("gray10", "gray90"), anchor="w")
        self.btn_live.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_band = ctk.CTkButton(self.sidebar_frame, text="🎤 バンド登録・選出", fg_color="transparent", text_color=("gray10", "gray90"), anchor="w")
        self.btn_band.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_timetable = ctk.CTkButton(self.sidebar_frame, text="⏱️ タイムテーブル", fg_color="transparent", text_color=("gray10", "gray90"), anchor="w")
        self.btn_timetable.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        # 下部の設定ボタン
        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="⚙️ 設定", fg_color="transparent", text_color=("gray10", "gray90"), anchor="w")
        self.btn_settings.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # =============================================================
        # 3. 右側：メインコンテンツエリア
        # =============================================================
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # -------------------------------------------------------------
        # 上段：イベント概要情報
        # -------------------------------------------------------------
        self.header_label = ctk.CTkLabel(self.main_frame, text="Welcome, Admin! 対象イベント: 夏合宿ライブ2026", font=ctk.CTkFont(size=22, weight="bold"))
        self.header_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # プログレスバー（進行状況）
        self.progress_label = ctk.CTkLabel(self.main_frame, text="現在のフェーズ: バンド選出・タイテ作成中 (進捗: 85%)", font=ctk.CTkFont(size=13))
        self.progress_label.grid(row=1, column=0, columnspan=2, padx=10, sticky="w")
        
        self.progressbar = ctk.CTkProgressBar(self.main_frame)
        self.progressbar.grid(row=2, column=0, columnspan=2, padx=10, pady=(5, 20), sticky="ew")
        self.progressbar.set(0.85)

        # -------------------------------------------------------------
        # 中段左側：バンドエントリー状況カード
        # -------------------------------------------------------------
        self.band_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="🎸 エントリー・選出状況 (総数: 12)")
        self.band_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        
        # サンプルバンドデータ表示
        bands = [
            ("The Beginners (4名)", "確定", "green"),
            ("けいおん部A (3名)", "確定", "green"),
            ("OB・OGバンド (5名)", "保留・要確認", "orange")
        ]
        for name, status, color in bands:
            lbl = ctk.CTkLabel(self.band_frame, text=f" 【{status}】 {name}", anchor="w", text_color=color)
            lbl.pack(fill="x", padx=10, pady=5)

        # バンド登録ボタン
        self.btn_reg_band = ctk.CTkButton(self.main_frame, text="➕ 新しいバンドを登録する", command=self.open_band_registration)
        self.btn_reg_band.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        # -------------------------------------------------------------
        # 中段右側：タイムテーブルプレビューカード
        # -------------------------------------------------------------
        self.time_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="⏱️ タイムテーブル (下書き)")
        self.time_frame.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        timelines = [
            "12:00 〜 開場 / ドアオープン",
            "12:30 〜 O.A (1年生バンド)",
            "13:00 〜 The Beginners",
            "13:40 〜 けいおん部A"
        ]
        for item in timelines:
            lbl = ctk.CTkLabel(self.time_frame, text=item, anchor="w")
            lbl.pack(fill="x", padx=10, pady=5)

        # タイテ編集ボタン
        self.btn_edit_time = ctk.CTkButton(self.main_frame, text="✏️ タイムテーブルを編集する")
        self.btn_edit_time.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        # -------------------------------------------------------------
        # 下段：出欠未回答者・タスクエリア
        # -------------------------------------------------------------
        self.task_frame = ctk.CTkFrame(self.main_frame)
        self.task_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        
        self.attendance_label = ctk.CTkLabel(self.task_frame, text="👥 出欠未回答者（催促連絡用）: 山田太郎, 佐藤花子, 鈴木一郎 ...", anchor="w")
        self.attendance_label.pack(side="left", padx=20, pady=15)

        self.btn_csv = ctk.CTkButton(self.task_frame, text="📊 CSV出力", width=100)
        self.btn_csv.pack(side="right", padx=20, pady=15)

    # 「新しいバンドを登録する」を押したときの仮のアクション
    def open_band_registration(self):
        print("バンド登録画面を開きます（ここに登録用のポップアップなどの処理を書く）")

if __name__ == "__main__":
    app = K_OnManagerApp()
    app.mainloop()