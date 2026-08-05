"""定数・設定値をまとめたファイル"""

FILE_PATH = 'attend_data.xlsx'
SHEET_NAME = '出欠状況'
FONT_NAME = 'Yu Gothic UI'
APP_MODE = 'System'  # 'Light' or 'Dark' or 'System'
APP_COLOR = 'green'  # 'blue' or 'green' or 'dark-blue'
FONT_TITLE = (FONT_NAME, 20, 'bold')
FONT_LABEL_BUTTON = (FONT_NAME, 16, 'bold')
FONT_SUBTITLE = (FONT_NAME, 14)

VERSION = '2.1.0'
UPDATE_LOG = "Excelファイルへの出席データの書き込み形式を変更し、目視で確認しやすくなったほか、○（漢数字）と○（記号）などの差異によって出席率計算に誤差が出る現象を修正しました。\n\n既存の出欠データを書き換えますか？"