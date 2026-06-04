import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def call_model(prompt: str) -> str:
    """
    Make a single chat completion call.
    Print the full response object first and understand its structure.
    Then return just the assistant's text.
    """
    response = client.chat.completions.create(
        model="openrouter/owl-alpha",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    # TODO: try adding a system prompt with different instructions and guidelines
    # TODO: inspect `response` before you extract anything from it
    # What's in response.choices? What's in response.usage?
    print(f"Full response:\n{response}")
    print(f"Choices:\n{response.choices}")
    print(f"Usage:\n{response.usage}")
    return response.choices[0].message.content

if __name__ == "__main__":
    print(f"Concise response:\n{call_model('How are you?')}")