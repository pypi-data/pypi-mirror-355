#
# c-apidocs - API Documentation Utilities
#

import os
import pathlib
import re
import sys

import hawkmoth
import hawkmoth.util.compiler
import hawkmoth.util.readthedocs


def hawkmoth_conf():
    try:
        hawkmoth.util.readthedocs.clang_setup()
    except Exception:
        sys.stderr.write('Error: Cannot setup Hawkmoth-clang\n')
        raise


def hawkmoth_converter(comment):
    """Custom kernel-doc conversion to reStructuredText"""

    if re.search(
                r"(?m)\Astruct [^-]+? - ",
                comment,
            ) is not None:
        #
        # Convert structs:
        #

        # Strip entity-name from synopsis.
        comment = re.sub(
            r"(?m)\Astruct ([^-]+?) - ",
            "",
            comment,
        )
        # Convert member descriptions.
        comment = re.sub(
            r"(?m)^@([a-zA-Z0-9_]+):",
            "\n:member \\1:",
            comment,
        )

    elif re.search(
                r"(?m)\A[^-]+?() - ",
                comment,
            ) is not None:
        #
        # Convert functions:
        #

        # Strip entity-name from synopsis.
        comment = re.sub(
            r"(?m)\A([ \t]*)([^-]+?) - ",
            "",
            comment,
        )
        # Convert parameter descriptions.
        comment = re.sub(
            r"(?m)^([ \t]*)@([a-zA-Z0-9_]+|\.\.\.):",
            "\n\\1:param \\2:",
            comment,
        )
        # Convert return-value section.
        comment = re.sub(
            r"(?m)^([ \t]*)([Rr]eturns?):",
            "\n\\1:return:",
            comment,
        )

    elif re.search(
                r"(?m)\ADOC:",
                comment,
            ) is not None:
        #
        # Convert section docs:
        #

        # Insert section header
        comment = re.sub(
            r"(?m)\ADOC: (.+)$",
            "\\1\n" + "-"*120 + "\n",
            comment,
        )
        # Insert section without header
        comment = re.sub(
            r"(?m)\ADOC:$",
            "",
            comment,
        )

    return comment


def hawkmoth_include_args():
    return hawkmoth.util.compiler.get_include_args()

def hawkmoth_glob_includes(path, glob):
    entries = []
    for entry in pathlib.Path(path).glob(glob):
        entries += ["-I" + os.path.abspath(str(entry))]
    return entries


def _process_docstring(app, lines, transform, options):
    if transform != 'kerneldoc':
        return

    comment = '\n'.join(lines)
    comment = hawkmoth_converter(comment)
    lines[:] = comment.splitlines()[:]

def setup(app):
    """c-apidocs kernel-doc extension for hawkmoth"""

    app.setup_extension('hawkmoth')
    app.connect('hawkmoth-process-docstring', _process_docstring)

    return {
        'parallel_read_safe': True,
    }
