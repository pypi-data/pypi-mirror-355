# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import concurrent.futures
from threading import local
import time
from datetime import timedelta
from typing import cast

COMMON_EXECUTOR = concurrent.futures.ThreadPoolExecutor()


def sleep_for(duration: timedelta):
    """
    Sleep for the specified duration.
    Args:
        duration (timedelta): The amount of time to sleep.
    """
    time.sleep(duration.total_seconds())


class ThreadLocal[T]:
    def __init__(self, default: T):
        self._local = local()
        self._local.value = default

    def set(self, value: T) -> None:
        self._local.value = value

    def get(self) -> T:
        return cast(T, self._local.value)
