# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
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

"""
``Collection of standard SD workflows``
=======================================

.. click:: csspin_workflows.stdworkflows:test
   :prog: spin [test|tests]

.. click:: csspin_workflows.stdworkflows:cept
   :prog: spin [cept|acceptance]

.. click:: csspin_workflows.stdworkflows:preflight
   :prog: spin preflight

.. click:: csspin_workflows.stdworkflows:lint
   :prog: spin lint

.. click:: csspin_workflows.stdworkflows:build
   :prog: spin build
"""

from csspin import invoke, option, task


@task(aliases=["tests"])
def test(
    instance: option(
        "-i",  # noqa: F821
        "--instance",  # noqa: F821
        help="Directory of the CONTACT Elements instance.",  # noqa: F722
    ),
    coverage: option(
        "-c",  # noqa: F821
        "--coverage",  # noqa: F821
        is_flag=True,
        help="Run the tests while collecting coverage.",  # noqa: F722
    ),
    with_test_report: option(
        "--with-test-report",  # noqa: F722
        is_flag=True,
        help="Create a test execution report.",  # noqa: F722
    ),
    args,
):
    """Run all tests defined in this project."""
    invoke(
        "test",
        instance=instance,
        coverage=coverage,
        with_test_report=with_test_report,
        args=args,
    )


@task(aliases=["acceptance"])
def cept(
    cfg,  # pylint: disable=unused-argument
    instance: option(
        "-i",  # noqa: F821
        "--instance",  # noqa: F821
        help="Directory of the CONTACT Elements instance.",  # noqa: F722
    ),
    coverage: option(
        "-c",  # noqa: F821
        "--coverage",  # noqa: F821
        is_flag=True,
        help="Run the tests while collecting coverage.",  # noqa: F722
    ),
    with_test_report: option(
        "--with-test-report",  # noqa: F722
        is_flag=True,
        help="Create a test execution report.",  # noqa: F722
    ),
    args,  # pylint: disable=unused-argument
):
    """Run all acceptance tests defined in this project."""
    invoke(
        "cept",
        instance=instance,
        coverage=coverage,
        with_test_report=with_test_report,
        args=args,
    )


@task(aliases=["check"])
def lint(
    allsource: option(
        "--all",  # noqa: F821
        "allsource",  # noqa: F821
        is_flag=True,
        help="Run for all src- and test-files.",  # noqa: F722
    ),
    args,
):
    """Run all linters defined in this project."""
    invoke("lint", allsource=allsource, args=args)


@task()
def preflight(
    ctx,
    instance: option(
        "-i",  # noqa: F821
        "--instance",  # noqa: F821
        help="Directory of the CONTACT Elements instance.",  # noqa: F722
    ),
):
    """Pre-flight checks.

    Do this before committing else baby seals will die!
    """
    ctx.invoke(test, instance=instance)
    ctx.invoke(cept, instance=instance)


@task()
def build(cfg):  # pylint: disable=unused-argument
    """Workflow which triggers all build tasks."""
    invoke("build")
