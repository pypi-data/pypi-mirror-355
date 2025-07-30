import tkinter as tk

app = None

def mtk(geo="400x400", title="Wrapped by more_tk", bg="white", full=False):
    global app
    if app is None:
        app = tk.Tk()
        app.geometry(geo)
        app.title(title)
        app.config(bg=bg)
        if full == False:
            app.attributes("-fullscreen", False)
        elif full == True:
            app.attributes("-fullscreen", True)
        else:
            print("'full' must be 'True', 'False' or just not set")
    return app

def mtk_mainloop():
    global app
    if app is not None:
        app.mainloop()

def label_mtk(text="No Text, define the text", bg_mtk="white", fg_mtk="black", x=0,y=0):
    label_ = tk.Label(text=text, bg=bg_mtk, fg=fg_mtk)
    label_.place(x=x,y=y)

def button_mtk(text="No Text, define the text", bg_mtk="white", fg_mtk="black", x=0,y=0):
    button_ = tk.Button(text=text, bg=bg_mtk, fg=fg_mtk)
    button_.place(x=x, y=y)