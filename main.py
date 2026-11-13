import sys
import customtkinter as ctk
from ui.uygulama import App

if __name__ == "__main__":
    try:
        # Windows'ta yüksek DPI uyumluluğu için
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        app = App()
        app.mainloop()
    except ImportError:
        print("Gerekli paketler yok. Kurulum: pip install customtkinter reportlab")
        sys.exit(1)