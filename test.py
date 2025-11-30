import requests

t = requests.get("https://cloud.onlysq.ru/api/files", cookies={"user_token": ""})

print(t.json()) # [{'id': 'id', 'name': 'name', 'owner_key': 'ownerkey', 'unique': 1, 'views': 1}]