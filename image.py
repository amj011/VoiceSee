import requests

url = "https://v1.genr.ai/api/circuit-element/generate-captions"
payload = {
    "img_url": "https://static.javatpoint.com/javascriptpages/images/random-image-generator-in-javascript3.png",
    "n_words": 15
}
headers = {"Content-Type": "application/json"}
response = requests.request("POST", url, json=payload, headers=headers)
print(response.text)