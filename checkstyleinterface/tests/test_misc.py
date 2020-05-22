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

"""test_misc.py"""

__author__ = "Quoc-Nam Dessoulles"
__email__ = "cokie.forever@gmail.com"
__license__ = "MIT"

import os

from checkstyleinterface import main
from checkstyleinterface.tests.util import BaseTest


class TestMisc(BaseTest):
    def test_getChangedLines_commitMode(self):
        dChangedLines = self.callWithArgs(main.getChangedLines, ["-g", self.sGitFolder, "-m", "commit"])
        assert dChangedLines == {
            os.path.join(self.sGitFolder, "java", "Test.java"): [1],
            os.path.join(self.sGitFolder, "java", "com", "Bar.java"): list(range(1, 17)),
            os.path.join(self.sGitFolder, "java", "com", "config.txt"): [1, 3, 5, 6]
        }

    def test_getChangedLines_pushMode(self):
        dChangedLines = self.callWithArgs(main.getChangedLines, ["-g", self.sGitFolder, "-m", "push"])
        assert dChangedLines == {
            os.path.join(self.sGitFolder, "java", "Test.java"): list(range(1, 17)),
            os.path.join(self.sGitFolder, "java", "com", "bu_delete.txt"): [1],
            os.path.join(self.sGitFolder, "java", "com", "config.txt"): list(range(1, 8))
        }

    def test_getChangedFiles_commitMode(self):
        lFiles = self.callWithArgs(main.getChangedFiles, ["-g", self.sGitFolder, "-m", "commit"])
        assert lFiles == [
            os.path.join(self.sGitFolder, "java", "Test.java"),
            os.path.join(self.sGitFolder, "java", "com", "Bar.java"),
            os.path.join(self.sGitFolder, "java", "com", "bu_delete.txt"),
            os.path.join(self.sGitFolder, "java", "com", "config.txt")
        ]

    def test_getChangedFiles_pushMode(self):
        lFiles = self.callWithArgs(main.getChangedFiles, ["-g", self.sGitFolder, "-m", "push"])
        assert lFiles == [
            os.path.join(self.sGitFolder, "java", "Test.java"),
            os.path.join(self.sGitFolder, "java", "com", "bu_delete.txt"),
            os.path.join(self.sGitFolder, "java", "com", "config.txt")
        ]
