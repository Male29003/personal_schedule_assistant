import tkinter as tk
from fe.ui import MainWindow

if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)

    def on_closing():
        app.running = False
        root.destroy()

    root.protocol("WW_DELETE_WINDOW", on_closing)
    root.mainloop()