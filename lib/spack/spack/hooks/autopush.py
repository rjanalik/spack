# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import llnl.util.tty as tty

import spack.binary_distribution as bindist
import spack.mirror
from spack.cmd import buildcache as bc

updated_mirrors = set()


def post_install(spec, explicit):
    # Push package to all buildcaches with autopush==True

    # Do nothing if package was not installed from source
    pkg = spec.package
    if pkg.installed_from_binary_cache:
        return

    # Push the package to all autopush mirrors
    for mirror in spack.mirror.MirrorCollection(binary=True, autopush=True).values():
        bindist.push_or_raise(
            spec,
            mirror.push_url,
            bindist.PushOptions(force=True, regenerate_index=False, unsigned=not mirror.signed),
        )
        tty.msg(f"{spec.name}: Pushed to build cache: '{mirror.name}'")


def on_install_done(update_index=False):
    # Exit right away if there are no mirrors to update
    if not updated_mirrors:
        return

    # Exit right away if user does not ask to update buildcache index
    if not update_index:
        return

    # Update index of all autopush mirrors where a package was pushed
    all_mirrors = spack.mirror.MirrorCollection(binary=True, autopush=True)
    update_index_mirrors = [all_mirrors.lookup(mirror) for mirror in updated_mirrors]
    for mirror in update_index_mirrors:
        # Sanity check
        if mirror.get_autopush():
            bc.update_index(mirror)
            tty.msg(f"Updated index of mirror {mirror.name}")
