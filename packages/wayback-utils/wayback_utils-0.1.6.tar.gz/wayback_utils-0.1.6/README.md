[![Python support](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13%20|%203.14-blue)](https://pypi.org/project/wayback-utils/)
[![PyPI Downloads](https://static.pepy.tech/badge/wayback-utils)](https://pepy.tech/projects/wayback-utils)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](https://opensource.org/licenses/MIT)

# wayback_utils.py

This module provides a Python interface to interact with the Wayback Machine web page archiving service (web.archive.org). It allows you to save URLs, check the status of archiving jobs, and verify if a URL has already been indexed.

Based on [SPN2 Public API Docs](https://archive.org/details/spn-2-public-api-page-docs-2023-01-22)

# Installation
```pip install wayback_utils```

# Usage:
> [!NOTE]  
> You need valid access keys to use the archiving API. 
> You can obtain your `ACCESS_KEY` and `SECRET_KEY` from your [archive.org](https://archive.org/account/s3.php).

Import WayBack classes:
```python
    from wayback_utils import WayBack, WayBackStatus, WayBackSave
```

Initialize the WayBack class with your access keys:
```python    
    wb = WayBack(ACCESS_KEY="your_access_key", SECRET_KEY="your_secret_key")
```

Start saving process:
```python
    result = wb.save("https://example.com")
```

You can also pass a callback function to `save()` using the `on_result` parameter. This callback will be called asynchronously with the final result of the archiving operation:

```python
    def my_callback(result):
        print("Archiving finished:", result.status)

    result = wb.save("https://example.com", on_result=my_callback)
```

Check the status of a job:
```python
    status = wb.status(result.job_id)
```

Verify if a URL is already indexed:
```python
    is_indexed = wb.indexed("https://example.com")
```

> [!WARNING]  
> URLs archived with the Wayback Machine may take up to 12 hours to become fully indexed and discoverable.

# Functions
These are the functions provided by the `WayBack` class.

## save
The `save( )` function accepts several optional parameters to customize the capture process:

### Parameters
|Parameter|Type|Description|
|-|-|-|
`url`|str|The URL to be archived.
`timeout`|int| Maximum time (in seconds) to wait for the archiving operation to complete.
`capture_all`|bool| Capture a web page with errors (HTTP status=4xx or 5xx). By default SPN2 captures only status=200 URLs.
`capture_outlinks`|bool| Capture web page outlinks automatically. This also applies to PDF, JSON, RSS and MRSS feeds.
`capture_screenshot`|bool| Capture full page screenshot in PNG format. This is also stored in the Wayback Machine as a different capture.
`delay_wb_availability`|bool| The capture becomes available in the Wayback Machine after ~12 hours instead of immediately. This option helps reduce the load on our systems. All API responses remain exactly the same when using this option.
`force_get`|bool| Force the use of a simple HTTP GET request to capture the target URL. By default SPN2 does a HTTP HEAD on the target URL to decide whether to use a headless browser or a simple HTTP GET request. force_get overrides this behavior.
`skip_first_archive`|bool| Skip checking if a capture is a first if you don’t need this information. This will make captures run faster.
`if_not_archived_within`|int| Capture web page only if the latest existing capture at the Archive is older than the limit in seconds, e.g. “120”. If there is a capture within the defined timedelta, SPN2 returns that as a recent capture. The default system timedelta is 45 min.
`outlinks_availability`|bool| Return the timestamp of the last capture for all outlinks.
`email_result`|bool| Send an email report of the captured URLs to the user’s email.
`js_behavior_timeout`|int| Run JS code for `N` seconds after page load to trigger target page functionality like image loading on mouse over, scroll down to load more content, etc. The default system `N` is 5 sec. WARNING: The max `N` value that applies is 30 sec. NOTE: If the target page doesn’t have any JS you need to run, you can use js_behavior_timeout=0 to speed up the capture.
`on_result`|callback| Optional callback called when archiving finishes.

### Returns
Returns a `WayBackSave` object with details about the save job.
|Attributes|Type|Description|
|-|-|-|
`url`|str| The URL to be archived.
`job_id`|str| The unique identifier of the archiving job to check.
`message`|str| Any important message about the processs.
`status_code`|int| The save request status code.

### Performance Tips

- If you don’t need to know if your capture is the first in the Archive, please use `skip_first_archive`=True.
- If you are sure that the target URL is not an HTML page and can be downloaded via a plain HTTP request, use option `force_get`=True.
- If the target HTML page is plain and you don’t need to run any JS behavior to download all content (JS behaviors scroll down the page automatically and/or trigger AJAX requests), use `js_behavior_timeout`=False.
- Do NOT use `capture_outlinks`=True unless it is really necessary to capture all outlinks. If you are interested in capturing a specific outlink, make a capture, check the list of outlinks returned by SPN2 and capture only the specific outlink(s) you need.

## status
The `status( )` function checks the status of an archiving job.
### Parameters
|Parameter|Type|Description|
|-|-|-|
`job_id`|str| The unique identifier of the archiving job to check.
`timeout`|int| Maximum time in seconds to wait for the status response.

### Returns
Returns a `WayBackStatus` object with details about the job's progress or result.
|Attributes|Type|Description|
|-|-|-|
`status`|str| Archiving job status, "pending", "success", "error".
`job_id`|str| The unique identifier of the archiving job to check.
`original_url`|str| The URL to be archived.
`screenshot`|str| Screenshot of the website, if requested (capture_screenshot=True).
`timestamp`|str| Snapshot timestamp.
`duration_sec`|float| Duration of the archiving process.
`status_ext`|str| [Error code](#error-codes) identifier.
`exception`|str| Error 
`message`|str| Additional information about the process.
`outlinks`|list[str]| List of processed outlinks (outlinks_availability=True).
`resources`|list[str]| All files downloaded from the web.
`archive_url`|str| Full link to the website via the Wayback Machine

## indexed:
The `indexed( )` function checks if a given URL has already been archived and indexed by the Wayback Machine.
### Parameters
|Parameter|Type|Description|
|-|-|-|
`url`|str| The URL to check for existing archives.
`timeout`|int| Maximum time in seconds to wait for the response.

### Returns 
`True` if the URL has at least one valid (HTTP 2xx or 3xx) archived snapshot, otherwise `False`.

## Error Codes
|status_ext|Description|
|-|-|
`error:bad-gateway`| Bad Gateway for URL (HTTP status=502).
`error:bad-request`| The server could not understand the request due to invalid syntax. (HTTP status=401)
`error:bandwidth-limit-exceeded`| The target server has exceeded the bandwidth specified by the server administrator. (HTTP status=509).
`error:blocked`| The target site is blocking us (HTTP status=999).
`error:blocked-client-ip`| Anonymous clients listed in [Spamhaus XBL](https://www.spamhaus.org/xbl/) or [SBL](https://www.spamhaus.org/sbl/) are blocked. Tor exit nodes are excluded.
`error:blocked-url`| URL is on a block list based on Mozilla web tracker lists to avoid unwanted captures.
`error:browsing-timeout`| SPN2 back-end headless browser timeout.
`error:capture-location-error`| SPN2 back-end cannot find the created capture location (system error).
`error:cannot-fetch`| Cannot fetch the target URL due to system overload.
`error:celery`| Cannot start capture task.
`error:filesize-limit`| Cannot capture web resources over 2GB.
`error:ftp-access-denied`| Tried to capture an FTP resource but access was denied.
`error:gateway-timeout`| The target server didn't respond in time. (HTTP status=504).
`error:http-version-not-supported`| The target server does not support the HTTP protocol version used in the request (HTTP status=505).
`error:internal-server-error`| SPN internal server error.
`error:invalid-url-syntax`| Target URL syntax is not valid.
`error:invalid-server-response`| The target server response was invalid (e.g. invalid headers, invalid content encoding, etc).
`error:invalid-host-resolution`| Couldn’t resolve the target host.
`error:job-failed`| Capture failed due to system error.
`error:method-not-allowed`| The request method is known by the server but has been disabled and cannot be used (HTTP status=405).
`error:not-implemented`| The request method is not supported by the server and cannot be handled (HTTP status=501).
`error:no-browsers-available`| SPN2 back-end headless browser cannot run.
`error:network-authentication-required`| The client needs to authenticate to gain network access to the URL (HTTP status=511).
`error:no-access`| Target URL could not be accessed (status=403).
`error:not-found`| Target URL not found (status=404).
`error:proxy-error`| SPN2 back-end proxy error.
`error:protocol-error`| HTTP connection broken. (Possible cause: “IncompleteRead”).
`error:read-timeout`| HTTP connection read timeout.
`error:soft-time-limit-exceeded`| Capture duration exceeded 45s time limit and was terminated.
`error:service-unavailable`| Service unavailable for URL (HTTP status=503).
`error:too-many-daily-captures`| This URL has been captured 10 times today. No more captures allowed.
`error:too-many-redirects`| Too many redirects. SPN2 tries to follow 3 redirects automatically.
`error:too-many-requests`| The target host has received too many requests from SPN and is blocking it (HTTP status=429). Captures to the same host will be delayed for 10-20s to remedy.
`error:user-session-limit`| User has reached the limit of concurrent active capture sessions.
`error:unauthorized`| The server requires authentication (HTTP status=401).