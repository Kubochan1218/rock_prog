from typing import Callable, Optional, Tuple, Union
import customtkinter as ctk

# GUIフォント設定
FONT_NAME = 'Yu Gothic UI'
FONT_ICON_NAME = "Segoe Fluent Icons"
FONT_TITLE = (FONT_NAME, 20, 'bold')
FONT_LABEL_BUTTON = (FONT_NAME, 16)
FONT_SUBTITLE = (FONT_NAME, 14)
FONT_ICON_TITLE = (FONT_ICON_NAME, 20)
FONT_ICON_LABEL = (FONT_ICON_NAME, 16)

# 色指定の型定義: 単一の文字列または (ライトモード色, ダークモード色) のタプル
ColorType = Union[str, Tuple[str, str]]


class MultiFontButton(ctk.CTkFrame):
    def __init__(
        self,
        master: any,
        icon_text: str = "",
        label_text: str = "",
        fg_color: ColorType = ("#EAEAE8", "#2b2b2b"),
        hover_color: ColorType = ("#F4F5F2", "#323232"),
        text_color: ColorType = ("#000000", "#FFFFFF"),
        icon_font: Optional[tuple|ctk.CTkFont] = (FONT_ICON_NAME, 16),
        label_font: Optional[tuple|ctk.CTkFont] = (FONT_NAME, 16),
        corner_radius: int = 5,
        height: int = 30,
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
        self._disabled_color = ("#9CA3AF", "#4B5563")  # disabled時の背景色

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

        # 幅や高さの固定処理
        if width is not None:
            self.pack_propagate(False)
            self.grid_propagate(False)

        # デフォルトフォントの設定
        self._icon_font = icon_font or (FONT_ICON_NAME, 16)
        self._label_font = label_font or (FONT_NAME, 16)

        # --- 内部レイアウト ---
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(expand=True, anchor=self._anchor, padx=10)

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
        else:
            self.configure(fg_color=self._fg_color)
        self._update_cursor()


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