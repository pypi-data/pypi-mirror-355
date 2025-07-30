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

def button_mtk(text="No Text, define the text", bg_mtk="white", fg_mtk="black", x=0,y=0, command_=""):
    button_ = tk.Button(text=text, bg=bg_mtk, fg=fg_mtk, command=command_)
    button_.place(x=x, y=y)

def entry_mtk(bg_mtk="white", fg_mtk="black", x=0, y=0):
    entry_ = tk.Entry(bg=bg_mtk, fg=fg_mtk)
    entry_.place(x=x, y=y)
    return entry_

def bind_mtk(key, cmd):
    global app
    if app is None:
        print("Call mtk() first before binding.")
        return
    final_key = f"<{key}>"
    app.bind(final_key, cmd)