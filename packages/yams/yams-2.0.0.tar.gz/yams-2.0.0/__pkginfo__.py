# copyright 2004-2025 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact https://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of yams.
#
# yams is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# yams is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with yams. If not, see <https://www.gnu.org/licenses/>.
"""Yams packaging information."""
__docformat__ = "restructuredtext en"

# pylint: disable-msg=W0622

# package name
modname = "yams"

# release version
numversion = (2, 0, 0)
version = ".".join(str(num) for num in numversion)

# license and copyright
license = "LGPL"

# short and long description
description = "entity / relation schema"

# author name and email
author = "Logilab"
author_email = "devel@logilab.fr"

# home page
web = f"https://forge.extranet.logilab.fr/open-source/{modname}"

# mailing list
mailinglist = "mailto://python-projects@lists.logilab.org"

# executable
scripts = ["bin/yams-check", "bin/yams-view"]

install_requires = [
    "setuptools",
    "logilab-common >= 2.1.0, < 3.0.0",
    "typing-extensions >= 4.14.0, < 5.0.0",
    "python-dateutil >= 2.9.0",
    'importlib_metadata; python_version < "3.10"',
]

classifiers = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
]
