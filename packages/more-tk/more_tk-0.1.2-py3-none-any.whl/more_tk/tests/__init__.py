from more_tk.src.more_tk import entry_mtk, mtk_mainloop, mtk, button_mtk

app = mtk()

entry = entry_mtk(bg_mtk="lightyellow", x=50, y=20)

def show_text():
    print(entry.get())

btn = button_mtk(text="Print Entry", command_=show_text)

app.mainloop()
