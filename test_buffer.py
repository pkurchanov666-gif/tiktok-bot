import requests
import json

API_KEY = "AEvLjUanIen82-EL1JsiFJ3LesWurhR-r78hr_P1IRu"
CHANNEL_ID = "69f242045c4c051afaf20ced"

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
        "channelId": CHANNEL_ID,
        "text": "Test TikTok photo post",
        "schedulingType": "notification",
        "mode": "addToQueue",
        "metadata": {
            "tiktok": {
                "title": "Test TikTok photo post"
            }
        },
        "assets": {
            "images": [
                {"url": "https://placehold.co/960x1280.jpg?text=Slide+1"},
                {"url": "https://placehold.co/960x1280.jpg?text=Slide+2"},
                {"url": "https://placehold.co/960x1280.jpg?text=Slide+3"},
                {"url": "https://placehold.co/960x1280.jpg?text=Slide+4"},
                {"url": "https://placehold.co/960x1280.jpg?text=Slide+5"}
            ]
        }
    }
}

response = requests.post(
    "https://api.buffer.com/graphql",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "query": mutation,
        "variables": variables
    }
)

print("Статус:", response.status_code)
data = response.json()
print(json.dumps(data, indent=2, ensure_ascii=False))