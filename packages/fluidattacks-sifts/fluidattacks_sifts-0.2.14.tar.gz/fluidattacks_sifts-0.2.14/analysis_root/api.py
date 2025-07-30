import os
from typing import Any, TypedDict

import aiohttp

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=10)


class RootInfo(TypedDict):
    id: str
    nickname: str


class RootInfoResponse(TypedDict):
    root: RootInfo | None


class RootQueryResponse(TypedDict):
    data: RootInfoResponse


class GitRoot(TypedDict):
    nickname: str
    id: str
    state: str
    gitignore: str


class GroupRoots(TypedDict):
    roots: list[GitRoot]


class GroupResponse(TypedDict):
    group: GroupRoots


class GroupRootsResponse(TypedDict):
    data: GroupResponse


class GraphQLApiError(Exception):
    """Raised when the GraphQL API returns errors."""


# GraphQL query for root info
ROOT_QUERY = """
query GetRoot($groupName: String!, $rootId: ID!) {
  root(groupName: $groupName, rootId: $rootId) {
    ... on GitRoot {
      id
      nickname
      state
      gitignore
    }
  }
}
"""

GROUP_ROOTS_QUERY = """
query GroupRoots($groupName: String!) {
  group(groupName: $groupName) {
    roots {
      ... on GitRoot {
        nickname
        id
        state
        gitignore
      }
    }
  }
}
"""


def initialize_session() -> tuple[aiohttp.ClientSession, str]:
    # Get the API token from environment variable
    api_token = os.environ.get("INTEGRATES_API_TOKEN")
    if not api_token:
        msg = "INTEGRATES_API_TOKEN environment variable is not set"
        raise ValueError(msg)

    # Set the base URL and authorization headers for the session
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

    return aiohttp.ClientSession(
        base_url="https://app.fluidattacks.com/",
        headers=headers,
    ), api_token


async def execute_graphql_query(
    session: aiohttp.ClientSession,
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    payload = {"query": query, "variables": variables}
    async with session.post(
        "/api",
        json=payload,
        timeout=DEFAULT_TIMEOUT,
    ) as response:
        response.raise_for_status()
        result = await response.json()
        if "errors" in result:
            raise GraphQLApiError(result["errors"])
        return result  # type: ignore[no-any-return]


async def fetch_root(
    session: aiohttp.ClientSession,
    group_name: str,
    root_id: str,
) -> RootQueryResponse:
    variables = {"groupName": group_name, "rootId": root_id}
    response: RootQueryResponse = await execute_graphql_query(  # type: ignore[assignment]
        session,
        ROOT_QUERY,
        variables,
    )
    return response


async def fetch_group_roots(
    session: aiohttp.ClientSession,
    group_name: str,
) -> GroupRootsResponse:
    variables = {"groupName": group_name}
    response: GroupRootsResponse = await execute_graphql_query(  # type: ignore[assignment]
        session,
        GROUP_ROOTS_QUERY,
        variables,
    )
    return response
