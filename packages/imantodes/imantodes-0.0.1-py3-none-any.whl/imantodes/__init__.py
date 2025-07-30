# SPDX-License-Identifier: LGPL-3.0-only
# For initializing the `imantodes` package

# for how __version__ is set:
# https://chatgpt.com/c/684d00a8-1f58-8010-87e3-ae6501b8c991
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('imantodes')
except PackageNotFoundError:
    __version__ = '0.0.0'  # fallback during local dev or testing
