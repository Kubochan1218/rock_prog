from typing import Callable, Optional, Tuple, Union
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime

# GUIフォント設定
FONT_NAME = 'Yu Gothic UI'
FONT_ICON_NAME = "Segoe Fluent Icons"
FONT_TITLE = (FONT_NAME, 20, 'bold')
FONT_LABEL_BUTTON = (FONT_NAME, 16)
FONT_BOLD_TEXT = (FONT_NAME, 18, 'bold')
FONT_SUBTITLE = (FONT_NAME, 14)
FONT_ICON_TITLE = (FONT_ICON_NAME, 20)
FONT_ICON_LABEL = (FONT_ICON_NAME, 16)

COLOR_BUTTON_BLUE = ("#0067C0", "#4CC2FF")
HOVER_COLOR_BUTTON_BLUE = ("#1976C5", "#49B3EB")
COLOR_BUTTON_GRAY = ("#FEFEFE", "#373737")
HOVER_COLOR_BUTTON_GRAY = ("#F8F8F8", "#434343")

# 色指定の型定義: 単一の文字列または (ライトモード色, ダークモード色) のタプル
ColorType = Union[str, Tuple[str, str]]

try:
    from tkcalendar import Calendar
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False

class MultiFontButton(ctk.CTkFrame):
    """アイコンとテキストを同時に表示できるカスタムボタン"""
    def __init__(
        self,
        master: any,
        icon_text: str = "",
        label_text: str = "",
        fg_color: ColorType = COLOR_BUTTON_GRAY,
        hover_color: ColorType = ("#F4F5F2", "#323232"),
        text_color: ColorType = ("#000000", "#FFFFFF"),
        icon_font: Optional[tuple|ctk.CTkFont] = (FONT_ICON_NAME, 16),
        label_font: Optional[tuple|ctk.CTkFont] = (FONT_NAME, 16),
        corner_radius: int = 5,
        height: int = 36,
        width: Optional[int] = 160,
        command: Optional[Callable] = None,
        state: str = "normal",  # "normal" または "disabled"
        anchor: str = "center",  # "center", "w", "e", "n", "s" など
    ):
        # カラー設定の保持
        self._original_fg_color = fg_color
        self._fg_color = fg_color
        self._hover_color = hover_color
        self._pressed_color = fg_color
        self._text_color = text_color
        self._disabled_color = ("#F4F5F2", "#323232")  # disabled時の背景色

        # 初期状態の設定
        current_fg = (
            self._fg_color if state == "normal" else self._disabled_color
        )

        super().__init__(
            master,
            fg_color=current_fg,
            corner_radius=corner_radius,
            height=height,
            width=width,
        )

        # プロパティ保持
        self._command = command
        self._state = state
        self._anchor = anchor
        self._is_pressed = False

        # 幅や高さの固定処理
        if width is not None:
            self.pack_propagate(False)
            self.grid_propagate(False)

        # デフォルトフォントの設定
        self._icon_font = icon_font or (FONT_ICON_NAME, 16)
        self._label_font = label_font or (FONT_NAME, 16)

        # 選択状態表示バー
        self._selection_bar = ctk.CTkFrame(self, height=int(height * 0.45), width=3, fg_color="transparent", corner_radius=2)
        self._selection_bar.pack(padx=0, side="left")

        # --- 内部レイアウト ---
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(expand=True, anchor=self._anchor, padx=5)

        # アイコン用ラベル
        self._icon_label = ctk.CTkLabel(
            self._container,
            text=icon_text,
            font=self._icon_font,
            text_color=self._text_color,
        )

        # テキスト用ラベル
        self._text_label = ctk.CTkLabel(
            self._container,
            text=label_text,
            font=self._label_font,
            text_color=self._text_color,
        )

        # テキストが存在する場合のみ配置
        if icon_text:
            self._icon_label.pack(side="left", padx=(0, 5))
        if label_text:
            self._text_label.pack(side="left", padx=5, anchor="w")

        # --- イベントバインド ---
        self._widgets = (
            self,
            self._container,
            self._icon_label,
            self._text_label,
        )
        for w in self._widgets:
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_button_press)
            w.bind("<ButtonRelease-1>", self._on_button_release)

        self._update_cursor()

    # --- 内部イベントハンドラ ---
    def _on_enter(self, event):
        if self._state == "normal":
            self._fg_color = self._hover_color
            self.configure(fg_color=self._hover_color)

    def _on_leave(self, event):
        if self._state == "normal":
            self._fg_color = self._original_fg_color
            self.configure(fg_color=self._fg_color)

    def _on_button_press(self, event):
        if self._state == "normal":
            self._is_pressed = True
            self.configure(fg_color=self._pressed_color)

    def _on_button_release(self, event):
        if self._state == "normal" and self._is_pressed:
            self._is_pressed = False

            # マウスリリース時にカーソルがボタン領域内にあるかチェック
            inside = (0 <= event.x <= self.winfo_width()) and (0 <= event.y <= self.winfo_height())
            if inside:
                self.configure(fg_color=self._hover_color)
                if self._command:
                    self._command()
            else:
                self.configure(fg_color=self._fg_color)

    def _update_cursor(self):
        cursor = "hand2" if self._state == "normal" else ""
        for w in self._widgets:
            w.configure(cursor=cursor)

    # --- 外部設定用メソッド (state変更等) ---
    def configure_state(self, state: str):
        """ボタンの有効/無効状態を変更 ("normal" or "disabled")"""
        self._state = state
        if state == "disabled":
            self.configure(fg_color=self._disabled_color)
            # self._selection_bar.configure(fg_color=COLOR_BUTTON_BLUE)  # 選択バーの色を変更
        else:
            self.configure(fg_color=self._fg_color)
            # self._selection_bar.configure(fg_color="transparent")  # 選択バーの色を元に戻す
        self._update_cursor()

class CalendarInput(ctk.CTkFrame):
    """カレンダー入力用のカスタムコンポーネントクラス"""
    def __init__(
        self,
        master: any,
        app_ref=None,
        calendar_font=(FONT_NAME, 12),
        button_font=(FONT_NAME, 16),
        button_color: ColorType = COLOR_BUTTON_GRAY,
        button_hover_color: ColorType = HOVER_COLOR_BUTTON_GRAY,
        date_pattern: str = "yyyy-mm-dd",
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=("#FFFFFF", "#2B2B2B"),      # Entryの標準背景色（Light/Dark）
            border_color=("#979DA2", "#565B5E"),  # Entryの標準ボーダー色
            border_width=2,
            corner_radius=6,                      # Entryの標準角丸
            **kwargs
        )
        
        self.app_ref = app_ref
        self.font = calendar_font
        self.button_font = button_font
        self.button_color = button_color
        self.button_hover_color = button_hover_color
        self.date_pattern = date_pattern

        # 日付入力用 Entry
        self.entry = ctk.CTkEntry(self, font=self.button_font, width=100, height=24, fg_color="transparent", border_width=0, corner_radius=0)
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 0), pady=2)

        # カレンダー呼び出しボタン
        self.cal_button = ctk.CTkButton(
            self,
            text="",
            width=28,
            height=23,
            font=FONT_ICON_LABEL,
            fg_color="transparent",
            hover_color=self.button_hover_color,
            text_color=("#000000", "#FFFFFF"),
            corner_radius=4,
            command=self._open_calendar
        )
        self.cal_button.pack(side="right", padx=(0, 4), pady=(3, 2))
        
    def _open_calendar(self):
        """カレンダーポップアップウィンドウを開く"""
        if not HAS_TKCALENDAR:
            messagebox.showinfo("お知らせ", "tkcalendarモジュールがインストールされていません。手入力してください。")
            return

        try:
            cal_win = ctk.CTkToplevel(self)
            cal_win.title("日付を選択")
            
            # アイコン設定（app_refが存在する場合）
            if self.app_ref and hasattr(self.app_ref, 'get_config_path'):
                icon_path = self.app_ref.get_config_path('assets\\icons\\rock_icon.ico')
                cal_win.after(200, lambda: cal_win.iconbitmap(icon_path))
                
            cal_win.grab_set()

            # カレンダーの配置
            cal = Calendar(
                cal_win,
                selectmode='day',
                date_pattern="yyyy-mm-dd",
                font=self.font if self.font else (FONT_NAME, 12)
            )
            cal.pack(padx=15, pady=15)

            def set_date():
                date_str = cal.get_date()
                if self.date_pattern != "yyyy-mm-dd":
                    try:
                        date_dt = datetime.strptime(date_str, "%Y-%m-%d")
                        date_str = date_dt.strftime(self.date_pattern)
                    except ValueError:
                        pass
                self.entry.delete(0, 'end')
                self.entry.insert(0, date_str)
                cal_win.destroy()

            # 決定ボタン
            ctk.CTkButton(
                cal_win,
                text='決定',
                font=self.button_font,
                fg_color=self.button_color,
                hover_color=self.button_hover_color,
                text_color=("#000000", "#FFFFFF"),
                command=set_date
            ).pack(side='bottom', pady=10)

        except Exception as e:
            messagebox.showerror("エラー", f"カレンダーの起動に失敗しました: {e}")

    # 外部から値を取得・設定するためのメソッド
    def get(self):
        """入力された日付を取得"""
        return self.entry.get()

    def set(self, value):
        """日付を外部からセット"""
        self.entry.delete(0, 'end')
        self.entry.insert(0, value)

    def delete(self, first, last=None):
        """入力値を削除"""
        self.entry.delete(first, last)

class ModernTile(ctk.CTkFrame):
    """
    タイトル、説明文、左右アイコン、および任意のウィジェットを追加できる
    モダンなタイル型コンポーネントクラス
    """
    def __init__(
        self,
        master: any,
        title: str = "タイルの名前",
        description: str = "タイルの説明",
        left_icon: str = "",
        right_icon: str = "",
        left_icon_cmd=None,
        right_icon_cmd=None,
        **kwargs
    ):
        # タイル外枠のスタイル設定
        super().__init__(master, **kwargs)

        self.left_icon_cmd = left_icon_cmd
        self.right_icon_cmd = right_icon_cmd

        # --- 1. 左側アイコン ---
        if left_icon:
            self.left_icon_label = ctk.CTkLabel(
                self,
                text=left_icon,
                font=FONT_ICON_TITLE
            )
            self.left_icon_label.pack(side="left", anchor="n", padx=(20, 10), pady=20)
            
            # 左アイコンクリックイベントの割り当て
            if self.left_icon_cmd:
                self.left_icon_label.bind("<Button-1>", lambda e: self.left_icon_cmd())
                self.left_icon_label.configure(cursor="hand2")

        # --- 2. 右側アイコン ---
        if right_icon:
            self.right_icon_label = ctk.CTkLabel(
                self,
                text=right_icon,
                font=FONT_ICON_LABEL
            )
            self.right_icon_label.pack(side="right", anchor="n", padx=(10, 20), pady=20)
            
            # 右アイコンクリックイベントの割り当て（メニュー開閉や設定ボタン等に便利）
            if self.right_icon_cmd:
                self.right_icon_label.bind("<Button-1>", lambda e: self.right_icon_cmd())
                self.right_icon_label.configure(cursor="hand2")

        # --- 3. 中央テキスト（タイトル ＆ 説明文） ---
        self.text_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.text_frame.pack(side="top", fill="x", expand=True, padx=10, pady=(10, 0), anchor="w")

        self.title_label = ctk.CTkLabel(
            self.text_frame,
            text=title,
            font=FONT_BOLD_TEXT,
            anchor="w"
        )
        self.title_label.pack(fill="x", anchor="w")

        self.desc_label = ctk.CTkLabel(
            self.text_frame,
            text=description,
            font=FONT_SUBTITLE,
            text_color="gray50",
            anchor="nw",
            justify="left"
        )
        self.desc_label.pack(fill="x", anchor="w")

        # --- 4. 任意ウィジェット追加用エリア（widgets_frame） ---
        self.widgets_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.widgets_frame.pack(fill="x", expand=True, padx=10, pady=(5, 15))

    def container(self) -> ctk.CTkFrame:
        """子ウィジェットを追加するためのフレームを取得"""
        return self.widgets_frame

    def set_title(self, text: str):
        """タイトル文字列を動的に更新"""
        self.title_label.configure(text=text)

    def set_description(self, text: str):
        """説明文を動的に更新"""
        self.desc_label.configure(text=text)

# --- 動作確認用サンプル ---
if __name__ == "__main__":
    app = ctk.CTk()
    app.geometry("400 x 300")

    def my_action():
        pass

    # 自作ボタンのインスタンス化
    custom_btn = MultiFontButton(
        master=app,
        icon_text="",
        label_text="ホーム",
        height=45,
        width=180,
        command=my_action,
        state="normal",
        anchor="center",
    )
    custom_btn.pack(pady=40)

    # ステート切替テスト用ボタン
    def toggle_state():
        new_state = "disabled" if custom_btn._state == "normal" else "normal"
        custom_btn.configure_state(new_state)

    toggle_btn = ctk.CTkButton(
        app, text="有効/無効 切り替え", command=toggle_state
    )
    toggle_btn.pack(pady=10)

    app.mainloop()