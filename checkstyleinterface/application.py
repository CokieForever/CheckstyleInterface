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

"""application.py"""

__author__ = "Quoc-Nam Dessoulles"
__email__ = "cokie.forever@gmail.com"
__license__ = "MIT"

import os
import subprocess
import tkinter as tk
import tkinter.messagebox
from tkinter import ttk

from checkstyleinterface.util import button, MultiColumnListbox, checkButton, label, getIntellijLocation, startFile


class CheckstyleError:
    def __init__(self):
        self.sFile = None
        self.iLine = None
        self.iCol = None
        self.sSeverity = None
        self.sCategory = None
        self.sMessage = None
        self.bIgnored = False

    def __eq__(self, oOther):
        return ((self.sFile is None and oOther.sFile is None)
                or os.path.normcase(os.path.abspath(self.sFile)) == os.path.normcase(os.path.abspath(oOther.sFile))) \
               and self.iLine == oOther.iLine \
               and self.iCol == oOther.iCol \
               and ((self.sSeverity is None and oOther.sSeverity is None)
                    or self.sSeverity.lower() == oOther.sSeverity.lower()) \
               and self.sCategory == oOther.sCategory \
               and self.sMessage == oOther.sMessage


def getItemValuesFromError(oError):
    sSeverity = oError.sSeverity.title()
    return (sSeverity if not oError.bIgnored else "Ignored (%s)" % sSeverity, oError.sCategory,
            "%s at %d:%d" % (oError.sFile, oError.iLine, oError.iCol), oError.sMessage)


class Application(ttk.Frame):
    def __init__(self, oMaster, lCheckstyleErrorsProvider):
        super().__init__(oMaster)
        self.oMaster = oMaster
        self.lCheckstyleErrorsProvider = lCheckstyleErrorsProvider
        self.oListView = None
        self.dCheckstyleErrors = {}
        self.oIgnoreButton = None
        self.oIgnoreCategoryButton = None
        self.oIgnoreAllButton = None
        self.oUnignoreAllButton = None
        self.oShowIgnoredVar = None
        self.bUnignore = False
        self.oErrorsLabel = None
        self.oWarningsLabel = None

        lCheckstyleErrors = self.lCheckstyleErrorsProvider()
        iErrorCount = len(list(filter(lambda e: e.sSeverity.lower() == "error", lCheckstyleErrors)))
        if iErrorCount == 0:
            print("No Checkstyle error found, leaving")
            self.iRetVal = 0
        else:
            iWarningCount = len(list(filter(lambda e: e.sSeverity.lower() == "warning", lCheckstyleErrors)))
            print("Checkstyle reported %d errors and %d warnings, opening interface" % (iErrorCount, iWarningCount))
            self.iRetVal = 1
            self.winfo_toplevel().title("Checkstyle summary")
            self.oMaster.protocol("WM_DELETE_WINDOW", lambda *args: self.onClose())
            self.pack(fill=tk.BOTH, expand=True)
            self.createWidgets()
            self.populateView(lCheckstyleErrors)

    def mainloop(self, n=0):
        if self.dCheckstyleErrors:
            super().mainloop(n=n)
        return self.iRetVal

    def createWidgets(self):
        self.oListView = MultiColumnListbox(self, ["Severity", "Category", "Source", "Message"],
                                            relief=tk.SUNKEN, borderwidth=1)
        self.oListView.grid(row=0, column=0, sticky=tk.N + tk.E + tk.W + tk.S)
        self.oListView.oTreeView.tag_configure("error", background="#ff7777")
        self.oListView.oTreeView.tag_configure("warning", background="#ffff77")
        self.oListView.oTreeView.tag_configure("info", background="#7777ff")
        self.oListView.oTreeView.tag_configure("error.ignored", background="#ffbbbb", foreground="#777777")
        self.oListView.oTreeView.tag_configure("warning.ignored", background="#ffffbb", foreground="#777777")
        self.oListView.oTreeView.tag_configure("info.ignored", background="#bbbbff", foreground="#777777")
        self.oListView.oTreeView.bind("<ButtonRelease-1>", lambda *args: self.onViewClicked())
        self.oListView.oTreeView.bind("<Double-1>", lambda *args: self.onViewDoubleClicked())

        oButtonsArea = ttk.Frame(self)
        oButtonsArea.grid(row=0, column=1, sticky=tk.N + tk.S, ipadx=10)

        self.oIgnoreButton = button(oButtonsArea, "Ignore", xCallback=lambda: self.onIgnoreButtonClicked())
        self.oIgnoreButton.pack(side=tk.TOP, pady=(5, 0))
        self.oIgnoreCategoryButton = button(oButtonsArea, "Ignore category",
                                            xCallback=lambda: self.onIgnoreCategoryButtonClicked())
        self.oIgnoreCategoryButton.pack(side=tk.TOP)
        self.oIgnoreAllButton = button(oButtonsArea, "Ignore all", xCallback=lambda: self.onIgnoreAllButtonClicked())
        self.oIgnoreAllButton.pack(side=tk.TOP, pady=(15, 0))
        self.oUnignoreAllButton = button(oButtonsArea, "Unignore all",
                                         xCallback=lambda: self.onUnignoreAllButtonClicked())
        self.oUnignoreAllButton.pack(side=tk.TOP)

        oCheckButton = checkButton(oButtonsArea, "Show ignored", bChecked=False,
                                   xCallback=lambda _: self.repopulateView())
        oCheckButton.pack(side=tk.TOP, pady=(15, 0))
        self.oShowIgnoredVar = oCheckButton.oBoolVar

        button(oButtonsArea, "Refresh", xCallback=lambda: self.onRefreshButtonClicked()) \
            .pack(side=tk.BOTTOM, pady=(0, 15))

        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 0, weight=1)

        oValidationArea = ttk.Frame(self)
        oValidationArea.grid(row=1, column=0, columnspan=2, sticky=tk.E + tk.W, ipady=5)

        self.oErrorsLabel = label(oValidationArea, "Errors: 0 (and 0 ignored)")
        self.oErrorsLabel.pack(side=tk.LEFT, padx=(5, 0))
        label(oValidationArea, "|").pack(side=tk.LEFT, padx=10)
        self.oWarningsLabel = label(oValidationArea, "Warnings: 0 (and 0 ignored)")
        self.oWarningsLabel.pack(side=tk.LEFT)

        button(oValidationArea, "Continue", xCallback=lambda: self.onOkButtonClicked()) \
            .pack(side=tk.RIGHT, pady=(10, 0), padx=5)
        button(oValidationArea, "Cancel", xCallback=lambda: self.onCancelButtonClicked()) \
            .pack(side=tk.RIGHT, pady=(10, 0))

    def populateView(self, lCheckstyleErrors):
        bShowIgnored = self.oShowIgnoredVar.get()
        lDisplayedErrors = [e for e in lCheckstyleErrors if bShowIgnored or not e.bIgnored]
        lItemsIds = self.oListView.setData(map(getItemValuesFromError, lDisplayedErrors))
        self.dCheckstyleErrors = {sItemId: lDisplayedErrors[iIdx] for iIdx, sItemId in enumerate(lItemsIds)}
        lHiddenErrors = [e for e in lCheckstyleErrors if not bShowIgnored and e.bIgnored]
        for iIdx, oError in enumerate(lHiddenErrors):
            self.dCheckstyleErrors["__hidden_%d" % iIdx] = oError
        self.doUpdateView()

    def repopulateView(self):
        self.populateView(self.dCheckstyleErrors.values())

    def updateView(self):
        if not self.oShowIgnoredVar.get():
            self.repopulateView()
        else:
            self.doUpdateView()

    def onClose(self):
        self.onOkButtonClicked()

    def onOkButtonClicked(self):
        oIter = (e for e in self.dCheckstyleErrors.values() if not e.bIgnored and e.sSeverity.lower() == "error")
        if next(oIter, None) is not None \
                and tk.messagebox.askquestion("Confirmation",
                                              "There are still errors. Are you sure you want to proceed?",
                                              icon="warning") != "yes":
            return
        self.iRetVal = 0
        self.oMaster.destroy()

    def onCancelButtonClicked(self):
        self.oMaster.destroy()

    def onViewClicked(self):
        self.configureIgnoreButtons()

    def onViewDoubleClicked(self):
        oError = self.dCheckstyleErrors[self.oListView.oTreeView.focus()]
        sIntellijExe = getIntellijLocation()
        if sIntellijExe:
            print("Opening file with IntelliJ")
            lArgs = [sIntellijExe, "--line", str(oError.iLine), "--column", str(oError.iCol), oError.sFile]
            subprocess.Popen(lArgs)
        else:
            print("Opening file with default editor")
            startFile(oError.sFile)

    def onIgnoreButtonClicked(self):
        for sItemId in self.oListView.oTreeView.selection():
            self.dCheckstyleErrors[sItemId].bIgnored = not self.bUnignore
        self.updateView()

    def onIgnoreCategoryButtonClicked(self):
        lCategories = set(self.dCheckstyleErrors[sItemId].sCategory for sItemId in self.oListView.oTreeView.selection())
        for oError in self.dCheckstyleErrors.values():
            if oError.sCategory in lCategories:
                oError.bIgnored = not self.bUnignore
        self.updateView()

    def onIgnoreAllButtonClicked(self):
        for oError in self.dCheckstyleErrors.values():
            oError.bIgnored = True
        self.updateView()

    def onUnignoreAllButtonClicked(self):
        for oError in self.dCheckstyleErrors.values():
            oError.bIgnored = False
        self.updateView()

    def onRefreshButtonClicked(self):
        lOldCheckstyleErrors = list(self.dCheckstyleErrors.values())
        lNewCheckstyleErrors = self.lCheckstyleErrorsProvider()
        for oError in lNewCheckstyleErrors:
            try:
                iIdx = lOldCheckstyleErrors.index(oError)
            except ValueError:
                continue
            oError.bIgnored = lOldCheckstyleErrors[iIdx].bIgnored
        self.populateView(lNewCheckstyleErrors)

    def doUpdateView(self):
        for sItemId, oError in self.dCheckstyleErrors.items():
            if not sItemId.startswith("__hidden_"):
                sTag = oError.sSeverity.lower()
                if oError.bIgnored:
                    sTag = "%s.ignored" % sTag
                self.oListView.oTreeView.item(sItemId, values=getItemValuesFromError(oError), tags=(sTag,))
        self.configureIgnoreButtons()
        self.updateLabels()

    def configureIgnoreButtons(self):
        lSelectedItems = self.oListView.oTreeView.selection()
        if not lSelectedItems:
            self.oIgnoreButton.config(state=tk.DISABLED)
            self.oIgnoreCategoryButton.config(state=tk.DISABLED)
        else:
            self.oIgnoreButton.config(state=tk.NORMAL)
            self.oIgnoreCategoryButton.config(state=tk.NORMAL)
            if len(lSelectedItems) == 1:
                oCheckstyleError = self.dCheckstyleErrors[lSelectedItems[0]]
                self.bUnignore = oCheckstyleError.bIgnored
                if self.bUnignore:
                    self.oIgnoreButton.config(text="Unignore")
                    self.oIgnoreCategoryButton.config(text="Unignore category")
                else:
                    self.oIgnoreButton.config(text="Ignore")
                    self.oIgnoreCategoryButton.config(text="Ignore category")

        dErrors = {e.bIgnored: e for e in self.dCheckstyleErrors.values()}
        self.oIgnoreAllButton.config(state=tk.NORMAL if dErrors.get(False) else tk.DISABLED)
        self.oUnignoreAllButton.config(state=tk.NORMAL if dErrors.get(True) else tk.DISABLED)

    def updateLabels(self):
        lErrors = [e for e in self.dCheckstyleErrors.values() if e.sSeverity.lower() == "error"]
        iIgnoredErrors = len(list(filter(lambda e: e.bIgnored, lErrors)))
        self.oErrorsLabel.config(text="Errors: %d (and %d ignored)"
                                      % (len(lErrors) - iIgnoredErrors, iIgnoredErrors))
        lWarnings = [e for e in self.dCheckstyleErrors.values() if e.sSeverity.lower() == "warning"]
        iIgnoredWarnings = len(list(filter(lambda e: e.bIgnored, lWarnings)))
        self.oWarningsLabel.config(text="Warnings: %d (and %d ignored)"
                                        % (len(lWarnings) - iIgnoredWarnings, iIgnoredWarnings))
