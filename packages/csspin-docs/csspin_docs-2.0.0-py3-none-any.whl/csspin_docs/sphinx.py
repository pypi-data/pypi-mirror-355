# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
# https://www.contact-software.com/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module implementing the sphinx plugin for csspin"""

from csspin import config, rmtree, setenv, sh, task

defaults = config(
    docs="{spin.project_root}/doc",
    opts="-qaE",
    build_dir="{sphinx.docs}/_build",
    requires=config(
        spin=["csspin_python.python"],
        python=["sphinx"],
    ),
)


def cleanup(cfg):  # pylint: disable=unused-argument
    """Clear sphinx's build directory"""
    rmtree("{sphinx.build_dir}")


@task()
def docs(cfg, args):
    """Build the documentation using sphinx"""
    setenv(LATEXMKOPTS="-silent")
    sh(
        "sphinx-build",
        "-M",
        *args,
        cfg.sphinx.docs,
        cfg.sphinx.build_dir,
        cfg.sphinx.opts,
    )
