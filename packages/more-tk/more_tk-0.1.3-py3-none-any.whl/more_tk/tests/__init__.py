from more_tk.src.more_tk import entry_mtk, mtk_mainloop, mtk, button_mtk, bind_mtk

app = mtk()

def printit(event):
    print("'Returned' pressed")
t = bind_mtk(key="Return", cmd=printit)

app.mainloop()
