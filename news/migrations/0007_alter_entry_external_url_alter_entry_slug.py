#
# Copyright (c) 2024 The C++ Alliance, Inc. (https://cppalliance.org)
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
# Official repository: https://github.com/boostorg/website-v2
#

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0006_alter_entry_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entry",
            name="external_url",
            field=models.URLField(
                blank=True, default="", max_length=500, verbose_name="URL"
            ),
        ),
        migrations.AlterField(
            model_name="entry",
            name="slug",
            field=models.SlugField(max_length=300, unique=True),
        ),
    ]
