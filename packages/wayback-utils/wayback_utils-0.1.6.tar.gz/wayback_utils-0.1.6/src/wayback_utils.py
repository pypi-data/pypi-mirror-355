import time
import requests
import threading
from typing import Callable
from urllib.parse import quote

UNKNOWN_ERROR = 599
PARSE_ERROR = 598


class WayBackStatus:
    """
    Represents the result of a Wayback Machine Status request.

    Attributes:
        `status` (str): Archiving job status, "pending", "success", "error".
        `job_id` (str): The unique identifier of the archiving job to check.
        `original_url` (str): The URL to be archived.
        `screenshot` (str): Screenshot of the website, if requested (capture_screenshot=1).
        `timestamp` (str): Snapshot timestamp.
        `duration_sec` (str): Duration of the archiving process.
        `status_ext` (str): Error code
        `exception` (str): Error
        `message` (str): Additional information about the process.
        `outlinks` (list[str]): List of processed outlinks (outlinks_availability=1).
        `resources` (list[str]): All files downloaded from the web.
        `archive_url` (str): Full link to the website via the Wayback Machine
    """

    status: str = None
    """`status`: Archiving job status, "pending", "success", "error"."""
    job_id: str = None
    """`job_id`: The unique identifier of the archiving job to check."""
    original_url: str = None
    """`original_url`: The URL to be archived."""
    screenshot: str = None
    """`screenshot`: Screenshot of the website, if requested (capture_screenshot=1)."""
    timestamp: str = None
    """`timestamp`: Snapshot timestamp."""
    duration_sec: float = None
    """`duration_sec`: Duration of the archiving process."""
    status_ext: str = None
    """`status_ext`: Error code"""
    exception: str = None
    """`exception`: Error"""
    message: str = None
    """`message`: Additional information about the process."""
    outlinks: list[str] = None
    """`outlinks`: List of processed outlinks (outlinks_availability=1)."""
    resources: list[str] = None
    """`resources`: All files downloaded from the web."""
    archive_url: str = None
    """`archive_url`: Full link to the website via the Wayback Machine"""

    def __init__(self, json):
        self.status = json.get("status", None)
        self.job_id = json.get("job_id", None)
        self.original_url = json.get("original_url", None)
        self.screenshot = json.get("screenshot", None)
        self.timestamp = json.get("timestamp", None)
        self.duration_sec = json.get("duration_sec", None)
        self.resources = json.get("resources", None)
        self.status_ext = json.get("status_ext", None)
        self.exception = json.get("exception", None)
        self.message = json.get("message", None)
        if self.status == "success":
            self.archive_url = f"https://web.archive.org/web/{self.timestamp}id_/{quote(self.original_url)}"


class WayBackSave:
    """
    Represents the result of a Wayback Machine save request.

    Attributes:
        `url` (str): URL to be archived.
        `job_id` (str): The unique identifier of the archiving job to check.
        `message` (str): Any important message about the process.
        `status_code` (int): The save request status code.
    """

    url: str = None
    """`url`: URL to be archived."""
    job_id: str = None
    """`job_id`: The unique identifier of the archiving job to check."""
    message: str = None
    """`message`: Any important message about the process."""
    status_code: int = None
    """`status_code`: The save request status code."""

    def __init__(self, json, status_code):
        self.url = json.get("url", None)
        self.job_id = json.get("job_id", None)
        self.message = json.get("message", None)
        self.status_code = status_code


class WayBack:

    ACCESS_KEY = None
    SECRET_KEY = None
    user_agent = None

    def __init__(
        self,
        ACCESS_KEY,
        SECRET_KEY,
        user_agent="wayback_utils",
    ):
        self.ACCESS_KEY = ACCESS_KEY
        self.SECRET_KEY = SECRET_KEY
        self.user_agent = user_agent
        self.access_check()

    def access_check(self):
        try:
            assert self.ACCESS_KEY and self.SECRET_KEY
        except AssertionError:
            raise ValueError(
                "Authentication error: You must set ACCESS_KEY and SECRET_KEY"
            )

    def save(
        self,
        url: str,
        timeout: int = 300,
        capture_all: bool = False,
        capture_outlinks: bool = False,
        capture_screenshot: bool = False,
        delay_wb_availability: bool = False,
        force_get: bool = False,
        skip_first_archive: bool = True,
        if_not_archived_within: int = 2700,  # 45 min
        outlinks_availability: bool = False,
        email_result: bool = False,
        js_behavior_timeout: int = 5,
        on_result: "Callable[[WayBackStatus], None]" = None,
    ) -> WayBackSave:
        r"""
        Initiates the archiving process of a URL using the Wayback Machine service.

        :param `url`: URL to be archived.
        :param `timeout`: Maximum time (in seconds) to wait for the archiving operation to complete.

        :param `capture_all`: Capture a web page with errors (HTTP status=4xx or 5xx). By default SPN2 captures only status=200 URLs.
        :param `capture_outlinks`: Capture web page outlinks automatically. This also applies to PDF, JSON, RSS and MRSS feeds.
        :param `capture_screenshot`: Capture full page screenshot in PNG format. This is also stored in the Wayback Machine as a different capture.
        :param `delay_wb_availability`: The capture becomes available in the Wayback Machine after ~12 hours instead of immediately. This option helps reduce the load on our systems. All API responses remain exactly the same when using this option.
        :param `force_get`: Force the use of a simple HTTP GET request to capture the target URL. By default SPN2 does a HTTP HEAD on the target URL to decide whether to use a headless browser or a simple HTTP GET request. force_get overrides this behavior.
        :param `skip_first_archive`: Skip checking if a capture is a first if you don’t need this information. This will make captures run faster.
        :param `if_not_archived_within`: Capture web page only if the latest existing capture at the Archive is older than the timedelta limit in seconds, e.g. “120”. If there is a capture within the defined timedelta, SPN2 returns that as a recent capture. The default system timedelta is 45 min.
        :param `outlinks_availability`: Return the timestamp of the last capture for all outlinks.
        :param `email_result`: Send an email report of the captured URLs to the user’s email.
        :param `js_behavior_timeout`: Run JS code for N seconds after page load to trigger target page functionality like image loading on mouse over, scroll down to load more content, etc. The default system N is 5 sec. WARNING: The max <N> value that applies is 30 sec. NOTE: If the target page doesn’t have any JS you need to run, you can use js_behavior_timeout=0 to speed up the capture.
        :param `on_confirmation`: Optional callback called when archiving finishes with the result.

        :return: An object with the request information.
        :rtype: WayBackSave
        """
        payload = {
            "url": url,  # No quote needed.
            "capture_all": int(capture_all == True),
            "capture_outlinks": int(capture_outlinks == True),
            "capture_screenshot": int(capture_screenshot == True),
            "delay_wb_availability": int(delay_wb_availability == True),
            "force_get": int(force_get == True),
            "skip_first_archive": int(skip_first_archive == True),
            "if_not_archived_within": if_not_archived_within,
            "outlinks_availability": int(outlinks_availability == True),
            "email_result": int(email_result == True),
            "js_behavior_timeout": js_behavior_timeout,
            "use_user_agent": self.user_agent,
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "Authorization": f"LOW {self.ACCESS_KEY}:{self.SECRET_KEY}",
        }

        try:
            response = requests.post(
                url="https://web.archive.org/save",
                data=payload,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if e.response is not None:
                return WayBackSave({}, e.response.status_code)
            else:
                return WayBackSave({}, UNKNOWN_ERROR)
        except Exception as e:
            return WayBackSave({}, UNKNOWN_ERROR)

        try:
            response_data = WayBackSave(response.json(), response.status_code)
        except:
            return WayBackSave({}, PARSE_ERROR)  # parse error

        if on_result is not None:

            def poll_status() -> WayBackStatus:
                status_error = WayBackStatus({"status": "error"})
                time.sleep(10)
                while True:
                    try:
                        statusInfo = self.status(response_data.job_id, timeout)
                        match statusInfo.status:
                            case "pending":
                                time.sleep(10)
                            case "success":
                                return on_result(statusInfo)
                            case "error":
                                return on_result(statusInfo)
                            case _:
                                return on_result(status_error)
                    except:
                        return on_result(status_error)

            threading.Thread(target=poll_status, daemon=True).start()

        return response_data

    def status(self, job_id: str, timeout: int = 300) -> WayBackStatus:

        payload = {
            "job_id": job_id,  # No quote needed.
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "Authorization": f"LOW {self.ACCESS_KEY}:{self.SECRET_KEY}",
        }

        try:
            response = requests.post(
                url="https://web.archive.org/save/status",
                data=payload,
                headers=headers,
                timeout=timeout,
            )
            return WayBackStatus(response.json())
        except:
            return WayBackStatus({"status": "error"})

    def indexed(self, url: str, timeout: int = 300) -> bool:
        wayback_api_url = (
            f"http://web.archive.org/cdx/search/cdx?url={quote(url)}"
            + "&fl=timestamp,original"
            + "&output=json"
            + "&page=0"
            + "&pageSize=1"
            + "&limit=1"
            + "&filter=statuscode:^[23][0-9]{2}$"  # from 200 to 399.
        )

        try:
            response = requests.get(url=wayback_api_url, timeout=timeout)
            data = response.json()
            if isinstance(data, list):
                return len(data) > 1
            else:
                return False
        except:
            return False
