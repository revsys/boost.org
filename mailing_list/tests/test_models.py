#
# Copyright (c) 2024 The C++ Alliance, Inc. (https://cppalliance.org)
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
# Official repository: https://github.com/boostorg/website-v2
#
import pytest
from model_bakery import baker


@pytest.fixture
def mailing_list_message_factory():
    def factory(**kwargs):
        return baker.make("mailing_list.MailingListMessage", **kwargs)

    return factory


def test_mailing_list_message_tree_structure(mailing_list_message_factory):
    root = mailing_list_message_factory(subject="Root")
    child1 = mailing_list_message_factory(subject="Child 1", parent=root)
    child2 = mailing_list_message_factory(subject="Child 2", parent=root)
    grandchild1 = mailing_list_message_factory(subject="Grandchild 1", parent=child1)
    grandchild2 = mailing_list_message_factory(subject="Grandchild 2", parent=child1)

    assert root.get_children().count() == 2
    assert child1 in root.get_children()
    assert child2 in root.get_children()

    assert child1.get_children().count() == 2
    assert grandchild1 in child1.get_children()
    assert grandchild2 in child1.get_children()

    assert child2.get_children().count() == 0
    assert grandchild1.get_children().count() == 0
    assert grandchild2.get_children().count() == 0
