#
# Copyright (c) 2024 The C++ Alliance, Inc. (https://cppalliance.org)
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
# Official repository: https://github.com/boostorg/website-v2
#
import logging
from .settings import *  # noqa


# Disable migrations for all-the-things
class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


# Disable our logging
logging.disable(logging.CRITICAL)

CELERY_TASK_ALWAYS_EAGER = True

DEBUG = False

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

MIGRATION_MODULES = DisableMigrations()

# User a faster password hasher
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

GITHUB_TOKEN = "changeme"

# Make content relative to the project root
BASE_CONTENT = BASE_DIR / "core/tests/content"  # noqa

# Don't use S3 in tests
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
