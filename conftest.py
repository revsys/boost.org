#
# Copyright (c) 2024 The C++ Alliance, Inc. (https://cppalliance.org)
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
# Official repository: https://github.com/boostorg/website-v2
#
import pytest
import tempfile
from PIL import Image

from django.core.files import File as DjangoFile

# Include the various pytest fixtures from all of our Django apps tests
# directories
pytest_plugins = [
    "core.tests.fixtures",
    "libraries.tests.fixtures",
    "news.tests.fixtures",
    "users.tests.fixtures",
    "versions.tests.fixtures",
]


@pytest.fixture
def temp_image_file():
    image = Image.new("RGB", (100, 100))

    tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
    image.save(tmp_file)

    tmp_file.seek(0)
    file_obj = DjangoFile(open(tmp_file.name, mode="rb"), name="tmp_file")
    yield file_obj.seek(0)
