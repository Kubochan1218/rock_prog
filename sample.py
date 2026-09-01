class Translator:
    def __init__(self):
        # 実際の運用では Excel (pandas等) から読み込む
        # 構造: { '日本語': {'en': '...', 'en_pos': '...', 'zh': '...', 'zh_pos': '...'} }
        self.dictionary = {
            "公園の": {"en": "in the park", "en_pos": "POST", "zh": "公园里的", "zh_pos": "PRE"},
            "椅子": {"en": "bench", "en_pos": "HEAD", "zh": "椅子", "zh_pos": "HEAD"},
            "青い": {"en": "blue", "en_pos": "PRE", "zh": "蓝色的", "zh_pos": "PRE"},
            "空": {"en": "sky", "en_pos": "HEAD", "zh": "天空", "zh_pos": "HEAD"},
            "大きな": {"en": "big", "en_pos": "PRE", "zh": "大的", "zh_pos": "PRE"}
        }

    def _ask_user_for_unknown(self, unknown_text):
        """未知語が出現した際にユーザに入力させる関数"""
        print(f"\n辞書にない言葉が見つかりました: 「{unknown_text}」")
        en = input("英語訳を入力してください: ")
        en_pos = input("英語の配置(PRE/POST/HEAD)を入力してください: ")
        zh = input("中国語訳を入力してください: ")
        zh_pos = input("中国語の配置(PRE/POST/HEAD)を入力してください: ")
        
        new_entry = {"en": en, "en_pos": en_pos.upper(), "zh": zh, "zh_pos": zh_pos.upper()}
        self.dictionary[unknown_text] = new_entry
        # TODO: ここでExcelファイルにも追記保存する処理を入れる
        return new_entry

    def tokenize(self, text):
        """最長一致による切り出しと未知語処理"""
        i = 0
        tokens = []
        unknown_buf = ""

        while i < len(text):
            match_len = 0
            # 現在のインデックスから、残り文字数の最大長から徐々に短くして検索（最長一致）
            for j in range(len(text), i, -1):
                chunk = text[i:j]
                if chunk in self.dictionary:
                    match_len = j - i
                    break
            
            if match_len > 0:
                # 辞書にある単語が見つかった。その前に未知語バッファがあれば処理する
                if unknown_buf:
                    self._ask_user_for_unknown(unknown_buf)
                    tokens.append(self.dictionary[unknown_buf])
                    unknown_buf = ""
                
                # 見つかった単語をトークンに追加
                tokens.append(self.dictionary[text[i:i+match_len]])
                i += match_len
            else:
                # 見つからない場合は未知語バッファに1文字積んで次へ
                unknown_buf += text[i]
                i += 1

        # 文末に未知語が残っていた場合の処理
        if unknown_buf:
            self._ask_user_for_unknown(unknown_buf)
            tokens.append(self.dictionary[unknown_buf])

        return tokens

    def translate(self, text, lang='en'):
        """指定した言語へ変換・語順並び替え"""
        tokens = self.tokenize(text)
        
        pre_list = []
        post_list = []
        result = []

        for token in tokens:
            word = token[lang]
            pos = token[f"{lang}_pos"]

            if pos == 'PRE':
                pre_list.append(word)
            elif pos == 'POST':
                post_list.append(word)
            elif pos == 'HEAD' or pos == 'FIXED':
                # HEADが来たらバッファを放出して結合
                result.extend(pre_list)
                result.append(word)
                result.extend(post_list)
                # バッファをリセット
                pre_list, post_list = [], []

        # 文末がHEADで終わらずに修飾語が残ってしまった場合のフェイルセーフ
        result.extend(pre_list)
        result.extend(post_list)

        # スペースで結合して出力
        return " ".join(result)

# --- 実行テスト ---
if __name__ == "__main__":
    translator = Translator()
    
    # 例1：公園の椅子
    print("【入力】公園の椅子")
    print("英語:", translator.translate("公園の椅子", lang='en'))
    print("中国語:", translator.translate("公園の椅子", lang='zh'))
    
    print("-" * 30)
    
    # 例2：青い空
    print("【入力】青い空")
    print("英語:", translator.translate("青い空", lang='en'))
    print("中国語:", translator.translate("青い空", lang='zh'))
    
    print("-" * 30)
    
    # 例3：複合（公園の大きな椅子）
    print("【入力】公園の大きな椅子")
    print("英語:", translator.translate("公園の大きな椅子", lang='en'))
    print("中国語:", translator.translate("公園の大きな椅子", lang='zh'))
