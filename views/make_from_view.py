import os.path, json, threading, itertools
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import Calendar

import config

# フォーム作成・編集用スコープ
SCOPES = ['https://www.googleapis.com/auth/forms.body']

class FormCreator(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self.creds = None
        self.form_service = None

        self.weeks = ["月", "火", "水", "木", "金", "土", "日"]

        LIVE_JSON_PATH = self.app.get_config_path('live_info.json')
        self.settings = self.app.settings if self.app else {}
        self.schedules = []

        self.form_info = {
            "title": "",
            "description": "",
            "dates": [],
            "band_name_example": "",
            "deadline": ""
        }

        # JSONファイルからライブ情報読み込み
        if os.path.exists(LIVE_JSON_PATH):
            with open(LIVE_JSON_PATH, 'r', encoding='utf-8') as f:
                self.existing_lives = json.load(f)
        else:
            self.existing_lives = {}

        self.create_widgets()

    def authenticate(self):
        """認証トークンの読み込み・更新処理"""
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        # Forms APIサービスのビルド
        self.form_service = build('forms', 'v1', credentials=self.creds)

    def clear_frame(self):
        """フレーム内のウィジェットをすべて削除"""
        for widget in self.winfo_children():
            widget.destroy()

    def create_widgets(self):
        """フォーム作成用のウィジェットを作成する"""
        self.clear_frame()

        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(padx=0, pady=0, fill='x')
        ctk.CTkLabel(title_frame, text='📋 バンド募集フォームの作成', font=config.FONT_TITLE).pack(side='left', pady=(15, 5), anchor="w")
        ctk.CTkButton(title_frame, text='連携解除', font=config.FONT_LABEL_BUTTON, fg_color="red", width=80, command=self.unconnect_account).pack(side='right', padx=5, pady=(15, 5), anchor="w")
        self.message_label = ctk.CTkLabel(title_frame, text='', font=config.FONT_TITLE, text_color='gray50')
        self.message_label.pack(side='right', padx=5, pady=(15, 5), anchor="w")
        self.update_ui()  # Googleアカウント連携状況の表示更新
        ctk.CTkLabel(self, text='ライブ名を選択して、以下のボタンをクリックしてください。', font=config.FONT_SUBTITLE, anchor="w", justify="left", text_color='gray50').pack(pady=(0, 5), anchor="w")

        select_live_frame = ctk.CTkFrame(self, fg_color="transparent")
        select_live_frame.pack(padx=0, pady=5, fill='x')

        def on_live_select(event):
            choice = self.live_name_combo.get()
            self.schedules.clear()
            for sch in self.existing_lives[choice].get('schedules', []):
                date_str = sch.get('date', '')
                
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                    self.schedules.append({
                        'date': date_obj
                        })
                except ValueError:
                    continue
            live_info_text = ""
            if choice in self.existing_lives:
                live_info_text = f"■ライブ名\n{choice}\n\n■日程\n{'\n'.join([f'{idx + 1}日目: {sch["date"].strftime("%m月%d日")}（{self.weeks[sch['date'].weekday()]}）' for idx, sch in (enumerate(self.schedules))])}" # 〇日目: yyyy-mm-dd
                self.form_info["dates"].clear()
                for sch in self.schedules:
                    date_str = f"{sch['date'].strftime('%m月%d日')}（{self.weeks[sch['date'].weekday()]}）"  # m/d（曜日）形式に変換
                    self.form_info["dates"].append(date_str)
            live_info.configure(state='normal')
            live_info.delete("1.0", "end")
            live_info.insert("1.0", live_info_text)
            live_info.configure(state='disabled')

        ctk.CTkLabel(select_live_frame, text='募集フォームを作成するライブ', font=config.FONT_LABEL_BUTTON).pack(side='left', padx=0)
        live_names_list = list(self.existing_lives.keys())
        self.live_name_combo = ctk.CTkComboBox(
            select_live_frame, 
            values=live_names_list if live_names_list else [""], 
            font=(config.FONT_NAME, 16), 
            width=240,
            state="readonly",
            command=on_live_select
        )
        self.live_name_combo.set("") # 初期値は空
        self.live_name_combo.pack(side='left', padx=10)

        deadline_frame = ctk.CTkFrame(self, fg_color="transparent")
        deadline_frame.pack(padx=0, pady=5, fill='x')
        ctk.CTkLabel(deadline_frame, text='募集締め切り', font=config.FONT_LABEL_BUTTON, anchor="w", justify="left").pack(side='left', pady=5, anchor="w")
        self.date_entry = ctk.CTkEntry(deadline_frame, width=200, font=(config.FONT_NAME, 16))
        self.date_entry.pack(side='left', padx=10, pady=0)

        # カレンダー機能
        def open_calendar():
            try:
                cal_win = ctk.CTkToplevel(self.master)
                cal_win.title("日付を選択")
                icon_path = self.app.get_config_path('rock_icon.ico')
                cal_win.after(200, lambda: cal_win.iconbitmap(icon_path))
                cal_win.grab_set()
                cal = Calendar(cal_win, selectmode='day', date_pattern='yyyy-mm-dd', font=(config.FONT_NAME, 12))
                cal.pack(padx=15, pady=15)
                
                def set_date():
                    date_input = cal.get_date()
                    date_input = datetime.strptime(date_input, "%Y-%m-%d").date()
                    date_str = f"{date_input.strftime('%m/%d')}（{self.weeks[date_input.weekday()]}）23:59"  # m/d形式に変換
                    self.date_entry.delete(0, 'end')
                    self.date_entry.insert(0, date_str)

                    cal_win.destroy()
                    
                ctk.CTkButton(cal_win, text='決定', font=config.FONT_LABEL_BUTTON, command=set_date).pack(side='bottom', pady=10)
            except Exception:
                messagebox.showinfo("お知らせ", "tkcalendarモジュールがインストールされていません。手入力してください。")

        btn_cal = ctk.CTkButton(deadline_frame, text="📅", width=30, fg_color="gray70", text_color="black", command=open_calendar)
        btn_cal.pack(side='left', padx=(0, 15))

        ctk.CTkLabel(self, text='フォームの注意事項', font=config.FONT_LABEL_BUTTON, anchor="w", justify="left").pack(pady=5, anchor="w")
        self.form_info["description"] = self.settings.get('form_instructions', config.FORM_DISCRIPTION) if self.settings else config.FORM_DISCRIPTION
        form_instructions_textbox = ctk.CTkTextbox(self, width=1100, height=100, font=(config.FONT_NAME, 14), corner_radius=10, text_color='white')
        form_instructions_textbox.pack(padx=0, pady=0, fill='x')
        form_instructions_textbox.insert("1.0", self.form_info["description"])

        ctk.CTkLabel(self, text='ⓘ ライブ情報', font=config.FONT_LABEL_BUTTON, anchor="w", justify="left").pack(pady=5, anchor="w")
        live_info = ctk.CTkTextbox(self, width=1100, height=160, font=(config.FONT_NAME, 14), corner_radius=10, text_color='white', state='disabled')
        live_info.pack(padx=0, pady=0, fill='x')

        self.create_button = ctk.CTkButton(self, text="Google Formを作成", font=config.FONT_LABEL_BUTTON, fg_color="#564080", width=300, height=50, command=self.start_create_form)
        self.create_button.pack(side='bottom', pady=20)

    def start_create_form(self):
        """フォーム作成処理を開始する"""
        if self.live_name_combo.get().strip() == "":
            messagebox.showerror("エラー", "ライブ名を選択してください。")
            return
        self.form_info["title"] = f"{self.live_name_combo.get()} バンド募集"
        if self.date_entry.get().strip() != "":
            self.form_info["description"] = f"【応募期間】～{self.date_entry.get()}\n" + self.form_info["description"]
            self.form_info["deadline"] = self.date_entry.get()

                
        self.create_button.configure(text="フォーム作成中...", state="disabled")

        threading.Thread(target=self.create_form, daemon=True).start()

    def create_form(self):
        """フォームを新規作成する"""
        self.authenticate()  # 認証を行う
        new_form = {
            "info": {
                "title": self.form_info["title"],
                "documentTitle": self.form_info["title"]
            }
        }
        res = self.form_service.forms().create(body=new_form).execute()
        form_id = res["formId"]

        update_requests = {
            "requests": [
                {
                    "updateFormInfo": {
                        "info": {
                            "description": self.form_info["description"]
                        },
                        "updateMask": "description"
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "必要事項入力",
                            "pageBreakItem": {}
                        },
                        "location": {"index": 0}
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "バンド名（コピー元）",
                            "description": f"例：\n・{self.form_info['band_name_example']}\n※バンド名とコピー元が異なる場合のみ、（）内にコピー元を記入してください。\n※入力した内容がそのままSNS（ロック部・学祭・大学公式）などに記載されます。",
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "textQuestion": {
                                        "paragraph": False
                                    }
                                }
                            }
                        },
                        "location": {"index": 1}
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "演奏時間",
                            "description": f"半角数字のみ\n例：20分の場合：「20」と入力（「分」は入力しない）",
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "textQuestion": {
                                        "paragraph": False
                                    }
                                }
                            }
                        },
                        "location": {"index": 2}
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "メンバー",
                            "description": f"パート・名前\n※例のように記述してください（パートと名前の間はスペースを空けてください）。\n例：Vo.Gt. ロック太郎\n※名前は「本名・フルネーム」でお願いします（苗字と名前の間のスペースは不要）。\n※複数人いる場合は改行して記入してください。",
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "textQuestion": {
                                        "paragraph": True
                                    }
                                }
                            }
                        },
                        "location": {"index": 3}
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "出演可能日について",
                            "description": "⚠️最も合う選択肢を選んで下さい。\n※欠席については、別途連絡してください（これは欠席連絡には該当しません）。",
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "choiceQuestion": {
                                        "type": "RADIO",
                                        "options": self.make_date_choice()
                                    }
                                }
                            }
                        },
                        "location": {"index": 4}
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "その他（出演できない時間帯や要望などがあれば）",
                            "questionItem": {
                                "question": {
                                    "required": False,
                                    "textQuestion": {
                                        "paragraph": True
                                    }
                                }
                            }
                        },
                        "location": {"index": 5}
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "確認",
                            "pageBreakItem": {}
                        },
                        "location": {"index": 6}
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "応募条件を満たしていることを確認してから応募してください。",
                            "pageBreakItem": {} 
                        },
                        "location": {"index": 7}
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": f"入力した情報は、{self.form_info['deadline']}まで編集できます。",
                            "pageBreakItem": {} 
                        },
                        "location": {"index": 8}
                    }
                }
            ]
        }
        # リクエストを送信してフォームを更新
        res = self.form_service.forms().batchUpdate(formId=form_id, body=update_requests).execute()

        initial_section_id = res["replies"][1]["createItem"]["itemId"]
        try_again_section_id = res["replies"][8]["createItem"]["itemId"]
        show_edit_deadline_section_id = res["replies"][9]["createItem"]["itemId"]

        add_questions_requests = {
            "requests": [
                {
                    "createItem": {
                        "item": {
                            "title": "応募条件を満たしていますか？",
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "choiceQuestion": {
                                        "type": "RADIO",
                                        "options": [
                                            {
                                                "value": "はい",
                                                "goToSectionId": show_edit_deadline_section_id
                                            },
                                            {
                                                "value": "いいえ",
                                                "goToSectionId": try_again_section_id
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        "location": {"index": 7}
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "もう一度やり直してください",
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "choiceQuestion": {
                                        "type": "RADIO",
                                        "options": [
                                            {
                                                "value": "はい",
                                                "goToSectionId": initial_section_id
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        "location": {"index": 9}
                    }
                }
            ]
        }

        # リクエストを送信して質問を追加
        self.form_service.forms().batchUpdate(formId=form_id, body=add_questions_requests).execute()

        self.create_button.configure(text="作成したフォームに移動", fg_color="#00A156", command=lambda: self.open_form_in_browser(form_id), state="normal")


    def make_date_choice(self):
        """日程の選択肢を作成する"""
        date_choices = []
        if len(self.form_info["dates"]) == 1:
            date_choices.append(f"[0]{self.form_info['dates'][0]}出演可能")
        elif len(self.form_info["dates"]) > 1:
            date_choices.append("[0]全日程出演可能")
            indexed_dates = list(enumerate(self.form_info["dates"], start=1))
            for r in range(1, len(self.form_info["dates"])):
                suffix = "のみ出演可能" if r == 1 else "出演可能"
                for combo in itertools.combinations(indexed_dates, r):
                    indices_str = "".join([f"[{idx}]" for idx, _ in combo])
                    dates_str = "、".join([date for _, date in combo])
                    
                    date_choices.append(f"{indices_str}{dates_str}{suffix}")

        form_options = [{"value": choice} for choice in date_choices]
        return form_options

    def check_login_status(self):
        """Googleアカウントが連携済みかどうかをチェックする関数"""
        token_path = 'token.json'
        
        # 1. token.json が存在しない場合は「未連携」
        if not os.path.exists(token_path):
            return False, None

        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            # 2. トークンが有効な場合
            if creds and creds.valid:
                return True, creds
                
            # 3. トークンは期限切れだが、リフレッシュ（自動更新）可能な場合
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # 更新したトークンを保存
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                return True, creds

        except Exception:
            # ファイルが壊れている・認証が失効している場合
            return False, None

        return False, None

    def update_ui(self):
        is_logged_in, self.creds = self.check_login_status()

        if is_logged_in:
            self.message_label.configure(text="Googleアカウント連携済み", text_color=("green", "light green"))
        else:
            self.message_label.configure(text="Googleアカウント未連携", text_color="gray")

    def unconnect_account(self):
        """Googleアカウントの連携を解除する関数"""
        token_path = 'token.json'
        if os.path.exists(token_path):
            os.remove(token_path)
            messagebox.showinfo("お知らせ", "Googleアカウントの連携を解除しました。")
        else:
            messagebox.showinfo("お知らせ", "Googleアカウントは連携されていません。")
        self.update_ui()  # UIを更新して連携状況を反映

    def open_form_in_browser(self, form_id):
        """作成したフォームをブラウザで開く"""
        import webbrowser
        form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
        webbrowser.open(form_url)

if __name__ == '__main__':
    # テスト用の簡単なGUIを作成してフォーム作成を実行
    root = ctk.CTk()
    root.title("Google Form 作成画面")
    root.geometry("1150x680")

    form_creator = FormCreator(root, app=None)
    form_creator.authenticate()
    form_creator.main()

    root.mainloop()