"""定数・設定値をまとめたファイル"""
VERSION = '2.3.0'

FILE_PATH = 'attend_data.xlsx'
SHEET_NAME = '出欠状況'
APP_MODE = 'System'  # 'Light' or 'Dark' or 'System'
APP_COLOR = 'win-default'  # 'blue' or 'green' or 'dark-blue' or 'win-default'

# GUIフォント設定
FONT_NAME = 'Yu Gothic UI'
FONT_TITLE = (FONT_NAME, 20, 'bold')
FONT_LABEL_BUTTON = (FONT_NAME, 16, 'bold')
FONT_SUBTITLE = (FONT_NAME, 14)

# GUIカラー設定
# テキストボタン
COLOR_TEXT_BUTTON = ("#3e909b", "#65e1f1")
HOVER_COLOR_TEXT_BUTTON = ("#c8c9c9", "#505050")

UPDATE_LOG = "Excelファイルへの出席データの書き込み形式を変更し、目視で確認しやすくなったほか、○（漢数字）と○（記号）などの差異によって出席率計算に誤差が出る現象を修正しました。\n\n既存の出欠データを書き換えますか？"

FORM_DISCRIPTION = "⚠️注意書きを読んでから入力して下さい。\n※応募に関する注意事項を記載した資料（補足資料なども含む）を読んでいなかったことに起因する不都合は配慮できません。\n※「例」通りに入力していない場合、正しく処理が出来ません。ご協力お願いします🙇"