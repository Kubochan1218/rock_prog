import tkinter as tk

"""
sample_button.py
- Tkinterでフレームを入れ子にし、外側/内側にボタンを配置するサンプル。
- 実行: python sample_button.py
"""


def main():
    root = tk.Tk()
    root.title('Sample Buttons - Nested Frames')

    # 外側フレーム（境界線を非表示）
    outer = tk.Frame(root, bd=0, relief='flat', padx=8, pady=8)
    outer.pack(padx=12, pady=12)

    # 外側のボタン（左）
    tk.Button(outer, text='外側ボタン1', width=12, height=2).pack(side='left', padx=6)

    # outer の中に入れ子の inner フレームを作成
    inner = tk.Frame(outer, bd=1, relief='flat', padx=6, pady=6)
    inner.pack(side='left', padx=6)

    # inner の中のボタン（縦並び）
    tk.Button(inner, text='内側ボタンA', width=12, height=2).pack(padx=4, pady=4)
    tk.Button(inner, text='内側ボタンB', width=12, height=2).pack(padx=4, pady=4)

    # 外側フレームの別のボタン（右）
    tk.Button(outer, text='外側ボタン2', width=12, height=2).pack(side='left', padx=6)

    root.mainloop()


if __name__ == '__main__':
    main()
