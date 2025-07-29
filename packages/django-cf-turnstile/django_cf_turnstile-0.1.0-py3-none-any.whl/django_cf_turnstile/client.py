import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


def post_form(url, data_dict, extra_headers=None, as_json=False):
    """
    Sends a POST request to a specified URL with data encoded as
    x-www-form-urlencoded, using only Python’s built-in urllib module.

    Args:
        url (str): The URL to post to.
        data_dict (dict): A dictionary of data to send.
        extra_headers (dict, optional): A dictionary of custom headers.
        as_json (bool, optional): Return data as json instead of a string
    """
    if extra_headers is None:
        extra_headers = {}

    data_encoded = urllib.parse.urlencode(data_dict).encode("utf-8")
    req = urllib.request.Request(
        url, data=data_encoded, headers=extra_headers, method="POST"
    )

    # Ensure Content-Type is set if not already, for urlencoded data
    if "Content-Type" not in req.headers:
        req.add_header(
            "Content-Type", "application/x-www-form-urlencoded; charset=utf-8"
        )

    req.add_header("Content-Length", str(len(data_encoded)))

    logger.debug(f"Sending {req.method} request to {req.full_url}")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_body = response.read().decode(
                response.headers.get_content_charset() or "utf-8"
            )

            if as_json is True:
                try:
                    response_body = json.loads(response_body)
                except json.JSONDecodeError:
                    logger.error("Response body is not valid JSON.")
                    return None, None

            return response.status, response_body

    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        return e.code, None
    except urllib.error.URLError as e:
        logger.error(f"URL Error: {e}")
        return None, None
    except Exception as e:
        logger.error(f"An Unexpected Error Occurred: {e}")
        return None, None
