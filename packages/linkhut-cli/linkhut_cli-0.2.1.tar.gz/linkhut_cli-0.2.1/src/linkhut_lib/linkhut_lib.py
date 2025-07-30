"""
LinkHut Library - Core functions for interacting with LinkHut API.

This module provides functions for managing bookmarks and tags through the LinkHut API,
including creating, updating, listing and deleting bookmarks, as well as managing tags.
"""

# todo: standardize error codes and messages across all functions

import json
import sys

from httpx import Response
from loguru import logger

from . import utils

logger.remove()
logger.add(
    sys.stderr,
    level="ERROR",
    format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


def get_bookmarks(
    tag: str = "",
    date: str = "",
    url: str = "",
    count: int = 0,
) -> list[dict[str, str]]:
    """
    Get bookmarks from LinkHut. Supports filtering or fetching by recent count.

    - If 'count' is provided, fetches the most recent 'count' bookmarks,
      optionally filtered by the first tag in the 'tag' list. Uses /v1/posts/recent.
    - If 'date', 'url', or 'tag' (without 'count') are provided, fetches bookmarks
      matching the criteria. Uses /v1/posts/get.
    - If no arguments are provided, fetches the 15 most recent bookmarks.

    Args:
        tag (str): Filter by tags (for /get) or a single tag (first element used for /recent).
        date (str): Filter by date (CCYY-MM-DDThh:mm:ssZ format expected by /get).
        url (str): Filter by exact URL (for /get).
        count (int|None): Number of recent bookmarks to fetch (for /recent).

    Returns:
        list[dict]: list of dictionaries containing bookmark metadata.
    """
    fields: dict[str, str] = {}
    action: str

    # Determine action based on provided parameters
    if count:
        action = "bookmark_recent"
        fields["count"] = str(count)
        if tag:
            # bookmark_recent accept only one tag, if multiple tags are provided, then only the first one is used
            # if presented with wrong tag, it returns {"posts": []}
            fields["tag"] = tag.replace(",", " ").split()[0]
            logger.debug(f"Using first tag for /recent endpoint: {fields['tag']}")
    elif tag or date or url:
        action = "bookmark_get"
        if tag:
            # bookmark_get expects tags=tag1+tag2...
            fields["tag"] = tag.replace(" ", "+").replace(",", "+")
        if date:
            try:
                # bookmark_get takes dt=CCYY-MM-DD
                utils.is_valid_date(date)  # validate date format
            except ValueError as e:
                logger.error(f"Invalid date format for {date}: {e}")
                return [{"error": "invalid_date_format"}]
            fields["dt"] = date
        if url:
            # TODO: Add URL encoding
            # no need to validate URL format here if user has imported the bookmark file, not all URLs will have http:// or https://
            # try:
            #     utils.verify_url(url)
            # except ValueError as e:
            #     logger.error(f"Invalid URL format for {url}: {e}")
            #     return [{"error": "invalid_url_format"}]
            fields["url"] = url
    else:
        # Default behavior: get recent 15 posts
        action = "bookmark_recent"
        fields["count"] = "15"

    try:
        response: Response = utils.linkhut_api_call(action=action, payload=fields)
        fetched_bookmarks: list[dict[str, str]] = response.json().get("posts", [])

        # if bookmarks are found, posts list will not be empty
        if fetched_bookmarks:
            logger.debug("Bookmarks fetched successfully")
            return fetched_bookmarks
        elif response.json().get("result_code") == "something went wrong" or not fetched_bookmarks:
            # result code "something went wrong" indicates posts/get endpoint was called with wrong url
            # todo: update logger error class severity equal to debug
            logger.warning("No Bookmarks Found")
            return [{"error": "no_bookmarks_found"}]
        else:
            logger.warning("No bookmarks found for the given criteria")
            return [{"error": "unknown_error"}]
    except Exception as e:
        logger.error(f"Error fetching bookmarks: {e}")
        return [{"error": "error_fetching_bookmarks"}]


def create_bookmark(
    url: str,
    title: str = "",
    note: str = "",
    tags: str = "",  # could be of form: "tag1,tag2" or "tag1 tag2" or "tag1 tag2,tag3"
    fetch_tags: bool = True,
    private: bool = False,
    to_read: bool = False,
    replace: bool = False,
) -> dict[str, str]:
    """
    Create a new bookmark in LinkHut.

    This function creates a new bookmark with the specified URL and optional metadata.
    If title is not provided, it will attempt to fetch the title automatically from the URL.
    If tags are not provided and fetch_tags is True, it will attempt to suggest tags based on the URL content.

    Args:
        url (str): The URL to bookmark
        title (str): Title for the bookmark. If None, fetches automatically.
        note (str): Extended notes or description for the bookmark
        tags (str): Comma-separated list of tags to apply to the bookmark
        fetch_tags (bool): Whether to auto-suggest tags if none provided (default: True)
        private (bool): Whether the bookmark should be private (default: False)
        to_read (bool): Whether to mark the bookmark as "to read" (default: False)
        replace (bool): Whether to replace an existing bookmark with the same URL (default: False)

    Returns:
        dict[str, str]: The created bookmark's metadata
    """
    try:
        # must start with http:// or https://
        utils.verify_url(url)
    except Exception as e:
        logger.error(f"Invalid URL: {url}. Error: {e}")
        return {"error": "invalid_url"}

    action = "bookmark_create"

    # If title not provided, try to fetch it
    if not title:
        title = utils.get_link_title(url)

    # If valid tags not provided, try to fetch suggestions
    if not tags.isalnum() and fetch_tags:
        tags_str: str = utils.get_tags_suggestion(url)  # comma separated tags
        tags = tags_str.replace(",", " ").replace(" ", "+")  # convert to + separated tags

    # checks if tag string in argument is not just a whitespace or empty string
    elif tags.isalnum():
        _tag_list: list[str] = tags.replace(",", " ").split()
        tags = "+".join(_tag_list)

    # Prepare API payload
    fields: dict[str, str] = {}
    fields["url"] = url
    fields["description"] = title
    fields["tags"] = tags
    fields["replace"] = "yes" if replace else "no"
    fields["toread"] = "yes" if to_read else "no"
    fields["shared"] = "no" if private else "yes"

    if note:
        fields["extended"] = note

    try:
        response: Response = utils.linkhut_api_call(action=action, payload=fields)
        response_dict: dict[str, str] = response.json()
        status_code: int = response.status_code
        if status_code == 200 and response_dict.get("result_code") == "done":
            logger.debug(f"Bookmark created successfully: {response_dict}")
            return fields
        else:
            logger.warning(f"Failed to create bookmark: {response_dict}")
            return {"error": "bookmark_exists"}
    except Exception as e:
        logger.error(f"Error creating bookmark: {e}")
        return {"error": "API error"}


def update_bookmark(
    url: str,
    new_tag: str = "",
    new_note: str = "",
    new_private: bool | None = None,
    new_to_read: bool | None = None,
    replace: bool = False,  # whether to replace data or append to existing data
) -> dict[str, str]:
    """
    Update an existing bookmark or create a new one if it doesn't exist.

    This function allows updating the tags, notes, privacy settings, and to-read status of a bookmark.
    If the bookmark doesn't exist, it will create a new one with the provided parameters.
    This function replaces the previous reading_list_toggle function.

    Args:
        url (str): The URL of the bookmark to update
        new_tag (str): New tags to set for the bookmark (replaces existing tags if replace=True)
        new_note (str): Note to append to the existing note (or replace if replace=True)
        new_private (str): Whether to set the bookmark as private ("yes") or public ("no")
        to_read (bool | None): Whether to mark as to-read (True) or read (False). None means no change.
        replace (bool): Whether to replace existing data or append to it

    Returns:
        dict[str, str]: Status information about the update operation
    """

    # check if there is nothing to update, if so return false
    if not new_tag and not new_note and new_private is None and new_to_read is None:
        logger.debug("No updates provided. Nothing to do.")
        return {"status": "missing_update_parameters"}

    fields_to_inherit: set[str] = {"description", "tags", "extended", "shared", "toread"}

    # check for existing bookmark with the given URL
    fetched_bookmark: dict[str, str] = get_bookmarks(url=url)[0]

    # if no, then create a new bookmark with given values
    if fetched_bookmark.get("error") == "no_bookmarks_found":
        logger.debug(f"Bookmark with URL {url} not found. Creating a new one.")
        private: bool = new_private if new_private is not None else False
        to_read: bool = new_to_read if new_to_read is not None else False
        bookmark_meta: dict[str, str] = create_bookmark(
            url=url, tags=new_tag, note=new_note, private=private, to_read=to_read
        )
        bookmark_meta["status"] = "no_bookmark_found"
        return bookmark_meta

    elif fetched_bookmark.get("error") == "invalid_url_format":
        logger.debug(f"Invalid URL format: {url}. Please provide a valid URL.")
        # propagate the error to the calling function
        return {"error": "invalid_url_format"}

    elif fetched_bookmark.get("error"):
        logger.debug("Unexpected error occurred while fetching bookmark data.")
        return {"error": "unknown_error"}

    # if yes
    elif fields_to_inherit.issubset(fetched_bookmark.keys()):
        # get existing bookmark meta
        title: str = fetched_bookmark.get("description", url)
        tags: str = fetched_bookmark.get("tags", "")
        note: str = fetched_bookmark.get("extended", "")
        current_toread: bool = fetched_bookmark.get("toread") == "yes"
        current_private: bool = fetched_bookmark.get("shared") == "no"

        # Determine privacy setting
        if new_private is not None:
            private: bool = new_private
        else:
            private: bool = current_private

        # Determine to_read setting
        if new_to_read is not None:
            final_toread = new_to_read
        else:
            final_toread = current_toread

        # Check if no actual changes are needed
        if (
            new_to_read is not None
            and current_toread == new_to_read
            and new_private is not None
            and current_private == new_private
            and not new_tag
            and not new_note
        ):
            logger.info(f"Bookmark with URL {url} already has the desired status. Nothing to do.")
            return {"status": "no_update_needed"}

        logger.info(f"Bookmark with URL {url} already exists. Updating it.")

        # Refactored tag and note concatenation for clarity
        if replace:
            updated_tags = new_tag
            updated_note = new_note
        else:
            updated_tags = f"{tags} {new_tag}".strip() if new_tag else tags
            updated_note = f"{note} {new_note}".strip() if new_note else note

        bookmark_meta = create_bookmark(
            url=url,
            title=title,
            tags=updated_tags,
            note=updated_note,
            private=private,
            replace=True,
            fetch_tags=False,
            to_read=final_toread,
        )
        return bookmark_meta
    else:
        logger.debug("Unexpected bookmark format received. Missing required fields.")
        return {"error": "unknown_error"}


def get_reading_list(count: int = 5) -> list[dict[str, str]]:
    """
    Fetch and display the user's reading list (bookmarks marked as to-read).

    Args:
        count (int): Number of bookmarks to fetch (default: 5)

    Returns:
        None: Results are printed directly to stdout
    """
    reading_list: list[dict[str, str]] = get_bookmarks(tag="unread", count=count)
    if reading_list[0].get("error") == "no_bookmarks_found":
        logger.info("No bookmarks found in the reading list.")
        return [{"error": "no_bookmarks_found"}]
    elif reading_list:
        logger.debug(f"Reading list fetched successfully: {json.dumps(reading_list, indent=2)}")
        return reading_list
    else:
        logger.error("No bookmarks found in the reading list.")
        return [{"error": "api_error"}]


def delete_bookmark(url: str) -> dict[str, str]:
    """
    Delete a bookmark.

    Args:
        bookmark_id (str): ID of the bookmark to delete

    Returns:
        Dict[str, Any]: Response from the API
    """
    action: str = "bookmark_delete"
    fields: dict[str, str] = {"url": url}

    try:
        # verify the URL format before making the API call
        utils.verify_url(url)
        response: Response = utils.linkhut_api_call(action=action, payload=fields)
    except ValueError as e:
        logger.error(f"Invalid URL format: {url}. Error: {e}")
        return {"error": "invalid_url_format"}
    except Exception as e:
        logger.error(f"Error deleting bookmark: {e}")
        return {"error": "api_error"}

    result_code: str = response.json().get("result_code", "")

    if result_code == "done":
        logger.debug(f"Bookmark with URL {url} successfully deleted.")
        return {"bookmark_deletion": "success"}
    else:
        logger.error(f"Unable to delete bookmark with URL {url}. Result code: {result_code}")
        return {"bookmark_deletion": "failure"}


def rename_tag(old_tag: str, new_tag: str) -> dict[str, str]:
    """
    Rename a tag across all bookmarks.

    Args:
        old_tag (str): Current tag name
        new_tag (str): New tag name

    Returns:
        Dict[str, Any]: Response from the API
    """
    action = "tag_rename"
    fields = {"old": old_tag, "new": new_tag}

    try:
        # verify the tag format before making the API call
        if not utils.is_valid_tag(old_tag) or not utils.is_valid_tag(new_tag):
            raise ValueError(f"Invalid tag format: {old_tag} or {new_tag}")
        response: Response = utils.linkhut_api_call(action=action, payload=fields)
    except ValueError as e:
        logger.error(f"Invalid tag format: {old_tag} or {new_tag}. Error: {e}")
        return {"error": "invalid_tag_format"}
    except Exception as e:
        logger.error(f"Error renaming tag: {e}")
        return {"error": "api_error"}

    result_code: str = response.json().get("result_code", "")

    if result_code == "done":
        logger.info(f"Tag '{old_tag}' successfully renamed to '{new_tag}'.")
        return {"tag_renaming": "success"}
    else:
        logger.error(f"Failed to rename tag '{old_tag}' to '{new_tag}'. Result code: {result_code}")
        return {"tag_error": "unsuccessful"}


# todo: #20 update error handling for delete_tag, rename_tag
def delete_tag(tag: str) -> dict[str, str]:
    """
    Delete a tag from all bookmarks.

    Args:
        tag (str): Tag to delete

    Returns:
        Dict[str, Any]: Response from the API
    """
    action: str = "tag_delete"
    fields: dict[str, str] = {"tag": tag}

    try:
        # verify the tag format before making the API call
        if not utils.is_valid_tag(tag):
            raise ValueError
        response: Response = utils.linkhut_api_call(action=action, payload=fields)
    except ValueError as e:
        logger.error(f"Invalid tag format for {tag}: {e}.")
        return {"error": "invalid_tag_format"}
    except Exception as e:
        logger.error(f"Error deleting tag: {e}")
        return {"error": "api_error"}

    result_code: str = response.json().get("result_code", "")

    if result_code == "done":
        logger.debug(f"Tag '{tag}' successfully deleted.")
        return {"tag_deletion": "success"}
    else:
        logger.error(f"Failed to delete tag '{tag}'. Tag doesn't exist. Result code: {result_code}")
        return {"tag_deletion": "unsuccessful"}


# def get_tags() -> List[Dict[str, Any]]:
#     """
#     Get all tags and their counts.

#     Returns:
#         List[Dict[str, Any]]: List of tags with counts
#     """
#     api_endpoint = "/v1/tags"
#     fields = {}

#     response = utils.linkhut_api_call(api_endpoint=api_endpoint, fields=fields)

#     return response


if __name__ == "__main__":
    # Example usage
    # These examples show how to use the library functions directly
    # Uncomment any of these lines to test the functionality

    url = "https://huggingface.co"
    # title = "Example Title"
    # note = "This is a note."
    # tags = ["tag1", "tag2"]

    # 1. Create a new bookmark
    create_bookmark(url=url)

    # 2. Mark a bookmark as to-read
    # reading_list_toggle(url, to_read=True, tags=['MCP'])

    # 3. Update a bookmark's privacy setting
    # update_bookmark(url=url, private=False)

    # 4. Delete a bookmark
    # delete_bookmark(url)

    # 5. List bookmarks with a specific tag
    # print(get_bookmarks(tag=["blog"]))

    # 6. Show reading list
    # get_reading_list(count=5)
