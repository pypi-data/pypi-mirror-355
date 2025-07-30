# ttktooltip

A tooltip widget for Tkinter

Usage

```
ToolTip(myicon, "Click here.")
```

Description

```
# Create a tkinter object
self.myicon = tkinter.Label(self.root, image=None, cursor="hand2")

# Pass the object with your text.
ToolTip(self.myicon, "Click here.")
# Hover the mouse to display the text.
```

Show or destroy the tooltip explicitly.

```
mytooltip = ToolTip(self.myicon, "Click here.")
mytooltip.show()
mytooltip.hide()
```
