# wayback_utils.py

This module provides a Python interface to interact with the Wayback Machine web page archiving service (web.archive.org). It allows you to save URLs, check the status of archiving jobs, and verify if a URL has already been indexed.

## Main classes:

- WayBackStatus: Represents the status of an archiving job.
- WayBackSave: Represents the response when requesting to archive a URL.
- WayBack: Main class to interact with the Wayback Machine API.

# Installation
```pip install wayback_utils```
- You need valid access keys (`ACCESS_KEY` and `SECRET_KEY`) to use the archiving API.
- You can provide an on_confirmation callback function to save() to receive the final archiving status asynchronously.
- The module uses requests and threading.

## Basic usage:

> **Note:**  
> You can obtain your `ACCESS_KEY` and `SECRET_KEY` from [archive.org](https://archive.org/account/s3.php).
1. Initialize the WayBack class with your access keys:
```python
    from wayback_utils import WayBack, WayBackStatus, WayBackSave
    
    wb = WayBack(ACCESS_KEY="your_access_key", SECRET_KEY="your_secret_key")
```
2. Save a URL:
```python
    result = wb.save("https://example.com")
```
3. Check the status of a job:
```python
    status = wb.status(result.job_id)
```
4. Verify if a URL is already indexed:
```python
    is_indexed = wb.indexed("https://example.com")
```

You can also pass a callback function to `save()` using the `on_confirmation` parameter. This callback will be called asynchronously with the final result of the archiving operation:

```python
def my_callback(result):
    print("Archiving finished:", result.status)

result = wb.save("https://example.com", on_confirmation=my_callback)
```

> **Warning:**  
> URLs archived with the Wayback Machine may take up to 12 hours to become fully indexed and discoverable.
Notes:

## save() parameters:

The `save( )` method accepts several optional parameters to customize the capture process:

- `url`: The URL to be archived.
- `timeout`: Maximum time (in seconds) to wait for the archiving operation to complete.
- `capture_all`: Set to `1` to capture web pages even if they return HTTP errors (4xx/5xx). By default, only status 200 pages are captured.
- `capture_outlinks`: Set to `1` to automatically capture outlinks found on the page (including PDF, JSON, RSS, MRSS).
- `capture_screenshot`: Set to `1` to capture a full-page PNG screenshot, stored as a separate capture.
- `delay_wb_availability`: Set to `1` to delay capture availability in the Wayback Machine by ~12 hours, reducing system load.
- `force_get`: Set to `1` to force a simple HTTP GET request for capture, overriding the default HEAD-based logic.
- `skip_first_archive`: Set to `1` to skip checking if this is the first archive, speeding up the process.
- `outlinks_availability`: Set to `1` to return the timestamp of the last capture for all outlinks.
- `email_result`: Set to `1` to receive an email report of the captured URLs.
- `on_confirmation`: A callback function that will be called asynchronously with the final result of the archiving operation.

## status() parameters:

The `status( )` method checks the status of an archiving job.

- `job_id`: The unique identifier of the archiving job to check.
- `timeout`: Maximum time in seconds to wait for the status response.

Returns a `WayBackStatus` object with details about the job's progress or result.

## indexed() parameters:

The `indexed( )` method checks if a given URL has already been archived and indexed by the Wayback Machine.

- `url`: The URL to check for existing archives.
- `timeout`: Maximum time in seconds to wait for the response.

Returns `True` if the URL has at least one valid (HTTP 2xx or 3xx) archived snapshot, otherwise `False`.


# License:
MIT license.
