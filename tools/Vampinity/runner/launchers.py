"""How the runner starts the app on the console: websrv's /launch (the default) or ProsperoMgr's API.

  --launcher websrv        GET http://<console>:<web port>/launch?titleId=<app>, as always. websrv's /launch first
                           kills whatever big app is open; the runner makes sure nothing is open before it.
  --launcher prosperomgr   ProsperoMgr's own web API (asked for by GrowingBlackBeans, PR 38: his console runs
                           ProsperoMgr, not websrv):
                             GET  /api/titles/running   {"title_id": "<id>"}, "" when no big app runs
                             POST /api/titles/launch    body {"title_id": "<id>"}, answers {"ok": true,
                                                        "via_notification": <bool>}, or {"error": "<text>"}
                             GET  /api/thermal          {"ok", "cpu_c", "soc_c", "m2_c", "hottest_c", ...}
                           on port 7070 (ProsperoMgr's README), host and port settable in runner-config.json
                           "launcher".

Where the ProsperoMgr calls come from: ProsperoMgr publishes no separate API document. These three routes are read
from its public source, github.com/notmaj0r/ProsperoMgr (GPL-3.0), commit 231363b (main, 23 Nov 2026):
source/backend/src/api_routes.cpp (the routes and their answers), source/backend/src/titles.cpp (LaunchTitle,
GetRunningTitleId), source/backend/include/http_server.hpp (errors are {"error": ...}) and
source/frontend/src/lib/api.js (its own web page calls them the same way). Release v1.2.1 (15 Nov 2026) has the same
three routes and the same LaunchTitle. Nothing else of ProsperoMgr is used: never its close, kill, fan, file or
install calls.

What its launch does, from that source: it needs a signed-in foreground user; it calls sceSystemServiceLaunchApp for
the title; for a title whose home-screen tile opens a web address it opens the browser instead, and for a tile with
another system address it only posts a notification with a button ("via_notification": true). A notification or
an error stops the start. A tile that opens a web address answers {"ok": true, "via_notification": false} like a
plain launch, so the runner cannot tell it apart here; the boot-trace wait right after catches a start that did not
happen. Unlike websrv's /launch it does NOT close an app
that is already open, so the runner asks /api/titles/running first and starts nothing while any big app runs.

NOT RUN ON A CONSOLE YET. Not known from the source: whether EglantinePS5, started this way, shows its own title id
in /api/titles/running, and what sceSystemServiceLaunchApp does when another app is open. Standard library only.
"""
import http.client
import json
import urllib.error
import urllib.request

KINDS = ("websrv", "prosperomgr")
PROSPEROMGR_PORT = 7070
SOURCE = "github.com/notmaj0r/ProsperoMgr commit 231363b (routes also in release v1.2.1)"


class LaunchRefused(Exception):
    """The launcher did not start the app, and says why. Nothing was started."""


class ProsperoMgr:
    """ProsperoMgr's web API: running title, launch, temperatures. no_answer: the runner's NoAnswer class, raised when
    ProsperoMgr cannot be reached at all (the runner treats that as a network drop)."""

    def __init__(self, host, port, timeout, no_answer=OSError, opener=None):
        self.base = f"http://{host}:{port}"
        self.timeout, self.no_answer = timeout, no_answer
        self.open = opener or urllib.request.urlopen

    def _call(self, method, path, body=None, timeout=None):
        """(HTTP status, parsed JSON or None)."""
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.base + path, data=data, method=method,
                                         headers={"Content-Type": "application/json"} if data is not None else {})
        try:
            with self.open(request, timeout=timeout or self.timeout) as response:
                status, raw = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, raw = error.code, error.read() if hasattr(error, "read") else b""
        except (OSError, http.client.HTTPException) as error:
            raise self.no_answer(f"ProsperoMgr at {self.base} does not answer ({error})") from error
        try:
            return status, json.loads(raw or b"null")
        except ValueError:
            return status, None

    def running(self):
        """The title id of the big app that runs now, "" when none. LaunchRefused when the answer is unclear."""
        status, answer = self._call("GET", "/api/titles/running")
        if status != 200 or not isinstance(answer, dict) or not isinstance(answer.get("title_id"), str):
            raise LaunchRefused(f"ProsperoMgr's /api/titles/running answered HTTP {status} {answer!r}: cannot tell "
                                "whether an app is open")
        return answer["title_id"]

    def thermal(self):
        """ProsperoMgr's /api/thermal answer as it comes (a dict), or None when it gives none."""
        status, answer = self._call("GET", "/api/thermal")
        return answer if status == 200 and isinstance(answer, dict) else None

    def launch(self, title_id):
        """Start title_id. Returns nothing; raises LaunchRefused (with ProsperoMgr's own words) when it did not."""
        now = self.running()
        if now:
            raise LaunchRefused(f"ProsperoMgr says {now} is running. Its launch does not close an open app (websrv's "
                                "/launch does), so nothing was started. Close it first")
        status, answer = self._call("POST", "/api/titles/launch", {"title_id": title_id}, timeout=3 * self.timeout)
        if status != 200 or not isinstance(answer, dict):
            error = answer.get("error") if isinstance(answer, dict) else None
            raise LaunchRefused(f"ProsperoMgr's launch answered HTTP {status}: {error or answer!r}")
        if answer.get("via_notification"):
            raise LaunchRefused("ProsperoMgr only posted a notification with a button for this title (its tile opens a "
                                "system address): nobody is there to press it, so the start is stopped")
        if answer.get("ok") is not True:
            raise LaunchRefused(f"ProsperoMgr's launch answered {answer!r}, not ok")


def describe(args):
    """One line for the plan print."""
    if args.launcher == "prosperomgr":
        return (f"ProsperoMgr at {args.launcher_host or args.host}:{args.launcher_port} (POST /api/titles/launch, "
                f"after GET /api/titles/running shows no open app; from {SOURCE}; not yet run on a console)")
    return "websrv /launch"


def make(args, no_answer):
    """The ProsperoMgr launcher for these arguments, or None for websrv (the console's own /launch is used)."""
    if args.launcher == "prosperomgr":
        return ProsperoMgr(args.launcher_host or args.host, args.launcher_port, args.timeout, no_answer)
    return None
