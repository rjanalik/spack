# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Hub(GoPackage):
    """The github git wrapper"""

    homepage = "https://github.com/github/hub"
    url = "https://github.com/github/hub/archive/v2.2.2.tar.gz"
    git = "https://github.com/github/hub.git"

    version("master", branch="master")
    version("2.14.2", sha256="e19e0fdfd1c69c401e1c24dd2d4ecf3fd9044aa4bd3f8d6fd942ed1b2b2ad21a")
