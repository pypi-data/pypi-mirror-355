# Copyright (C) 2019-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

pytest_plugins = [
    "swh.journal.pytest_plugin",
    "swh.loader.pytest_plugin",
    "swh.scheduler.pytest_plugin",
    "swh.storage.pytest_plugin",
]
