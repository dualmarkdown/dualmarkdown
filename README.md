This project provides two pandoc filters for the [Dual Markdown Framework](https://dualmarkdown.github.io/): `dual_md` and `teaching_md`.

The Markdown extensions provided by these filters are described [here](https://dualmarkdown.github.io/documentation).

# Usage

To use any of the two available filters (`dual_md` and `teaching_md`) just use the `-F` option of `pandoc`:

`pandoc -F dual_md -F teaching_md [rest-of-options]`

## Installation

To use these pandoc filters, you must install [Pandoc][pandoc] on your system. It is also highly recommended to install [`pandoc-crossref`][pandoc_crossref] to benefit from all the Markdown extensions provided by the various filters of the Dual Markdown Framework.


[pandoc_crossref]: https://github.com/lierdakil/pandoc-crossref
[pandoc]: http://pandoc.org/

### Binary installation (Windows and Mac OS X only)

In the project's [download page](https://github.com/dualmarkdown/dualmarkdown/releases/latest) you can find a ZIP file containing executable files for Windows and Mac OS X. For the installation, just extract the executable files from the ZIP archive and place them in any directory included in the PATH (e.g. the directory where `pandoc.exe` or the `pandoc` executable was installed on your system). 


### Installation from source

Installing the pandoc filters from source requires [Python], a programming language whose interpreter comes pre-installed on Linux and Mac OS X, and which can be easily installed on [Windows]. Panbuild works with both Python v2.7 and v3.x.

The installation also requires `pip`, a program that downloads and installs modules from the Python Package Index ([PyPI]) or from a specified URL. On Mac OS X, it typically comes installed with your Python distribution. On Windows, make sure you choose to install `pip` during the installation of Python (latest Python installers provide such an option). On a Debian-based system (including Ubuntu), you can install `pip` (as root) as follows:

	apt-get install python-pip

There are basically two ways to install Panbuild from source: with and without `git`.

#### Git-based installation 

This approach is straightforward and perhaps more suitable for Linux and Mac OS X, where the `git` command can be easily installed. In following this approach you can install the filters by using the following command as root:

    pip install git+https://github.com/dualmarkdown/dualmarkdown

To upgrade to the most recent release, proceed as follows:

    pip install --upgrade git+https://github.com/dualmarkdown/dualmarkdown

#### Installation without `git` 

If the one-command installation shown above does not work (i.e. `git` is not installed on your system) you can follow this two-step process:

1. Download a copy of the repository in [ZIP format](github.com/dualmarkdown/dualmarkdown/archive/master.zip) and extract it in a _temporary_ folder on your computer.

2. Then install the filters on your system by running `pip` as follows:
  ```
  pip install <full_path_of_your_temporary_folder>
  ```



