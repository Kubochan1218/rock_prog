import customtkinter as ctk

# 基本設定（サークルのテーマに合わせる）
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 
FONT_NAME = "Yu Gothic" # Windowsの場合は記法に合わせて自動フォールバックされます

class DashboardMock(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ダッシュボードイメージ確認")
        self.geometry("900x700")

        # 全体をスクロール可能にするメイン枠
        main_scroll = ctk.CTkScrollableFrame(self)
        main_scroll.pack(fill="both", expand=True, padx=15, pady=15)

        # 1. 歓迎メッセージ
        welcome_lbl = ctk.CTkLabel(main_scroll, text="👋 ようこそ、幹部管理ページへ！", font=(FONT_NAME, 20, "bold"))
        welcome_lbl.pack(pady=(10, 5), anchor="w", padx=10)
        
        sub_lbl = ctk.CTkLabel(main_scroll, text="サークルの現在のステータスと次のタスクです。", font=(FONT_NAME, 14), text_color="gray")
        sub_lbl.pack(pady=(0, 15), anchor="w", padx=10)

        # 2. 中段：カードを2つ横に並べるためのコンテナ（packのside='left'を利用）
        card_container = ctk.CTkFrame(main_scroll, fg_color="transparent")
        card_container.pack(fill="x", pady=10)

        # --- 左カード：ライブ＆応募状況 ---
        live_card = ctk.CTkFrame(card_container, fg_color=("gray85", "gray18"), width=420, height=220)
        live_card.pack(side="left", padx=10, fill="both", expand=True)
        live_card.pack_propagate(False) # 枠のサイズを固定

        ctk.CTkLabel(live_card, text="📅 直近のライブ & 応募状況", font=(FONT_NAME, 16, "bold"), text_color="#80d4ff").pack(pady=10, anchor="w", padx=15)
        ctk.CTkLabel(live_card, text="・次回イベント: 2026 夏ライブ\n・開催日程: 2026/08/15 ～ 08/16", font=(FONT_NAME, 15), justify="left").pack(anchor="w", padx=20, pady=5)
        
        # 強調用のステータス枠
        status_box = ctk.CTkFrame(live_card, fg_color=("gray80", "gray25"), corner_radius=5)
        status_box.pack(fill="x", padx=15, pady=10, ipady=5)
        ctk.CTkLabel(status_box, text="🔥 現在の応募総数: 24 バンド\n (選出完了: 18 / 未選出: 6)", font=(FONT_NAME, 15, "bold"), text_color="#bfff80").pack(pady=5)

        # --- 右カード：出席スタッツ ---
        stats_card = ctk.CTkFrame(card_container, fg_color=("gray85", "gray18"), width=420, height=220)
        stats_card.pack(side="left", padx=10, fill="both", expand=True)
        stats_card.pack_propagate(False)

        ctk.CTkLabel(stats_card, text="📈 サークル全体の出席スタッツ", font=(FONT_NAME, 16, "bold"), text_color="#80d4ff").pack(pady=10, anchor="w", padx=15)
        ctk.CTkLabel(stats_card, text="・直近の練習日出席率:  78 %\n・今期の平均出席率:    82 %\n\n・現在のサークル登録部員数:  65 名", font=(FONT_NAME, 15), justify="left").pack(anchor="w", padx=20, pady=5)

        # 3. 下段：リマインダー（横幅いっぱい）
        remind_card = ctk.CTkFrame(main_scroll, fg_color=("gray85", "gray18"))
        remind_card.pack(fill="x", pady=15, padx=10)
        
        ctk.CTkLabel(remind_card, text="⏳ 期限カウントダウン", font=(FONT_NAME, 16, "bold"), text_color="#ff8080").pack(pady=10, anchor="w", padx=15)
        ctk.CTkLabel(remind_card, text="🔥 夏ライブ本番まで ・・・・・・・・・・・・・・・ あと 35 日\n⚠️ バンド選出・タイムテーブル確定締め切りまで ・・・ あと  5 日", font=(FONT_NAME, 15, "bold"), justify="left").pack(anchor="w", padx=25, pady=(0, 15))

        # 4. 最下段：クイックアクセスボタン
        quick_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        quick_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(quick_frame, text="⚡ クイックアクセス", font=(FONT_NAME, 16, "bold"), pady=5).pack(anchor="w") # pack用に下部マージン意識
        
        btn_box = ctk.CTkFrame(quick_frame, fg_color="transparent")
        btn_box.pack(fill="x", pady=5)
        
        # 3つのボタンを綺麗に横並び
        ctk.CTkButton(btn_box, text="📅 出席を入力", font=(FONT_NAME, 16), height=40).pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(btn_box, text="📥 バンドインポート", font=(FONT_NAME, 16), height=40).pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(btn_box, text="🎸 バンド選出を実行", font=(FONT_NAME, 16), height=40).pack(side="left", expand=True, fill="x", padx=5)

if __name__ == "__main__":
    app = DashboardMock()
    app.mainloop()