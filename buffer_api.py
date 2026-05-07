import httpx

GRAPHQL_URL = "https://api.buffer.com/graphql"

async def graphql_request(api_key, query, variables=None):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(GRAPHQL_URL, 
            headers={"Authorization": f"Bearer {api_key}"},
            json={"query": query, "variables": variables or {}})
        return response.json()

async def get_profiles(api_key):
    q = "{ account { organizations { id } } }"
    data = await graphql_request(api_key, q)
    org_id = data["data"]["account"]["organizations"][0]["id"]
    
    q_ch = "query($id: ChannelsInput!) { channels(input: $id) { id name service } }"
    data_ch = await graphql_request(api_key, q_ch, {"id": {"organizationId": org_id}})
    return data_ch["data"]["channels"]

async def send_to_buffer(api_key, profile_id, image_urls, caption):
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        __typename
        ... on PostActionSuccess { post { id } }
        ... on InvalidInputError { message }
      }
    }
    """
    variables = {
        "input": {
            "channelId": profile_id, "text": caption,
            "schedulingType": "notification", "mode": "addToQueue",
            "assets": {"images": [{"url": url} for url in image_urls]}
        }
    }
    data = await graphql_request(api_key, mutation, variables)
    if "errors" in data or data["data"]["createPost"]["__typename"] != "PostActionSuccess":
        raise Exception(str(data))
    return True
