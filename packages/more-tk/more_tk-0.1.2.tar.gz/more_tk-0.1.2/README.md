# more_tk

## What is more_tk?

**more_tk** is a super lightweight Python package built as a wrapper around [tkinter](https://tkinter.com/).  
It simplifies basic GUI setup and provides an alternate syntax that’s a little more challenging — perfect for fun projects, experiments, or testing yourself.

> ⚠️ **Disclaimer:** more_tk is not designed to replace tkinter — it's a minimalistic rework for learning, challenges, or simple GUIs.

---

## Getting Started

### Setting Up the Window

To create a basic window:

```python
app = mtk()
```

Then to start the main loop:

```python
mtk_mainloop()
```

### `mtk()` Parameters

You can customize your window using these optional arguments:

| Parameter | Description | Example |
|----------|-------------|---------|
| `geo`    | Sets window size (format: `"widthxheight"`) | `"600x400"` |
| `title`  | Window title (default: `"Wrapped by more_tk"`) | `"My App"` |
| `bg`     | Background color (supports names or hex) | `"lightblue"` or `"#33cc33"` |
| `full`   | Fullscreen toggle (`True` or `False`) | `True` |

---

## Widgets

### Labels

Create a label using:

```python
label_mtk(text="Hello", bg_mtk="white", fg_mtk="black", x=0, y=0)
```

| Parameter | Description |
|-----------|-------------|
| `text`    | Text to display |
| `bg_mtk`  | Background color |
| `fg_mtk`  | Text color |
| `x`, `y`  | Position on screen |

---

### Buttons

Create a button:

```python
button_mtk(text="Click Me", bg_mtk="white", fg_mtk="black", x=100, y=100, command_=my_function)
```

All parameters are the same as `label_mtk`, with the addition of:

- `command_`: The function to call when clicked.

---

### Entry Fields

Create a text input:

```python
entry = entry_mtk(bg_mtk="white", fg_mtk="black", x=50, y=50)
```

You can later use `entry.get()` to retrieve the input text.

---

## Example App

```python
from more_tk import *

def hello():
    print("Hello from more_tk!")

app = mtk(geo="400x300", title="My First App", bg="lightgray")
label_mtk(text="Welcome!", x=150, y=50)
button_mtk(text="Click", command_=hello, x=150, y=100)
mtk_mainloop()
```

---

## Why use more_tk?

- Tiny size — installs in seconds  
- No heavy dependencies  
- Great for challenges or teaching beginners  
- Makes simple GUIs easier to read and build

---