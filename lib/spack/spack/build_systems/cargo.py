# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
import inspect
from typing import List

import llnl.util.filesystem as fs

import spack.builder
import spack.package_base
from spack.directives import build_system, depends_on
from spack.multimethod import when

from ._checks import BaseBuilder, execute_install_time_tests


class CargoPackage(spack.package_base.PackageBase):
    """Specialized class for packages built using a Makefiles."""

    #: This attribute is used in UI queries that need to know the build
    #: system base class
    build_system_class = "CargoPackage"

    build_system("cargo")

    with when("build_system=cargo"):
        # TODO: this seems like it should be depends_on, see
        # setup_dependent_build_environment in cargo for why I kept it like this
        depends_on("rust", type="build")


@spack.builder.builder("cargo")
class CargoBuilder(BaseBuilder):
    """The Cargo builder encodes the most common way of building software with
    a rust Cargo.toml file. It has two phases that can be overridden, if need be:

            1. :py:meth:`~.CargoBuilder.edit`
            2. :py:meth:`~.CargoBuilder.install`

    For a finer tuning you may override:

        +-----------------------------------------------+----------------------+
        | **Method**                                    | **Purpose**          |
        +===============================================+======================+
        | :py:attr:`~.CargoBuilder.install_args`        | Specify arguments    |
        |                                               | to ``cargo install`` |
        +-----------------------------------------------+----------------------+
        | :py:attr:`~.CargoBuilder.test_args`           | Specify arguments    |
        |                                               | to ``cargo test``    |
        +-----------------------------------------------+----------------------+
    """

    phases = ("edit", "install")

    #: Arguments for ``cargo install`` during the :py:meth:`~.CargoBuilder.install` phase
    install_args: List[str] = []

    #: Arguments for ``cargo test`` during the :py:meth:`~.CargoBuilder.check` phase
    test_args: List[str] = []

    #: Callback names for install-time test
    install_time_test_callbacks = ["check"]

    @property
    def build_directory(self):
        """Return the directory containing the main Cargo.toml."""
        return self.pkg.stage.source_path

    def edit(self, pkg, spec, prefix):
        """Edit the sources before calling cargo install. The default is a no-op."""
        pass

    def install(self, pkg, spec, prefix):
        """Run "cargo install"."""
        with fs.working_dir(self.build_directory):
            inspect.getmodule(self.pkg).cargo(
                "install", "--root", self.prefix, "--path", ".", *self.install_args
            )

    spack.builder.run_after("install")(execute_install_time_tests)

    def check(self):
        """Run "cargo test"."""
        with fs.working_dir(self.build_directory):
            inspect.getmodule(self.pkg).cargo("test", *self.test_args)
