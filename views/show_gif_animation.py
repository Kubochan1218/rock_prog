import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageSequence

class AnimatedGifCTkLabel(ctk.CTkLabel):
    def __init__(self, master, gif_path, delay=100, size=None, **kwargs):
        """
        gif_path: GIFファイルのパス
        delay: アニメーションの速度（ミリ秒）
        size: 画像を表示するサイズ (幅, 高さ) のタプル。指定しない場合は画像の原寸大。
        """
        # 通常のCTkLabelとしての初期化（text=" "など、画像以外の設定を引き継ぐ）
        super().__init__(master, text="", **kwargs)
        
        self.frames = []
        self.gif_index = 0
        self.delay = delay
        
        pil_img = Image.open(gif_path)
        img_width = size[0] if size else pil_img.width
        img_height = size[1] if size else pil_img.height
        
        for frame in ImageSequence.Iterator(pil_img):
            # 各フレームをコピーして独立した画像として扱う
            frame_copy = frame.copy()
            
            ctk_img = ctk.CTkImage(
                light_image=frame_copy,
                dark_image=frame_copy,
                size=(img_width, img_height)
            )
            self.frames.append(ctk_img)
                
        if self.frames:
            self.animate()

    def animate(self):
        # 現在のフレームを反映
        self.configure(image=self.frames[self.gif_index])
        
        # インデックスを進める
        self.gif_index = (self.gif_index + 1) % len(self.frames)
        
        # 次のフレームを予約
        self.after(self.delay, self.animate)
