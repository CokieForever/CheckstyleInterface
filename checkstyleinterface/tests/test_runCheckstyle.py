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

"""test_runCheckstyle.py"""

__author__ = "Quoc-Nam Dessoulles"
__email__ = "cokie.forever@gmail.com"
__license__ = "MIT"

import os
import shutil
import stat
import subprocess
import sys
import time
from unittest.mock import patch

from checkstyleinterface import main
import pytest


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


class TestRunCheckstyle:
    sResFolder = os.path.abspath(os.path.join(os.path.dirname(__file__), "res"))
    sCheckstyleJarFile = os.path.join(sResFolder, "checkstyle", "checkstyle-8.32-all.jar")
    sPropFile = os.path.join(sResFolder, "checkstyle", "checkstyle.properties")
    sConfigFile = os.path.join(sResFolder, "checkstyle", "checkstyle.xml")
    sGitFolder = os.path.join(sResFolder, "git")

    @classmethod
    def setup_class(cls):
        with open(cls.sPropFile, "w") as oFile:
            oFile.write("config_loc=%s\n" % os.path.dirname(cls.sConfigFile).replace("\\", "/"))
        sTmpFolder = os.path.join(cls.sResFolder, "tmp")
        removeFolder(sTmpFolder)
        withRetry(lambda: os.makedirs(sTmpFolder))
        sNewGitFolder = os.path.join(sTmpFolder, "git")
        shutil.copytree(cls.sGitFolder, sNewGitFolder)
        withRetry(lambda: os.rename(os.path.join(sNewGitFolder, "gitdir"), os.path.join(sNewGitFolder, ".git")))
        cls.sGitFolder = sNewGitFolder

    @classmethod
    def teardown_class(cls):
        sTmpFolder = os.path.join(cls.sResFolder, "tmp")
        removeFolder(sTmpFolder)

    def callRunCheckstyle(self, lArgs, sJarFile=sCheckstyleJarFile, sConfigFile=sConfigFile):
        lArgs += ["-c", sConfigFile, "-p", self.sPropFile]
        if sJarFile:
            lArgs += ["-j", sJarFile]
        with patch.object(sys, "argv", ["main.py"] + lArgs):
            oArgs = main.parseArgs()
        return main.runCheckstyle(oArgs)

    def test_runWithFile(self):
        lErrors = self.callRunCheckstyle(["-f", os.path.join(self.sGitFolder, "java", "Test.java")])
        assertErrors(lErrors, 1, 1, 1)

    def test_runWithMultipleFiles(self):
        lErrors = self.callRunCheckstyle(["-f", os.path.join(self.sGitFolder, "java", "Test.java"),
                                          os.path.join(self.sGitFolder, "java", "Foo.java")])
        assertErrors(lErrors, 2, 2, 1)

    def test_runWithFolder(self):
        lErrors = self.callRunCheckstyle(["-d", os.path.join(self.sGitFolder, "java")])
        assertErrors(lErrors, 2, 2, 1)

    def test_runWithMultipleFolders(self):
        lErrors = self.callRunCheckstyle(["-d", os.path.join(self.sGitFolder, "java"),
                                          os.path.join(self.sGitFolder, "java", "com")])
        assertErrors(lErrors, 3, 3, 1)

    def test_runWithFolderAndFile(self):
        lErrors = self.callRunCheckstyle(["-f", os.path.join(self.sGitFolder, "java", "Test.java"),
                                          "-d", os.path.join(self.sGitFolder, "java", "com")])
        assertErrors(lErrors, 2, 2, 1)

    def test_runWithFolder_recursive(self):
        lErrors = self.callRunCheckstyle(["-d", os.path.join(self.sGitFolder, "java"), "-r"])
        assertErrors(lErrors, 3, 3, 1)

    def test_runWithGit_commitMode(self):
        lErrors = self.callRunCheckstyle(["-g", self.sGitFolder, "-m", "commit"])
        assertErrors(lErrors, 1, 1, 0)

    def test_runWithGit_pushMode(self):
        lErrors = self.callRunCheckstyle(["-g", self.sGitFolder, "-m", "push"])
        assertErrors(lErrors, 1, 1, 1)

    def test_runWithEnvironmentVariable(self, monkeypatch):
        monkeypatch.setenv("CHECKSTYLE_JAR_LOC", self.sCheckstyleJarFile)
        lErrors = self.callRunCheckstyle(["-f", os.path.join(self.sGitFolder, "java", "Test.java")], sJarFile="")
        assertErrors(lErrors, 1, 1, 1)

    def test_runFailsWhenNoFileProvided(self):
        with pytest.raises(SystemExit) as oExc:
            self.callRunCheckstyle([])
        assert oExc.value.code == 2

    def test_runFailsWhenInvalidConfig(self):
        sFakeConfigFile = os.path.join(self.sGitFolder, "..", "config.xml")
        with open(sFakeConfigFile, "w") as oFile:
            oFile.write("foobar")
        with pytest.raises(subprocess.CalledProcessError):
            self.callRunCheckstyle(["-f", os.path.join(self.sGitFolder, "java", "Test.java")],
                                   sConfigFile=sFakeConfigFile)
