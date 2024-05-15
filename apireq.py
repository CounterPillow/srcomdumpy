# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import concurrent.futures
import time

import urllib3
from urllib3.util import Retry


class APIRequestor:
    """Class to handle sending throttled requests to an API"""

    requests_per_min = None
    _history = None
    _pool = None
    _executor = None

    def __init__(self, requests_per_min, user_agent, pool_executors=10):
        self.requests_per_min = requests_per_min
        self._history = list()
        self._pool = urllib3.PoolManager(headers={"User-Agent": user_agent},
                                         retries=Retry(total=10))
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=pool_executors)

    def prune_history(self):
        cur_time = time.monotonic_ns()
        ns = s_to_ns(60)

        while True:
            if len(self._history) > 0 and self._history[0] + ns <= cur_time:
                self._history.pop(0)
            else:
                break

    def submit(self, url, method="GET"):
        """Submit a request to base_url + url

        Sleeps if we're above the request throttling limit.

        urllib3 retries aren't accounted for in the throttling tally.

        Returns a concurrent.futures.Future object.
        """

        backoff = 1
        max_backoff = 60

        while True:
            self.prune_history()
            if len(self._history) >= self.requests_per_min:
                time.sleep(backoff)
                backoff = min(max_backoff, backoff * 2)
                continue
            break

        self._history.append(time.monotonic_ns())

        return self._executor.submit(self._pool.request, method, url)


def s_to_ns(s):
    """Convert seconds to nanoseconds
    """

    return s * 10**9
