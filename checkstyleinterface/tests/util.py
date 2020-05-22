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

"""util.py"""

__author__ = "Quoc-Nam Dessoulles"
__email__ = "cokie.forever@gmail.com"
__license__ = "MIT"

import os
import shutil
import stat
import sys
import time
from unittest.mock import patch

from checkstyleinterface import main


def withRetry(xCallable):
    try:
        xCallable()
    except OSError:
        time.sleep(1)
        xCallable()


def removeFolder(sFolderPath):
    if os.path.isdir(sFolderPath):
        def onRmError(sPath):
            os.chmod(sPath, stat.S_IWRITE)
            os.remove(sPath)

        shutil.rmtree(sFolderPath, onerror=lambda *args: onRmError(args[1]))


def assertErrors(lErrors, iErrorsCount, iWarningsCount, iInfoCount):
    for oError in lErrors:
        assert oError is not None
        assert os.path.isfile(oError.sFile)
        assert oError.iLine > 0
        assert oError.iCol >= 0
        assert oError.sSeverity.lower() in ["error", "warning", "info"]
        assert oError.sMessage
        assert not oError.bIgnored
    assert len(lErrors) == iErrorsCount + iWarningsCount + iInfoCount
    assert len([e for e in lErrors if e.sSeverity.lower() == "error"]) == iErrorsCount
    assert len([e for e in lErrors if e.sSeverity.lower() == "warning"]) == iWarningsCount
    assert len([e for e in lErrors if e.sSeverity.lower() == "info"]) == iInfoCount


class BaseTest:
    sResFolder = os.path.abspath(os.path.join(os.path.dirname(__file__), "res"))
    sCheckstyleJarFile = os.path.join(sResFolder, "checkstyle", "checkstyle-8.32-all.jar")
    sPropFile = os.path.join(sResFolder, "checkstyle", "checkstyle.properties")
    sConfigFile = os.path.join(sResFolder, "checkstyle", "checkstyle.xml")
    sGitFolder = os.path.join(sResFolder, "git")

    def setup_method(self):
        with open(self.sPropFile, "w") as oFile:
            oFile.write("config_loc=%s\n" % os.path.dirname(self.sConfigFile).replace("\\", "/"))
        sTmpFolder = os.path.join(self.sResFolder, "tmp")
        removeFolder(sTmpFolder)
        withRetry(lambda: os.makedirs(sTmpFolder))
        sNewGitFolder = os.path.join(sTmpFolder, "git")
        shutil.copytree(self.sGitFolder, sNewGitFolder)
        withRetry(lambda: os.rename(os.path.join(sNewGitFolder, "gitdir"), os.path.join(sNewGitFolder, ".git")))
        self.sGitFolder = sNewGitFolder

    def teardown_method(self):
        sTmpFolder = os.path.join(self.sResFolder, "tmp")
        removeFolder(sTmpFolder)

    def callWithArgs(self, xFunction, lArgs, sJarFile=sCheckstyleJarFile, sConfigFile=sConfigFile):
        lArgs += ["-c", sConfigFile, "-p", self.sPropFile]
        if sJarFile:
            lArgs += ["-j", sJarFile]
        with patch.object(sys, "argv", ["main.py"] + lArgs):
            oArgs = main.parseArgs()
        return xFunction(oArgs)
