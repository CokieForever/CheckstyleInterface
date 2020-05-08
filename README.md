![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)
![](https://img.shields.io/github/license/CokieForever/CheckstyleInterface)
![](https://img.shields.io/github/workflow/status/CokieForever/CheckstyleInterface/Build)

# Checkstyle Interface

A small UI to use [Checkstyle](https://checkstyle.sourceforge.io/) as a commit hook.

## Description

This is a small tool which runs Checkstyle with provided parameters and displays the found errors in a window, if any.

Primarily, this tool is intended to be used as a pre-commit or pre-push hook, to display Checkstyle issues
automatically and in a more user-friendly way that a simple log display. The user can then choose to ignore the errors
and pursuing with the commit or to cancel the operation.

## Installation

To install the tool, go to the root folder and run:

`pip install .`

This will install the tool and put it in your PATH.

## Usage

Then you can run: `checkinter -c <Checkstyle XML config> -f <file to check>` to check a single file. Use `-d` to check
all files of a directory, and `-g` to check only the modified files of a local Git repository. Moreover, you will need
to specify the location of the Checkstyle JAR to use with either the `-j` option or the `CHECKSTYLE_JAR_LOC`
environment variable. You can download the JAR from here: https://github.com/checkstyle/checkstyle/releases/.

You can run `checkinter --help` for more information about the different options.

If no error is found, the command will simply terminate immediately with a return value of 0. Otherwise, the user
interface will be started and populated with the found errors. The interface can be used to review the errors, after
what the user can close the interface and decide to continue or to cancel. In the first case, the final return
value will be 0, in the second case it will be 1. This return value can be used e.g. in pre-commit hooks, to cancel
the commit according to the choice of the user.

## Uninstallation

Simply run `pip uninstall checkstyleinterface` to uninstall the tool.

## Development status

The application is still being built. Therefore all functionalities may not be available / implemented yet.
