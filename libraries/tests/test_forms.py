#
# Copyright (c) 2024 The C++ Alliance, Inc. (https://cppalliance.org)
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
# Official repository: https://github.com/boostorg/website-v2
#
from ..forms import LibraryForm, VersionSelectionForm


def test_library_form_success(tp, library, category):
    form = LibraryForm(data={"categories": [category]})
    assert form.is_valid() is True


def test_version_selection_form(library_version):
    # Test with a valid version
    valid_version = library_version.version
    form = VersionSelectionForm(data={"version": valid_version.pk})
    assert form.is_valid()

    # Test with an invalid version
    form = VersionSelectionForm(data={"version": 9999})
    assert form.is_valid() is False

    # Test with no version selected
    form = VersionSelectionForm(data={"version": None})
    assert form.is_valid() is False
