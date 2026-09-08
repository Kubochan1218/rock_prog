import customtkinter as ctk
import config
from views.my_parts import MultiFontButton

class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, on_menu_select, app, **kwargs):
        super().__init__(master, width=220, corner_radius=0, **kwargs)
        self.grid_rowconfigure(7, weight=1)

        self.on_menu_select = on_menu_select  # メニュー選択時のコールバック関数
        self.app = app  # アプリケーションインスタンス
        # サークルロゴ/タイトル
        self.logo_label = ctk.CTkLabel(self, text="🎸 ロック部 出席管理", font=ctk.CTkFont(family=config.FONT_NAME, size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=25)
        
        # 常駐ナビゲーションボタン群
        self.btn_nav_top = MultiFontButton(self, icon_text="", label_text="ホーム", anchor="w", fg_color=("#DBDBDB", "#2b2b2b"), command=lambda: on_menu_select("top"))
        self.btn_nav_top.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.btn_nav_attend = MultiFontButton(self, icon_text="", label_text="出欠管理・確認", anchor="w", fg_color=("#DBDBDB", "#2b2b2b"), command=lambda: on_menu_select("attendance"))
        self.btn_nav_attend.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        self.btn_nav_check = MultiFontButton(self, icon_text="", label_text="ライブ管理", anchor="w", fg_color=("#DBDBDB", "#2b2b2b"), command=lambda: on_menu_select("live"))
        self.btn_nav_check.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        self.btn_nav_form = MultiFontButton(self, icon_text="", label_text="バンド募集フォーム作成", anchor="w", fg_color=("#DBDBDB", "#2b2b2b"), command=lambda: on_menu_select("form"))
        self.btn_nav_form.grid(row=4, column=0, padx=5, pady=5, sticky="ew")

        self.btn_nav_band = MultiFontButton(self, icon_text="", label_text="バンド登録・選出", anchor="w", fg_color=("#DBDBDB", "#2b2b2b"), command=lambda: on_menu_select("band"))
        self.btn_nav_band.grid(row=5, column=0, padx=5, pady=5, sticky="ew")
        
        self.btn_nav_select = MultiFontButton(self, icon_text="", label_text="タイムテーブル", anchor="w", fg_color=("#DBDBDB", "#2b2b2b"), command=lambda: on_menu_select("timetable"))
        self.btn_nav_select.grid(row=6, column=0, padx=5, pady=5, sticky="ew")
        
        # 下部の固定設定ボタン
        self.btn_nav_settings = MultiFontButton(self, icon_text="", label_text="設定", anchor="w", fg_color=("#DBDBDB", "#2b2b2b"), command=lambda: on_menu_select("settings"))
        self.btn_nav_settings.grid(row=7, column=0, padx=5, pady=25, sticky="sew")

        # 右クリック用のバインド
        self.app.bind_pin_menu(widget=self.btn_nav_attend, name="👥 出欠管理・確認", fg_color=config.COLOR_BUTTON_YELLOWGREEN, hover_color=config.HOVER_COLOR_BUTTON_YELLOWGREEN, command_str="show_attendance_date_select")
        self.app.bind_pin_menu(widget=self.btn_nav_check, name="📅 ライブ管理", fg_color=config.COLOR_BUTTON_BLUE, hover_color=config.HOVER_COLOR_BUTTON_BLUE, command_str="register_live")
        self.app.bind_pin_menu(widget=self.btn_nav_form, name="📋 バンド募集フォーム作成", fg_color=config.COLOR_BUTTON_PINK, hover_color=config.HOVER_COLOR_BUTTON_PINK, command_str="create_form")
        self.app.bind_pin_menu(widget=self.btn_nav_band, name="🎤 バンド登録・選出", fg_color=config.COLOR_BUTTON_YELLOW, hover_color=config.HOVER_COLOR_BUTTON_YELLOW, command_str="register_band")
        self.app.bind_pin_menu(widget=self.btn_nav_select, name="🕑 タイムテーブル", fg_color=config.COLOR_BUTTON_PURPLE, hover_color=config.HOVER_COLOR_BUTTON_PURPLE, command_str="make_timetable")