import os
import sys
import subprocess
import requests
import ctypes
from tkinter import messagebox

import config

CURRENT_VERSION = config.VERSION
REPO_OWNER = "Kubochan1218"
REPO_NAME = "rock_club"

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
APP_USER_AGENT = f"Rock System/{CURRENT_VERSION}"

class UpdateChecker:
    def __init__(self):
        self.latest_version = None
        self.installer_url = None

    def check_for_update(self):
        try:
            headers = {"User-Agent": APP_USER_AGENT}
            response = requests.get(GITHUB_API_URL, headers=headers, timeout=5)
            
            if response.status_code != 200:
                print(f"GitHub APIエラー: ステータスコード {response.status_code}")
                return False
            
            try:
                release_data = response.json()
            except Exception as json_err:
                print("JSONの解析に失敗しました。")
                return False
            self.latest_version = release_data.get("tag_name", "")
            
            if self.latest_version == CURRENT_VERSION:
                print("アプリは最新です。")
                return False
            
            for asset in release_data.get("assets", []):
                if asset.get("name") == "Rock_system_Installer.exe":
                    self.installer_url = asset.get("browser_download_url")
                    break
            
            if not self.installer_url:
                print("リリース内に Rock_system_Installer.exe が見つかりませんでした。")
                return False
            
            return True
        
        except Exception as e:
            print(f"アップデートチェック中にエラーが発生しました: {e}")
            return False

    def update_from_github(self):
        try:
            # Tempフォルダーへダウンロード
            temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
            installer_path = os.path.join(temp_dir, "setup_update.exe")
            
            print(f"最新バージョン {self.latest_version} をダウンロード中...")
            res_file = requests.get(self.installer_url, stream=True)
            with open(installer_path, "wb") as f:
                for chunk in res_file.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # 管理者権限でサイレント実行
            params = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART"
            print("インストーラーを起動します。UACの許可をしてください...")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", installer_path, params, None, 1
            )
            
            # 自アプリを即座に終了
            sys.exit(0)
        except Exception as e:
            print(f"アップデート中にエラーが発生しました: {e}")

if __name__ == "__main__":
    update_checker = UpdateChecker()
    if update_checker.check_for_update():
        if messagebox.askyesno("アップデート確認", f"新しいバージョン {update_checker.latest_version} が利用可能です。\n\nアップデートしますか？"):
            update_checker.update_from_github()
    else:
        print("アップデートはありません。")
