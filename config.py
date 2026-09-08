"""定数・設定値をまとめたファイル"""
VERSION = '2.3.0'

FILE_PATH = 'attend_data.xlsx'
SHEET_NAME = '出欠状況'
APP_MODE = 'System'  # 'Light' or 'Dark' or 'System'
APP_COLOR = 'win-default'  # 'blue' or 'green' or 'dark-blue' or 'win-default'

# GUIフォント設定
FONT_NAME = 'Yu Gothic UI'
FONT_ICON_NAME = "Segoe Fluent Icons"
FONT_TITLE = (FONT_NAME, 20, 'bold')
FONT_LABEL_BUTTON = (FONT_NAME, 16, 'bold')
FONT_TEXT = (FONT_NAME, 18)
FONT_BOLD_TEXT = (FONT_NAME, 18, 'bold')
FONT_SUBTITLE = (FONT_NAME, 14)
FONT_ICON_TITLE = (FONT_ICON_NAME, 20)
FONT_ICON_LABEL = (FONT_ICON_NAME, 16)

# GUIカラー設定
# テキストボタン
COLOR_TEXT_BUTTON = ("#003E92", "#8DD7E9")
HOVER_COLOR_TEXT_BUTTON = ("#c8c9c9", "#505050")
# ボタン
COLOR_BUTTON_BLUE = ("#0067C0", "#4CC2FF")
HOVER_COLOR_BUTTON_BLUE = ("#1976C5", "#49B3EB")
COLOR_BUTTON_GRAY = ("#FEFEFE", "#373737")
HOVER_COLOR_BUTTON_GRAY = ("#F8F8F8", "#434343")

COLOR_BUTTON_GREEN = "#00d170"
HOVER_COLOR_BUTTON_GREEN = ("#1ee287", "#01bb64")
COLOR_BUTTON_YELLOWGREEN = "#bfff80"
HOVER_COLOR_BUTTON_YELLOWGREEN = ("#cfff9f", "#a2e95b")
COLOR_BUTTON_LIGHTBLUE = "#80d4ff"
HOVER_COLOR_BUTTON_LIGHTBLUE = ("#a3e4ff", "#50c8ff")
COLOR_BUTTON_YELLOW = "#ffcc00"
HOVER_COLOR_BUTTON_YELLOW = ("#ffdc17", "#dda600")
COLOR_BUTTON_ORANGE = "#ff9900"
HOVER_COLOR_BUTTON_ORANGE = ("#ffae0c", "#dd8100")
COLOR_BUTTON_LIGHTORANGE = "#ffcd9c"
HOVER_COLOR_BUTTON_LIGHTORANGE = ("#ffd6b3", "#e6a87f")
COLOR_BUTTON_RED = "#ff0000"
HOVER_COLOR_BUTTON_RED = ("#ff3333", "#cc0000")
COLOR_BUTTON_PURPLE = "#a748ff"
HOVER_COLOR_BUTTON_PURPLE = ("#ae5eff", "#9c32ff")
COLOR_BUTTON_PINK = "#ff9999"
HOVER_COLOR_BUTTON_PINK = ("#ffa1a1", "#fc8181")

UPDATE_LOG = "Excelファイルへの出席データの書き込み形式を変更しました。\n\n既存の出欠データを書き換えますか？"

FORM_DISCRIPTION = "⚠️注意書きを読んでから入力して下さい。\n※応募に関する注意事項を記載した資料（補足資料なども含む）を読んでいなかったことに起因する不都合は配慮できません。\n※「例」通りに入力していない場合、正しく処理が出来ません。ご協力お願いします🙇"