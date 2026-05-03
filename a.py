from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:4000/v1",
    api_key="sk-50c3d8d9d6884dafa9b1e17ebff450d7"
)

response = client.chat.completions.create(
    model="gemini-3.1-pro-high",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.choices[0].message.content)