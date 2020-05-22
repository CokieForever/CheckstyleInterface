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

"""main.py"""

__author__ = "Quoc-Nam Dessoulles"
__email__ = "cokie.forever@gmail.com"
__license__ = "MIT"

import argparse
import os
import re
import subprocess
import sys
import tempfile
import tkinter as tk
import xml.etree.ElementTree as ET
from html import unescape

from checkstyleinterface.application import Application, CheckstyleError
from checkstyleinterface.util import makeExecutable


def main():
    oArgs = parseArgs()
    if oArgs.add_hook:
        sys.exit(addGitHook(oArgs))
    elif oArgs.batch_mode:
        lErrors = list(filter(lambda e: e.sSeverity.lower() == "error", runCheckstyle(oArgs)))
        sys.exit(1 if lErrors else 0)
    else:
        oTkRoot = tk.Tk()
        oTkRoot.minsize(850, 480)
        oApp = Application(oTkRoot, lambda: runCheckstyle(oArgs))
        sys.exit(oApp.mainloop())


def addGitHook(oArgs):
    iRetVal = 0
    for sGitFolder in oArgs.git_project:
        sGitFolder = os.path.abspath(sGitFolder)
        if not os.path.isdir(os.path.join(sGitFolder, ".git")):
            print("WARN: The folder %s is not a git folder, ignored" % sGitFolder)
            iRetVal = 1
            continue

        sHookFile = os.path.join(getHookDir(sGitFolder), "pre-push" if oArgs.git_mode == "push" else "pre-commit")
        if os.path.isfile(sHookFile):
            print("There is already a git hook active in %s, so I will just append mine to the existing file."
                  % sGitFolder)
            sAnswer = input("Is it ok for you? (y/n): ")
            if sAnswer != "y":
                print("Operation cancelled for %s" % sGitFolder)
                iRetVal = 1
                continue
        else:
            os.makedirs(os.path.dirname(sHookFile), exist_ok=True)
            with open(sHookFile, "w") as oFile:
                oFile.write("#!/bin/sh\n")

        makeExecutable(sHookFile)

        lArgs = ["checkinter"]
        lArgs += ["-g", '"%s"' % sGitFolder]
        lArgs += ["-m", oArgs.git_mode]
        if oArgs.batch_mode:
            lArgs += ["-b"]
        if oArgs.directory:
            lArgs += ["-d"] + ['"%s"' % os.path.abspath(s) for s in oArgs.directory]
        if oArgs.file:
            lArgs += ["-f"] + ['"%s"' % os.path.abspath(s) for s in oArgs.file]
        if oArgs.recursive:
            lArgs += ["-r"]
        lArgs += ["-j", '"%s"' % os.path.abspath(oArgs.checkstyle_jar)]
        if oArgs.config_file:
            lArgs += ["-c", '"%s"' % os.path.abspath(oArgs.config_file)]
        if oArgs.prop_file:
            lArgs += ["-p", '"%s"' % os.path.abspath(oArgs.prop_file)]

        with open(sHookFile, "a") as oFile:
            oFile.write("\n# Checkstyle verification\n%s" % " ".join(lArgs))

        print("Added hook in %s" % sGitFolder)

    return iRetVal


def getHookDir(sGitFolder):
    oProcess = subprocess.run(["git", "config", "core.hookspath"], capture_output=True,
                              encoding="utf-8", cwd=sGitFolder)
    if oProcess.returncode != 0:
        print("WARN: Unable to read core.hookspath config value in %s, will assume the standard one" % sGitFolder)
        sHookDir = ""
    else:
        sHookDir = oProcess.stdout.strip()

    if sHookDir:
        sHookDir = os.path.abspath(os.path.join(sGitFolder, sHookDir))
    else:
        sHookDir = os.path.join(sGitFolder, ".git", "hooks")

    return sHookDir


def runCheckstyle(oArgs):
    dFiles = getFilesList(oArgs)
    if not dFiles:
        return []

    lArgs = ["java", "-jar", oArgs.checkstyle_jar, "-f", "xml"]
    if oArgs.config_file:
        sConfigFile = os.path.abspath(oArgs.config_file)
        if not os.path.isfile(sConfigFile):
            print("WARN: The config file %s is not readable, ignored." % sConfigFile)
        else:
            lArgs += ["-c", sConfigFile]
    if oArgs.prop_file:
        sPropFile = os.path.abspath(oArgs.prop_file)
        if not os.path.isfile(sPropFile):
            print("WARN: The properties file %s is not readable, ignored." % sPropFile)
        else:
            lArgs += ["-p", sPropFile]

    with tempfile.TemporaryDirectory() as sTempDir:
        sOutputFile = os.path.join(sTempDir, "output.xml")
        lArgs += ["-o", sOutputFile]
        print("Running checkstyle: %s" % lArgs)
        try:
            subprocess.run(lArgs + list(dFiles.keys()), check=True)
            return []
        except subprocess.CalledProcessError:
            if not os.path.isfile(sOutputFile):
                raise
        oRoot = ET.parse(sOutputFile).getroot()

    lErrors = []
    for oError in checkstyleErrorsFromXml(oRoot):
        lLines = dFiles[oError.sFile]
        if lLines is None or oError.iLine in lLines:
            lErrors.append(oError)

    return lErrors


def checkstyleErrorsFromXml(oRoot):
    for oFileNode in oRoot.findall("file"):
        sFilePath = oFileNode.get("name")
        for oErrorNode in oFileNode.findall("error"):
            oError = CheckstyleError()
            oError.sFile = os.path.abspath(sFilePath)
            oError.iLine = int(oErrorNode.get("line"))
            oError.iCol = int(oErrorNode.get("column")) if "column" in oErrorNode.attrib else 0
            oError.sSeverity = oErrorNode.get("severity")
            oError.sCategory = oErrorNode.get("source").split(".")[-1]
            oError.sMessage = unescape(oErrorNode.get("message"))
            yield oError


def isJavaFile(sFilePath):
    if os.path.splitext(sFilePath)[1].lower() == ".java":
        if os.path.isfile(sFilePath):
            return True
        print("WARN: The file %s is not readable, ignored" % sFilePath)
        return False


def getFilesList(oArgs):
    print("Getting files list...")
    dFiles = {}

    for sFilePath in oArgs.file:
        sFilePath = os.path.abspath(sFilePath)
        if not os.path.isfile(sFilePath):
            print("WARN: The file %s is not readable, ignored" % sFilePath)
            continue
        dFiles[sFilePath] = None

    for sFolder in oArgs.directory:
        sFolder = os.path.abspath(sFolder)
        if not os.path.isdir(sFolder):
            print("WARN: The folder %s is not readable, ignored" % sFolder)
            continue
        for sDirPath, lDirNames, lFileNames in os.walk(sFolder):
            for sFileName in lFileNames:
                sFilePath = os.path.join(sDirPath, sFileName)
                if isJavaFile(sFilePath):
                    dFiles[sFilePath] = None
            if not oArgs.recursive:
                lDirNames.clear()

    if oArgs.lines_only:
        for sFilePath, lLines in getChangedLines(oArgs).items():
            if isJavaFile(sFilePath):
                dFiles[sFilePath] = lLines
    else:
        for sFilePath in getChangedFiles(oArgs):
            if isJavaFile(sFilePath):
                dFiles[sFilePath] = None

    print("%d files to be analyzed." % len(dFiles))
    return dFiles


def getChangedFiles(oArgs):
    lFiles = []
    for sFolder in oArgs.git_project:
        sFolder = os.path.abspath(sFolder)
        try:
            if oArgs.git_mode == "push":
                sOutput = subprocess.run(["git", "--no-pager", "show", "HEAD", "--pretty=", "--name-only"], check=True,
                                         capture_output=True, encoding="utf-8", cwd=sFolder).stdout
            else:
                sOutput = subprocess.run(["git", "--no-pager", "diff", "HEAD", "--name-only"], check=True,
                                         capture_output=True, encoding="utf-8", cwd=sFolder).stdout
        except subprocess.CalledProcessError:
            print("WARN: Unable to run git in the folder %s, ignored" % sFolder)
            continue
        for sRelativeFilePath in sOutput.splitlines():
            sFilePath = os.path.abspath(os.path.join(sFolder, sRelativeFilePath))
            lFiles.append(sFilePath)
    return lFiles


def getChangedLines(oArgs):
    oFileRegex = re.compile(r"\+{3} b/(.*)")
    oDevNullRegex = re.compile(r"\+{3} /dev/null")
    oLinesRegex = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    dChangedLines = {}

    for sFolder in oArgs.git_project:
        sFolder = os.path.abspath(sFolder)
        lArgs = ["git", "--no-pager", "show", "HEAD", "--pretty=", "--unified=0"] if oArgs.git_mode == "push" \
            else ["git", "--no-pager", "diff", "HEAD", "--unified=0"]
        try:
            sOutput = subprocess.run(lArgs, check=True, capture_output=True, encoding="utf-8", cwd=sFolder).stdout
        except subprocess.CalledProcessError:
            print("WARN: Unable to run git in the folder %s, ignored" % sFolder)
            continue

        sCurrentFile = None
        for sLine in sOutput.splitlines():
            oMatch = oFileRegex.match(sLine)
            if oMatch is not None:
                sCurrentFile = os.path.abspath(os.path.join(sFolder, oMatch.group(1).strip()))
            elif oDevNullRegex.match(sLine) is not None:
                sCurrentFile = None
            elif sCurrentFile is not None:
                oMatch = oLinesRegex.match(sLine)
                if oMatch is not None:
                    iStartLine = int(oMatch.group(1))
                    iLinesCount = int(oMatch.group(2)) if oMatch.group(2) else 1
                    if iLinesCount > 0:
                        dChangedLines.setdefault(sCurrentFile, []).extend(
                            list(range(iStartLine, iStartLine + iLinesCount)))

    return dChangedLines


def parseArgs():
    oParser = argparse.ArgumentParser(description="Checkstyle check with user interface")

    oParser.add_argument("-g", "--git-project", help="Git project containing files to check", nargs="*", default=[])
    oParser.add_argument("-m", "--git-mode", choices=["push", "commit"], type=str.lower, default="commit",
                         help="Specifies which files are analyzed in directories specified with -g. In commit mode "
                              "(default), checks only the modified files. In push mode, checks only the files "
                              "modified in the last commit.")
    oParser.add_argument("-l", "--lines-only", help="For files in git projects, check changed lines only instead of "
                                                    "entire files", action="store_true")
    oParser.add_argument("-b", "--batch-mode", help="Batch mode: no interface is opened, "
                                                    "returns 1 if there are Checkstyle failures", action="store_true")
    oParser.add_argument("-d", "--directory", help="Directory containing files to check", nargs="*", default=[])
    oParser.add_argument("-f", "--file", help="File to check", nargs="*", default=[])
    oParser.add_argument("-r", "--recursive", help="Check directories provided with -d recursively",
                         action="store_true")
    oParser.add_argument("-j", "--checkstyle-jar", default=os.getenv("CHECKSTYLE_JAR_LOC"),
                         help="Location of the checkstyle JAR. Alternatively, you can define the environment variable "
                              "CHECKSTYLE_JAR_LOC.")
    oParser.add_argument("-c", "--config-file", help="Location of the checkstyle configuration file")
    oParser.add_argument("-p", "--prop-file", help="Location of the checkstyle properties file")
    oParser.add_argument("-k", "--add-hook", help="Do not run Checkstyle, but instead add a git hook "
                                                  "in the provided git projects", action="store_true")

    oArgs = oParser.parse_args()
    if not oArgs.git_project and not oArgs.directory and not oArgs.file:
        oParser.error("Please provide files to check with -g, -d or -f.")
    if not oArgs.checkstyle_jar:
        oParser.error("Please provide the location of the checkstyle JAR with -j, or define the environment variable "
                      "CHECKSTYLE_JAR_LOC.")
    if not os.path.isfile(oArgs.checkstyle_jar):
        oParser.error("The checkstyle JAR file %s is not readable." % oArgs.checkstyle_jar)
    if oArgs.add_hook and not oArgs.git_project:
        oParser.error("When using -k, please provide at least one git project with -g.")
    if oArgs.lines_only and not oArgs.git_project:
        print("WARN: The -l option will have no effect, as no git project was provided with -g.")
    if oArgs.recursive and not oArgs.directory:
        print("WARN: The -r option will have no effect, as no directory was provided with -d.")

    return oArgs


if __name__ == "__main__":
    main()
