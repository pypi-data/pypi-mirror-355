"""User management module for RepoRover."""

from typing import Callable

import requests
from rich.progress import Progress

from reporover.constants import (
    GitHubAccessLevel,
    StatusCode,
)
from reporover.util import print_json_string


def modify_user_access(  # noqa: PLR0913
    github_organization_url: str,
    repo_prefix: str,
    username: str,
    access_level: GitHubAccessLevel,
    token: str,
    progress: Progress,
    put_request_function: Callable = requests.put,
) -> StatusCode:
    """Change user access to the specified level."""
    # define the status codes for the request
    request_status_code = None
    # extract the repository name from the URL
    organization_name = github_organization_url.split("github.com/")[1].split(
        "/"
    )[0]
    # define the full name of the repository that involves
    # the prefix of the repository a separating dash and
    # then the name of the user; note that this is the standard
    # adopted by GitHub repositories created by GitHub Classroom
    full_repository_name = repo_prefix + "-" + username
    full_name_for_api = organization_name + "/" + full_repository_name
    # define the API URL for the request
    api_url = f"https://api.github.com/repos/{full_name_for_api}/collaborators/{username}"
    # headers for the request
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # data for the request
    data = {"permission": access_level.value}
    # make the PUT request to change the user's permission
    response = put_request_function(api_url, headers=headers, json=data)
    # check if the request was successful
    # display positive configuration since change of the access level worked
    if response.status_code == StatusCode.SUCCESS.value:
        progress.console.print(
            f"󰄬 Changed {username}'s access to '{access_level.value}' in"
            + f" {full_repository_name}"
        )
        # indicate that the success occurred to
        # the calling function for follow-on
        # computation and return of status code
        request_status_code = StatusCode.SUCCESS
    # display error message since the change of the access level did not work
    else:
        # display the basic error message
        progress.console.print(
            f" Failed to change {username}'s access to '{access_level.value}' in"
            + f" {full_repository_name}\n"
            + f"  Diagnostic: {response.status_code}"
        )
        # display all of the rest of the details in the string
        # that encodes the JSON response from the GitHub API
        print_json_string(response.text, progress)
        # indicate that the failure occurred to
        # the calling function for follow-on
        # computation and return of status code
        request_status_code = StatusCode.FAILURE
    # return the status code of the request
    return request_status_code
