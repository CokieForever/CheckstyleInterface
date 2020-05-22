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

"""test_runAddHook.py"""

__author__ = "Quoc-Nam Dessoulles"
__email__ = "cokie.forever@gmail.com"
__license__ = "MIT"

import os
import subprocess
import sys

from checkstyleinterface import main
from checkstyleinterface.tests.util import BaseTest
from checkstyleinterface.util import makeExecutable


class TestAddHook(BaseTest):
    def test_runWithHook_pushMode(self):
        assert self.callWithArgs(main.addGitHook, ["-g", self.sGitFolder, "-m", "push"]) == 0
        assert os.path.isfile(os.path.join(self.sGitFolder, ".git", "hooks", "pre-push"))

    def test_runWithHook_commitMode_error(self):
        dEnv = self.prepareEnvironment()
        assert self.callWithArgs(main.addGitHook, ["-g", self.sGitFolder, "-m", "commit", "-b"]) == 0
        assert os.path.isfile(os.path.join(self.sGitFolder, ".git", "hooks", "pre-commit"))
        oProcess = subprocess.run(["git", "commit", "-m", "Test"], cwd=self.sGitFolder, env=dEnv)
        assert oProcess.returncode == 1

    def test_runWithHook_commitMode_success(self):
        dEnv = self.prepareEnvironment()
        assert self.callWithArgs(main.addGitHook, ["-g", self.sGitFolder, "-m", "commit", "-b"]) == 0
        assert os.path.isfile(os.path.join(self.sGitFolder, ".git", "hooks", "pre-commit"))
        self.fixFiles()
        oProcess = subprocess.run(["git", "commit", "-m", "Test"], cwd=self.sGitFolder, env=dEnv)
        assert oProcess.returncode == 0

    def fixFiles(self):
        os.remove(os.path.join(self.sGitFolder, "java", "Test.java"))
        sBarFile = os.path.join(self.sGitFolder, "java", "com", "Bar.java")
        sTmpBarFile = sBarFile + ".tmp"
        with open(sBarFile, "r") as oOldFile:
            with open(sTmpBarFile, "w") as oNewFile:
                for sLine in oOldFile:
                    if sLine.startswith("package "):
                        oNewFile.write("package com;\n")
                    else:
                        oNewFile.write(sLine)
        os.replace(sTmpBarFile, sBarFile)

    def prepareEnvironment(self):
        sRootFolder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        sTmpFolder = os.path.abspath(os.path.dirname(self.sGitFolder))
        sCheckinterFile = os.path.join(sTmpFolder, "checkinter")
        with open(sCheckinterFile, "w") as oFile:
            # We write a shell script, but as it will be executed by Git bash, it works on Windows as well
            oFile.write('#!/bin/sh\ncd %s\n%s -m checkstyleinterface.main "$@"'
                        % (sRootFolder.replace("\\", "/"), sys.executable.replace("\\", "/")))
        makeExecutable(sCheckinterFile)
        dEnv = os.environ.copy()
        dEnv["PATH"] = sTmpFolder + os.pathsep + dEnv["PATH"]
        return dEnv
