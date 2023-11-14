# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
import inspect
from typing import List

import llnl.util.filesystem as fs

import spack.builder
import spack.package_base
from spack.directives import build_system, extends
from spack.multimethod import when

from ._checks import BaseBuilder, execute_install_time_tests


class GoPackage(spack.package_base.PackageBase):
    """Specialized class for packages built using a Makefiles."""

    #: This attribute is used in UI queries that need to know the build
    #: system base class
    build_system_class = "GoPackage"

    build_system("go")

    with when("build_system=go"):
        # TODO: this seems like it should be depends_on, see
        # setup_dependent_build_environment in go for why I kept it like this
        extends("go@1.14:", type="build")


@spack.builder.builder("go")
class GoBuilder(BaseBuilder):
    """The Go builder encodes the most common way of building software with
    a golang go.mod file. It has three phases that can be overridden, if need be:

            1. :py:meth:`~.GoBuilder.edit`
            2. :py:meth:`~.GoBuilder.build`
            3. :py:meth:`~.GoBuilder.install`

    For a finer tuning you may override:

        +-----------------------------------------------+--------------------+
        | **Method**                                    | **Purpose**        |
        +===============================================+====================+
        | :py:attr:`~.GoBuilder.install_args`          | Specify arguments to ``go install``   |
        +-----------------------------------------------+--------------------+
        | :py:attr:`~.GoBuilder.test_args`        | Specify arguments to ``go test``   |
        +-----------------------------------------------+--------------------+
    """

    phases = ("edit", "install")

    #: Arguments for ``go install`` during the :py:meth:`~.GoBuilder.install` phase
    install_args: List[str] = []

    #: Arguments for ``go test`` during the :py:meth:`~.GoBuilder.check` phase
    test_args: List[str] = []

    #: Callback names for install-time test
    install_time_test_callbacks = ["check"]

    def setup_build_environment(self, env):
        env.set("GO111MODULE", "on")
        env.set("GOTOOLCHAIN", "local")

    @property
    def build_directory(self):
        """Return the directory containing the main go.mod."""
        return self.pkg.stage.source_path

    def edit(self, pkg, spec, prefix):
        """Edit the sources before calling go build. The default is a no-op."""
        pass

    def install(self, pkg, spec, prefix):
        """Run "go install"."""
        with fs.working_dir(self.build_directory):
            inspect.getmodule(self.pkg).go("install", *self.install_args)

    spack.builder.run_after("install")(execute_install_time_tests)

    def check(self):
        """Run "go test"."""
        with fs.working_dir(self.build_directory):
            inspect.getmodule(self.pkg).go("test", *self.test_args)
