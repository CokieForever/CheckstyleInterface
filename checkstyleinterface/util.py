#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2020 Quoc-Nam Dessoulles
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Tkinter utility functions."""

__author__ = "Quoc-Nam Dessoulles"
__email__ = "cokie.forever@gmail.com"
__license__ = "MIT"

import os
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkFont
import tkinter.scrolledtext
from tkinter import ttk

import psutil


def tkVar(oVar, oValue=None, xCallback=None):
    if oValue is not None:
        oVar.set(oValue)
    if xCallback is not None:
        oCallbackWrapper = CallbackWrapper(oVar.get(), xCallback)
        oVar.trace("w", lambda *args: oCallbackWrapper.fireIfNew(oVar.get()))
    return oVar


def stringVar(sValue=None, xCallback=None):
    return tkVar(tk.StringVar(), oValue=sValue, xCallback=xCallback)


def intVar(iValue=None, xCallback=None):
    return tkVar(tk.IntVar(), oValue=iValue, xCallback=xCallback)


def boolVar(bValue=None, xCallback=None):
    return tkVar(tk.BooleanVar(), oValue=bValue, xCallback=xCallback)


class CallbackWrapper:
    def __init__(self, oInitValue, xCallback):
        self.oValue = oInitValue
        self.xCallback = xCallback

    def fireIfNew(self, oValue):
        if oValue != self.oValue:
            self.oValue = oValue
            self.xCallback(oValue)


def label(oRoot, sText):
    return ttk.Label(oRoot, text=sText)


def button(oRoot, sText, xCallback=None):
    return ttk.Button(oRoot, text=sText, command=lambda *oArgs: xCallback() if xCallback else None)


def checkButton(oRoot, sText, bChecked=False, xCallback=None):
    oBoolVar = boolVar(bChecked, xCallback=xCallback)
    oButton = ttk.Checkbutton(oRoot, text=sText, variable=oBoolVar)
    # Keeping a reference is important to prevent garbage collection
    oButton.oBoolVar = oBoolVar
    return oButton


def optionMenu(oRoot, lChoices, sInitValue=None, xCallback=None):
    return OptionMenu(oRoot, lChoices, sInitValue=sInitValue, xCallback=xCallback)


class OptionMenu(ttk.OptionMenu):
    def __init__(self, oRoot, lChoices, sInitValue=None, xCallback=None):
        if sInitValue is None:
            sInitValue = lChoices[0] if lChoices else ""
        self.oStringVar = stringVar(sValue=sInitValue, xCallback=xCallback)
        super().__init__(oRoot, self.oStringVar, sInitValue, *lChoices)

    def updateChoices(self, lNewChoices, sInitValue=None):
        if sInitValue is None:
            sInitValue = lNewChoices[0] if lNewChoices else ""
        oMenu = self["menu"]
        oMenu.delete(0, tk.END)
        for sChoice in lNewChoices:
            oMenu.add_command(label=sChoice, command=lambda s=sChoice: self.oStringVar.set(s))
        self.oStringVar.set(sInitValue)


def entry(oRoot, sInitValue=None, iWidth=None, xCallback=None, bOnlyOnEnterPress=True):
    if bOnlyOnEnterPress:
        oStringVar = stringVar(sValue=sInitValue)
    else:
        oStringVar = stringVar(sValue=sInitValue, xCallback=xCallback)

    if iWidth:
        oEntry = ttk.Entry(oRoot, textvariable=oStringVar, width=iWidth)
    else:
        oEntry = ttk.Entry(oRoot, textvariable=oStringVar)

    if bOnlyOnEnterPress:
        oEntry.bind("<Return>", lambda _: xCallback(oStringVar.get()))

    # Keeping a reference is important to prevent garbage collection
    oEntry.oStringVar = oStringVar
    return oEntry


def comboBox(oRoot, lValues, sInitValue=None, xCallback=None):
    if sInitValue is None:
        sInitValue = lValues[0] if lValues else ""
    oStringVar = stringVar(sValue=sInitValue, xCallback=xCallback)
    oComboBox = ttk.Combobox(oRoot, values=lValues, textvariable=oStringVar)
    # Keeping a reference is important to prevent garbage collection
    oComboBox.oStringVar = oStringVar
    return oComboBox


def scrolledText(oRoot, sInitValue=None):
    oScrolledText = tk.scrolledtext.ScrolledText(oRoot)
    if sInitValue:
        oScrolledText.insert(tkinter.END, sInitValue)
    return oScrolledText


class MultiColumnListbox(ttk.Frame):
    def __init__(self, oMaster, lColumns, **kwargs):
        super().__init__(oMaster, **kwargs)
        self.oTreeView = None
        self.lColumns = lColumns
        self.setupWidgets()
        self.buildTree()

    def setupWidgets(self):
        self.oTreeView = ttk.Treeview(self, columns=self.lColumns, show="headings")
        oVertScrollBar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.oTreeView.yview)
        oHrzScrollBar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.oTreeView.xview)
        self.oTreeView.configure(yscrollcommand=oVertScrollBar.set, xscrollcommand=oHrzScrollBar.set)
        self.oTreeView.grid(column=0, row=0, sticky=tk.N + tk.S + tk.E + tk.W)
        oVertScrollBar.grid(column=1, row=0, sticky=tk.N + tk.S)
        oHrzScrollBar.grid(column=0, row=1, sticky=tk.E + tk.W)
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 0, weight=1)

    def buildTree(self):
        for sColName in self.lColumns:
            self.oTreeView.heading(sColName, text=sColName, command=lambda c=sColName: self.sortByColumn(c, False))
            self.oTreeView.column(sColName, width=tkFont.Font().measure(sColName))

    def setData(self, lData):
        self.oTreeView.delete(*self.oTreeView.get_children())
        lItemIds = []
        for iRowIdx, lRowData in enumerate(lData):
            lItemIds.append(self.oTreeView.insert("", tk.END, values=lRowData))
            for iColIdx, sValue in enumerate(lRowData):
                iColWidth = tkFont.Font().measure(sValue)
                if self.oTreeView.column(self.lColumns[iColIdx], width=None) < iColWidth:
                    self.oTreeView.column(self.lColumns[iColIdx], width=iColWidth)
        return lItemIds

    def getData(self):
        for oRowItem in self.oTreeView.get_children(""):
            yield tuple([self.oTreeView.set(oRowItem, sColName) for sColName in self.lColumns])

    def sortByColumn(self, sColName, bDescending):
        lData = [(self.oTreeView.set(sItemId, sColName), sItemId) for sItemId in self.oTreeView.get_children("")]
        lData.sort(reverse=bDescending)
        for iIdx, (_, sItemId) in enumerate(lData):
            self.oTreeView.move(sItemId, "", iIdx)
        self.oTreeView.heading(sColName, command=lambda: self.sortByColumn(sColName, not bDescending))


def findAll(sText, sExpr):
    iLen = len(sExpr)
    iStart = 0
    while True:
        iStart = sText.find(sExpr, iStart)
        if iStart == -1:
            return
        yield iStart
        iStart += iLen


def getIntellijLocation():
    lProcessesNames = ["idea", "idea64"]
    if os.name == "nt":
        lProcessesNames = [s + ".exe" for s in lProcessesNames]
    for oProcess in psutil.process_iter(["pid", "name", "exe"]):
        try:
            if oProcess.name() in lProcessesNames:
                return oProcess.exe()
        except psutil.Error:
            pass
    return None


def startFile(sFilePath):
    if sys.platform == 'darwin':
        subprocess.Popen(['open', sFilePath])
    elif sys.platform == 'win32':
        os.startfile(sFilePath)
    else:
        subprocess.Popen(['xdg-open', sFilePath])
