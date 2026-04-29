import httpx

GRAPHQL_URL = "https://api.buffer.com/graphql"


async def graphql_request(api_key, query, variables=None):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            GRAPHQL_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "variables": variables or {}
            }
        )

    try:
        data = response.json()
    except Exception:
        raise Exception(f"Buffer вернул не JSON: {response.text}")

    if response.status_code >= 400:
        raise Exception(f"Buffer ошибка {response.status_code}: {data}")

    if "errors" in data:
        raise Exception(f"Buffer GraphQL ошибка: {data['errors']}")

    return data["data"]


async def get_profiles(api_key):
    account_query = """
    {
      account {
        organizations {
          id
          name
        }
      }
    }
    """

    account_data = await graphql_request(api_key, account_query)
    organizations = account_data["account"]["organizations"]

    if not organizations:
        raise Exception("У аккаунта Buffer нет организаций")

    org_id = organizations[0]["id"]

    channels_query = """
    query GetChannels($input: ChannelsInput!) {
      channels(input: $input) {
        id
        name
        service
      }
    }
    """

    channels_data = await graphql_request(
        api_key,
        channels_query,
        {"input": {"organizationId": org_id}}
    )

    profiles = []
    for ch in channels_data["channels"]:
        profiles.append({
            "id": ch.get("id"),
            "service": ch.get("service", "unknown"),
            "formatted_username": ch.get("name") or ch.get("id"),
        })

    return profiles


async def send_to_buffer(api_key, profile_id, image_urls, caption):
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        __typename
        ... on InvalidInputError {
          message
        }
        ... on NotFoundError {
          message
        }
        ... on UnauthorizedError {
          message
        }
        ... on UnexpectedError {
          message
        }
        ... on RestProxyError {
          message
        }
        ... on LimitReachedError {
          message
        }
      }
    }
    """

    variables = {
        "input": {
            "channelId": profile_id,
            "text": caption,
            "schedulingType": "notification",
            "mode": "addToQueue",
            "metadata": {
                "tiktok": {
                    "title": caption[:150]
                }
            },
            "assets": {
                "images": [{"url": url} for url in image_urls]
            }
        }
    }

    data = await graphql_request(api_key, mutation, variables)
    result = data["createPost"]

    if result["__typename"] != "PostActionSuccess":
        message = result.get("message", "Неизвестная ошибка Buffer")
        raise Exception(message)

    return result