""" This module provides a simple tooltip implementation for Tkinter widgets.
    It allows you to add tooltips to any Tkinter widget by creating 
    an instance of the ToolTip class.
    
    This code is part of the ttktooltip package, which provides 
    a tooltip widget for Tkinter.
"""

__copyright__ = """
    Copyright (c) 2025 Prashant Mandal
    All rights reserved.
    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose and without fee or royalty is hereby granted,
    provided that the above copyright notice appear in all copies and that
    both that copyright notice and this permission notice appear in
    supporting documentation or portions thereof, including modifications,
    that you make.

    ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES 
    OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY 
    SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
    FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
    NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
    WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !
"""

__version__ = '0.1.0'
__author__ = 'Prashant Mandal'

import tkinter as tk

BACKGROUND = '#ffffe0'
FOREGROUND = '#000000'
BORDERWIDTH = 1
FONT = ('tahoma', '8', 'normal')
RELIEF = 'solid'

class ToolTip(object):
    def __init__(self, widget, text='', 
                 background=BACKGROUND, foreground=FOREGROUND,
                 borderwidth=BORDERWIDTH, font=FONT, relief=RELIEF):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
        self.background = background
        self.foreground = foreground
        self.borderwidth = borderwidth
        self.font = font
        self.relief = relief

    def show(self, event=None):
        if self.tooltip or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tooltip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background=self.background,
                         foreground=self.foreground, relief=self.relief,
                         borderwidth=self.borderwidth, font=self.font)
        label.pack(ipadx=5, ipady=2)

    def hide(self, event=None):
        tw = self.tooltip
        self.tooltip = None
        if tw:
            tw.destroy()
