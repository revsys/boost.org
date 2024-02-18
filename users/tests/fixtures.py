#
# Copyright (c) 2024 The C++ Alliance, Inc. (https://cppalliance.org)
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
# Official repository: https://github.com/boostorg/website-v2
#
import pytest

from django.utils import timezone

from model_bakery import baker


@pytest.fixture
def user(db):
    """Regular website user"""
    user = baker.make(
        "users.User",
        email="user@example.com",
        first_name="Regular",
        last_name="User",
        last_login=timezone.now(),
        image="static/img/fpo/user.png",
    )
    user.set_password("password")
    user.save()

    return user


@pytest.fixture
def staff_user(db):
    """Staff website user with access to the Django admin"""
    user = baker.make(
        "users.User",
        email="staff@example.com",
        first_name="Staff",
        last_name="User",
        last_login=timezone.now(),
        is_staff=True,
        image="static/img/fpo/user.png",
    )
    user.set_password("password")
    user.save()

    return user


@pytest.fixture
def super_user(db):
    """Superuser with access to everything"""
    user = baker.make(
        "users.User",
        email="super@example.com",
        first_name="Super",
        last_name="User",
        last_login=timezone.now(),
        is_staff=True,
        is_superuser=True,
        image="static/img/fpo/user.png",
    )
    user.set_password("password")
    user.save()

    return user


@pytest.fixture
def assert_messages():
    def _assert_and_fetch(response, expected):
        messages = [
            (m.level_tag, m.message) for m in response.context.get("messages", [])
        ]
        assert messages == expected

    return _assert_and_fetch
