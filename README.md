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

This will install the tool and put it in your PATH. More information about `pip`
[here](https://pip.pypa.io/en/stable/).

## Usage

### Command line

Once the tool is installed, you can simply run it, for example:

`checkinter -c <Checkstyle XML config> -f <file to check>`

This checks a single file specified by `-f`. Use `-d` to check all files of a directory, and `-g` to check only the
modified files of a local Git repository. Moreover, you will need to specify the location of the Checkstyle JAR to use
with either the `-j` option or the `CHECKSTYLE_JAR_LOC` environment variable. You can download the JAR from here:
https://github.com/checkstyle/checkstyle/releases/.

The tool is made to be integrated with [Git](https://git-scm.com/). For example, you can check only the files
modified by the last commit in a local Git repository:

`checkinter -c <Checkstyle XML config> -g <Git repository> -m push`

Or only the lines changed since the last commit:

`checkinter -c <Checkstyle XML config> -g <Git project> -l`

Simply run `checkinter --help` for more information about the different options.

If no error is found, the command will simply terminate immediately with a return value of 0. Otherwise, the user
interface will be started and populated with the found errors. The interface can be used to review the errors, after
what the user can close the interface and decide to continue or to cancel. In the first case, the final return
value will be 0, in the second case it will be 1. This return value can be used e.g. in pre-commit hooks, to cancel
the commit according to the choice of the user - see the next section.

### Commit hook

You can use the command line to install a pre-commit or a pre-push hook in your git repositories, by using the `-k`
option. For example:

`checkinter -c <Checkstyle XML config> -g <Git repository> -k`

This will install a pre-commit hook in the specified Git repository, which will run
`checkinter -c <Checkstyle XML config> -g <Git repository>` before every commit. To install a pre-push commit, you can
use:

`checkinter -c <Checkstyle XML config> -g <Git repository> -m push -k`

When installing a hook, all options are preserved (obviously except the `-k` option itself), so additional files
passed with `-d` or `-f` will be checked by the hook as well, even if they don't belong to the repository. If a hook
is already present, the tool will simply add its command line at the end, after asking confirmation.

## Uninstallation

Simply run `pip uninstall checkstyleinterface` to uninstall the tool. Note that this will not remove the hooks you
added in your Git repositories. You will need to remove them manually or they won't run anymore. See
[here](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) for more information about Git hooks.

## Development status

The application is still being built. Therefore all functionalities may not be available / implemented yet.
