#!/usr/bin/env python3
"""Turn a release tag into a conservative archive name, never shell code."""
import re
import sys

def archive_name(tag):
    if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:[-.][A-Za-z0-9.-]+)?', tag):
        raise ValueError('Release tags must use vMAJOR.MINOR.PATCH with an optional safe suffix')
    return f'sentinel-detection-as-code-{tag}.tar.gz'

if __name__ == '__main__':
    try:
        print(archive_name(sys.argv[1]))
    except (IndexError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
