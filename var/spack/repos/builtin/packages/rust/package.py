# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import re

from spack.package import *


class Rust(Package):
    """The Rust programming language toolchain."""

    homepage = "https://www.rust-lang.org"
    url = "https://static.rust-lang.org/dist/rustc-1.42.0-src.tar.gz"
    git = "https://github.com/rust-lang/rust.git"

    maintainers("alecbcs")

    # Core dependencies
    depends_on("cmake@3.13.4:", type="build")
    depends_on("curl+nghttp2")
    depends_on("libgit2")
    depends_on("ninja", type="build")
    depends_on("openssl")
    depends_on("pkgconfig", type="build")
    depends_on("python", type="build")

    # Compiling Rust requires a previous version of Rust.
    # The easiest way to bootstrap a Rust environment is to
    # download the binary distribution of the compiler and build with that.
    depends_on("rust-bootstrap", type="build")

    # Pre-release version dependencies
    depends_on("rust-bootstrap@beta", type="build", when="@beta")
    depends_on("rust-bootstrap@nightly", type="build", when="@master")
    depends_on("rust-bootstrap@nightly", type="build", when="@nightly")

    # Stable version dependencies
    depends_on("rust-bootstrap@1.59:1.60", type="build", when="@1.60")
    depends_on("rust-bootstrap@1.64:1.65", type="build", when="@1.65")
    depends_on("rust-bootstrap@1.69:1.70", type="build", when="@1.70")

    # When adding a version of Rust you may need to add an additional version
    # to rust-bootstrap as the minimum bootstrapping requirements increase.
    # As a general rule of thumb Rust can be built with either the previous major
    # version or the current version of the compiler as shown above.

    # Pre-release versions.
    # Note: If you plan to use these versions remember to install with
    # `-n` to prevent Spack from failing due to failed checksums.
    #
    #     $ spack install -n rust@pre-release-version
    #
    version("beta")
    version("master", branch="master", submodules=True)
    version("nightly")

    # Stable versions.
    version("1.70.0", sha256="b2bfae000b7a5040e4ec4bbc50a09f21548190cb7570b0ed77358368413bd27c")
    version("1.65.0", sha256="5828bb67f677eabf8c384020582b0ce7af884e1c84389484f7f8d00dd82c0038")
    version("1.60.0", sha256="20ca826d1cf674daf8e22c4f8c4b9743af07973211c839b85839742314c838b7")

    variant(
        "analysis",
        default=False,
        description="Outputs code analysis that can be consumed by other tools",
    )
    variant(
        "clippy",
        default=True,
        description="A bunch of lints to catch common mistakes and improve your Rust code.",
    )
    variant("docs", default=False, description="Build Rust documentation.")
    variant("rustfmt", default=True, description="Formatting tool for Rust code.")
    variant("src", default=True, description="Include standard library source files.")

    extendable = True
    executables = ["^rustc$", "^cargo$"]

    phases = ["configure", "build", "install"]

    @classmethod
    def determine_version(csl, exe):
        output = Executable(exe)("--version", output=str, error=str)
        match = re.match(r"rustc (\S+)", output)
        return match.group(1) if match else None

    def setup_build_environment(self, env):
        # Manually inject the path of ar for build.
        ar = which("ar", required=True)
        env.set("AR", ar.path)

    def configure(self, spec, prefix):
        mkdirp(".cargo")
        with open(join_path(".cargo", "config.toml"), "w") as cfg:
            # Set prefix to install into spack prefix.
            print(f"install.prefix={prefix}", file=cfg)

            # Set relative path to put system configuration files
            # under the Spack package prefix.
            print("install.sysconfdir=etc", file=cfg)

            # Build extended suite of tools so dependent packages
            # packages can build using cargo.
            print("build.extended=true", file=cfg)

            # Build docs if specified by the +docs variant.
            print(f"build.docs={str(spec.satisfies('+docs')).lower()}", file=cfg)

            # Set binary locations for bootstrap rustc and cargo.
            print(f"build.cargo={spec['rust-bootstrap'].prefix.bin.cargo}", file=cfg)
            print(f"build.rustc={spec['rust-bootstrap'].prefix.bin.rustc}", file=cfg)

            # Disable bootstrap LLVM download.
            print("llvm.download-ci-llvm=false", file=cfg)

            output = Executable("openssl")("version", "-d", output=str, error=str)
            ossl = self.spec["openssl"]
            m = re.match('OPENSSLDIR: "([^"]+)"', output)
            if m:
                cert_dir = m.group(1)
            elif ossl.external and ossl.prefix == "/usr":
                cert_dir = "/etc"
            else:
                cert_dir = join_path(ossl.prefix, "etc")
            # Manually inject the path of openssl's certs for build.
            certs = join_path(cert_dir, "openssl/cert.pem")
            print(f"http.cainfo='''{certs}'''", file=cfg)

        flags = []
        # Include both cargo and rustdoc in minimal install to match
        # standard download of rust.
        tools = ["cargo", "rustdoc"]

        # Add additional tools as directed by the package variants.
        if spec.satisfies("+analysis"):
            tools.append("analysis")

        if spec.satisfies("+clippy"):
            tools.append("clippy")

        if spec.satisfies("+src"):
            tools.append("src")

        if spec.satisfies("+rustfmt"):
            tools.append("rustfmt")

        # Compile tools into flag for configure.
        flags.append(f"--tools={','.join(tools)}")

        configure(*flags)

    def build(self, spec, prefix):
        python("./x.py", "build")

    def install(self, spec, prefix):
        python("./x.py", "install")
