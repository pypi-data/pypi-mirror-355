"""
Stub function and module used as a setuptools entry point.
"""

import sys
import augur
from sys import argv, exit

# Entry point for setuptools-installed script and bin/augur dev wrapper.
def main():
    sys.stdout.reconfigure(
        # Support non-Unicode encodings by replacing Unicode characters instead of erroring.
        errors="backslashreplace",

        # Explicitly enable universal newlines mode so we do the right thing.
        newline=None,

        # By default, stdout is line-buffered when interactive (e.g. for
        # consistent stdio interleaving) but block-buffered when not for (I
        # assume) better performance.
    )
    # Apply the above to stderr as well.
    sys.stderr.reconfigure(
        errors="backslashreplace",
        newline=None,

        # By default, stderr is always line-buffered.
    )

    return augur.run( argv[1:] )

# Run when called as `python -m augur`, here for good measure.
if __name__ == "__main__":
    exit( main() )
