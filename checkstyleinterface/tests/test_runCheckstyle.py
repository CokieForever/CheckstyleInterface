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
import subprocess

import pytest

from checkstyleinterface import main
from checkstyleinterface.tests.util import BaseTest, assertErrors


class TestRunCheckstyle(BaseTest):
    def test_runWithFile(self):
        lErrors = self.callWithArgs(main.runCheckstyle, ["-f", os.path.join(self.sGitFolder, "java", "Test.java")])
        assertErrors(lErrors, 1, 1, 1)

    def test_runWithMultipleFiles(self):
        lErrors = self.callWithArgs(main.runCheckstyle, ["-f", os.path.join(self.sGitFolder, "java", "Test.java"),
                                                         os.path.join(self.sGitFolder, "java", "Foo.java")])
        assertErrors(lErrors, 2, 2, 1)

    def test_runWithFolder(self):
        lErrors = self.callWithArgs(main.runCheckstyle, ["-d", os.path.join(self.sGitFolder, "java")])
        assertErrors(lErrors, 2, 2, 1)

    def test_runWithMultipleFolders(self):
        lErrors = self.callWithArgs(main.runCheckstyle, ["-d", os.path.join(self.sGitFolder, "java"),
                                                         os.path.join(self.sGitFolder, "java", "com")])
        assertErrors(lErrors, 3, 3, 1)

    def test_runWithFolderAndFile(self):
        lErrors = self.callWithArgs(main.runCheckstyle, ["-f", os.path.join(self.sGitFolder, "java", "Test.java"),
                                                         "-d", os.path.join(self.sGitFolder, "java", "com")])
        assertErrors(lErrors, 2, 2, 1)

    def test_runWithFolder_recursive(self):
        lErrors = self.callWithArgs(main.runCheckstyle, ["-d", os.path.join(self.sGitFolder, "java"), "-r"])
        assertErrors(lErrors, 3, 3, 1)

    def test_runWithGit_commitMode(self):
        lErrors = self.callWithArgs(main.runCheckstyle, ["-g", self.sGitFolder, "-m", "commit"])
        assertErrors(lErrors, 2, 2, 1)

    def test_runWithGit_pushMode(self):
        lErrors = self.callWithArgs(main.runCheckstyle, ["-g", self.sGitFolder, "-m", "push"])
        assertErrors(lErrors, 1, 1, 1)

    def test_runWithGit_linesOnly(self):
        lErrors = self.callWithArgs(main.runCheckstyle, ["-g", self.sGitFolder, "-m", "commit", "-l"])
        assertErrors(lErrors, 2, 1, 0)

    def test_runWithEnvironmentVariable(self, monkeypatch):
        monkeypatch.setenv("CHECKSTYLE_JAR_LOC", self.sCheckstyleJarFile)
        lErrors = self.callWithArgs(main.runCheckstyle, ["-f", os.path.join(self.sGitFolder, "java", "Test.java")],
                                    sJarFile="")
        assertErrors(lErrors, 1, 1, 1)

    def test_runFailsWhenNoFileProvided(self):
        with pytest.raises(SystemExit) as oExc:
            self.callWithArgs(main.runCheckstyle, [])
        assert oExc.value.code == 2

    def test_runFailsWhenInvalidConfig(self):
        sFakeConfigFile = os.path.join(self.sGitFolder, "..", "config.xml")
        with open(sFakeConfigFile, "w") as oFile:
            oFile.write("foobar")
        with pytest.raises(subprocess.CalledProcessError):
            self.callWithArgs(main.runCheckstyle, ["-f", os.path.join(self.sGitFolder, "java", "Test.java")],
                              sConfigFile=sFakeConfigFile)
