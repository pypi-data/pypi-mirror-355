import os
import tkinter as tk
from tkinter import ttk

OUTPUT = "HDMI-2"

current_brightness = 1.0
current_warmth = 1.0

def apply_settings():
    red = 1.1
    green = 0.7
    blue = current_warmth
    os.system(f"xrandr --output {OUTPUT} --brightness {current_brightness:.2f} --gamma {red:.2f}:{green:.2f}:{blue:.2f}")

def on_brightness_change(event):
    global current_brightness
    current_brightness = float(brightness_slider.get())
    apply_settings()

def on_warmth_change(event):
    global current_warmth
    current_warmth = float(warmth_slider.get())
    apply_settings()

def main():
    global brightness_slider, warmth_slider
    root = tk.Tk()
    root.title("Display Comfort Controller")
    root.geometry("450x300")
    root.configure(bg="#1e1e1e")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 11))
    style.configure("TScale", background="#1e1e1e")
    style.configure("TFrame", background="#1e1e1e")

    frame = ttk.Frame(root)
    frame.pack(pady=30)

    ttk.Label(frame, text="Screen Brightness (0.1 - 1.0):").pack(pady=(0, 6))
    brightness_slider = ttk.Scale(frame, from_=0.1, to=1.0, orient="horizontal", length=320)
    brightness_slider.set(current_brightness)
    brightness_slider.pack()
    brightness_slider.bind("<Motion>", on_brightness_change)
    brightness_slider.bind("<ButtonRelease-1>", on_brightness_change)

    ttk.Label(frame, text="Night Mode Warmth (Stronger ←→ Normal):").pack(pady=(20, 6))
    warmth_slider = ttk.Scale(frame, from_=0.2, to=1.0, orient="horizontal", length=320)
    warmth_slider.set(current_warmth)
    warmth_slider.pack()
    warmth_slider.bind("<Motion>", on_warmth_change)
    warmth_slider.bind("<ButtonRelease-1>", on_warmth_change)

    root.mainloop()

if __name__ == "__main__":
    main()
