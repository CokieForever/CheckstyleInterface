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

"""checkinter.py"""

__author__ = "Quoc-Nam Dessoulles"
__email__ = "cokie.forever@gmail.com"
__license__ = "MIT"

import argparse
import os
import subprocess
import sys
import tempfile
import tkinter as tk
import xml.etree.ElementTree as ET
from html import unescape

from checkstyleinterface.application import Application, CheckstyleError


def main():
    oArgs = parseArgs()
    oTkRoot = tk.Tk()
    oTkRoot.minsize(850, 480)
    oApp = Application(oTkRoot, lambda: runCheckstyle(oArgs))
    sys.exit(oApp.mainloop())


def runCheckstyle(oArgs):
    lFiles = getFilesList(oArgs)
    if not lFiles:
        return []

    lArgs = ["java", "-jar", oArgs.checkstyle_jar, "-f", "xml"]
    if oArgs.config_file:
        sConfigFile = os.path.abspath(oArgs.config_file)
        if not os.path.isfile(sConfigFile):
            print("WARN: The config file %s does not exist, ignored." % sConfigFile)
        else:
            lArgs += ["-c", sConfigFile]
    if oArgs.prop_file:
        sPropFile = os.path.abspath(oArgs.prop_file)
        if not os.path.isfile(sPropFile):
            print("WARN: The properties file %s does not exist, ignored." % sPropFile)
        else:
            lArgs += ["-p", sPropFile]

    with tempfile.TemporaryDirectory() as sTempDir:
        sOutputFile = os.path.join(sTempDir, "output.xml")
        lArgs += ["-o", sOutputFile]
        print("Running checkstyle: %s" % lArgs)
        try:
            subprocess.run(lArgs + lFiles, check=True)
            return []
        except subprocess.CalledProcessError:
            if not os.path.isfile(sOutputFile):
                raise
        oRoot = ET.parse(sOutputFile).getroot()

    return list(checkstyleErrorsFromXml(oRoot))


def checkstyleErrorsFromXml(oRoot):
    for oFileNode in oRoot.findall("file"):
        sFilePath = oFileNode.get("name")
        for oErrorNode in oFileNode.findall("error"):
            oError = CheckstyleError()
            oError.sFile = sFilePath
            oError.iLine = int(oErrorNode.get("line"))
            oError.iCol = int(oErrorNode.get("column")) if "column" in oErrorNode.attrib else 0
            oError.sSeverity = oErrorNode.get("severity")
            oError.sCategory = oErrorNode.get("source").split(".")[-1]
            oError.sMessage = unescape(oErrorNode.get("message"))
            yield oError


def getFilesList(oArgs):
    print("Getting files list...")
    lFiles = []

    for sFilePath in oArgs.file:
        sFilePath = os.path.abspath(sFilePath)
        if not os.path.isfile(sFilePath):
            print("WARN: The file %s does not exist, ignored" % sFilePath)
            continue
        lFiles.append(sFilePath)

    for sFolder in oArgs.directory:
        sFolder = os.path.abspath(sFolder)
        if not os.path.isdir(sFolder):
            print("WARN: The folder %s does not exist, ignored" % sFolder)
            continue
        for sDirPath, lDirNames, lFileNames in os.walk(sFolder):
            for sFileName in lFileNames:
                sFilePath = os.path.join(sDirPath, sFileName)
                if os.path.splitext(sFileName)[1].lower() == ".java" and os.path.exists(sFilePath):
                    lFiles.append(sFilePath)
            if not oArgs.recursive:
                lDirNames.clear()

    for sFolder in oArgs.git_project:
        sFolder = os.path.abspath(sFolder)
        sOutput = ""
        try:
            if oArgs.git_mode == "commit":
                sOutput = subprocess.run(["git", "diff", "HEAD", "--name-only"], check=True, capture_output=True,
                                         encoding="utf-8", cwd=sFolder).stdout
            elif oArgs.git_mode == "push":
                sOutput = subprocess.run(["git", "show", "HEAD", "--pretty=", "--name-only"], check=True,
                                         capture_output=True, encoding="utf-8", cwd=sFolder).stdout
        except subprocess.CalledProcessError:
            print("WARN: Unable to run git in the folder %s, ignored" % sFolder)
            continue
        for sRelativeFilePath in sOutput.splitlines():
            sFilePath = os.path.abspath(os.path.join(sFolder, sRelativeFilePath))
            if os.path.splitext(sFilePath)[1].lower() == ".java" and os.path.exists(sFilePath):
                lFiles.append(sFilePath)

    print("%d files to be analyzed." % len(lFiles))
    return lFiles


def parseArgs():
    oParser = argparse.ArgumentParser(description="Checkstyle check with user interface")

    oParser.add_argument("-g", "--git-project", help="Git project containing files to check", nargs="*", default=[])
    oParser.add_argument("-m", "--git-mode", choices=["push", "commit"], type=str.lower, default="commit",
                         help="Specifies which files are analyzed in directories specified with -g. In commit mode "
                              "(default), checks only the modified files. In push mode, checks only the files "
                              "modified in the last commit.")
    oParser.add_argument("-d", "--directory", help="Directory containing files to check", nargs="*", default=[])
    oParser.add_argument("-f", "--file", help="File to check", nargs="*", default=[])
    oParser.add_argument("-r", "--recursive", help="Check directories provided with -d recursively",
                         action="store_true")
    oParser.add_argument("-j", "--checkstyle-jar", default=os.getenv("CHECKSTYLE_JAR_LOC"),
                         help="Location of the checkstyle JAR. Alternatively, you can define the environment variable "
                              "CHECKSTYLE_JAR_LOC.")
    oParser.add_argument("-c", "--config-file", help="Location of the checkstyle configuration file")
    oParser.add_argument("-p", "--prop-file", help="Location of the checkstyle properties file")

    oArgs = oParser.parse_args()
    if not oArgs.git_project and not oArgs.directory and not oArgs.file:
        oParser.error("Please provide files to check with -g, -d or -f.")
    if not oArgs.checkstyle_jar:
        oParser.error("Please provide the location of the checkstyle JAR with -j, or define the environment variable "
                      "CHECKSTYLE_JAR_LOC.")
    if not os.path.isfile(oArgs.checkstyle_jar):
        oParser.error("The checkstyle JAR file %s does not exist." % oArgs.checkstyle_jar)

    return oArgs


if __name__ == "__main__":
    main()
