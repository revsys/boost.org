#
# Copyright (c) 2024 The C++ Alliance, Inc. (https://cppalliance.org)
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
# Official repository: https://github.com/boostorg/website-v2
#

from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand
from django.contrib.contenttypes.models import ContentType


def gen_version_manager_group(apps, schema_editor):
    from versions.models import Version

    new_group, created = Group.objects.get_or_create(name="version_manager")
    # Code to add permission to group ???
    ct = ContentType.objects.get_for_model(Version)

    # Now what - Say I want to add 'Can add version' permission to new_group?
    permission, created = Permission.objects.get_or_create(
        codename="can_add_version", name="Can add version", content_type=ct
    )
    new_group.permissions.add(permission)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_auto_20211105_0915"),
    ]

    operations = [
        migrations.RunPython(
            gen_version_manager_group, reverse_code=migrations.RunPython.noop
        ),
    ]
