import time
import requests
import threading
from typing import Callable
from urllib.parse import quote

UNKNOWN_ERROR = 599
PARSE_ERROR = 598


class WayBackStatus:
    status: str = None
    job_id: str = None
    original_url: str = None
    screenshot: str = None
    timestamp: str = None
    duration_sec: str = None
    exception: str = None
    status_ext: str = None
    message: str = None
    outlinks: list[str] = None
    resources: list[str] = None
    archive_url: str = None

    def __init__(self, json):
        self.status = json.get("status", None)
        self.job_id = json.get("job_id", None)
        self.original_url = json.get("original_url", None)
        self.screenshot = json.get("screenshot", None)
        self.timestamp = json.get("timestamp", None)
        self.duration_sec = json.get("duration_sec", None)
        self.resources = json.get("resources", None)
        self.exception = json.get("exception", None)
        self.status_ext = json.get("status_ext", None)
        self.message = json.get("message", None)
        if self.status == "success":
            self.archive_url = f"https://web.archive.org/web/${self.timestamp}id_/${quote(self.original_url, safe='')}"


class WayBackSave:
    url: str = None
    job_id: str = None
    message: str = None
    status_code: int = None

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
        capture_all=0,
        capture_outlinks=0,
        capture_screenshot=0,
        delay_wb_availability=0,
        force_get=0,
        skip_first_archive=1,
        outlinks_availability=0,
        email_result=0,
        on_confirmation: "Callable[[WayBackStatus], None]" = None,
    ) -> WayBackSave:

        payload = {
            "url": url,  # No quote needed.
            "capture_all": capture_all,
            "capture_outlinks": capture_outlinks,
            "capture_screenshot": capture_screenshot,
            "delay_wb_availability": delay_wb_availability,
            "force_get": force_get,
            "skip_first_archive": skip_first_archive,
            "outlinks_availability": outlinks_availability,
            "email_result": email_result,
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "Authorization": f"LOW {self.ACCESS_KEY}:{self.SECRET_KEY}",
        }

        response = None

        try:
            response = requests.post(
                url="https://web.archive.org/save",
                data=payload,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
        except:
            if response is not None and response.status_code is not None:
                return WayBackSave({}, response.status_code)
            else:
                return WayBackSave({}, UNKNOWN_ERROR)  # unknown error

        try:
            responseData = WayBackSave(response.json(), response.status_code)
        except:
            return WayBackSave({}, PARSE_ERROR)  # parse error

        if on_confirmation is not None:

            def poll_status() -> WayBackStatus:
                time.sleep(10)
                while True:
                    try:
                        statusInfo = self.status(responseData.job_id, timeout)
                        match statusInfo.status:
                            case "pending":
                                time.sleep(10)
                            case "success":
                                return on_confirmation(statusInfo)
                            case "error":
                                return on_confirmation(statusInfo)
                    except:
                        return on_confirmation(WayBackStatus({"status": "error"}))

            threading.Thread(target=poll_status, daemon=True).start()

        return responseData

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
        waybackApiUrl = (
            f"http://web.archive.org/cdx/search/cdx?url={quote(url, safe='')}"
            + "&fl=timestamp,original"
            + "&output=json"
            + "&page=0"
            + "&pageSize=1"
            + "&limit=1"
            + "&filter=statuscode:^[23][0-9]{2}$"  # from 200 to 399.
        )

        try:
            response = requests.get(url=waybackApiUrl, timeout=timeout)
            data = response.json()
            if isinstance(data, list):
                return len(data) > 1
            else:
                return False
        except:
            return False
