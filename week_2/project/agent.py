"""
ResearchBot: Week 2 Project Starter
======================================
This file currently makes a basic single-turn call to OpenRouter.
Your job is to evolve it into a full research agent with:
  - Web search and web fetch tools (using OpenAI SDK tool calling)
  - An agent loop that iterates until the model stops requesting tools
  - A Textual TUI with a chat panel and a tool activity log
  - Keyboard shortcuts: Ctrl+L (clear display), Ctrl+K (clear history), Ctrl+Q (quit),
    and at least one more of your choice

Start by getting this file working, then add tools, then add the TUI.
Don't try to build everything at once.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import requests
import json
import trafilatura  
from week_2.project.alphaxiv import discover_papers_sync

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "openrouter/owl-alpha"

def web_search(query: str) -> dict:
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": os.environ["SERPER_API_KEY"],
        "Content-Type": "application/json"
    }
    payload = {
        "q": query
    }
    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    return response.json()

TOOLS =[{
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current information.Use this tool whenever the question involves recent events,news, sports results, current facts, dates, people, or anything that may have changed after your training data. Do not guess. Search first.Search the web for current information.MUST be used for: - sports scores - match results- current events- news- recent facts- anything that could have happened after training. ever answer such questions without calling this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description":
                "Fetch and read the full content of a webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "discover_papers",
        "description": (
            "Search AlphaXiv for academic research papers and research literature"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string"
                }
            },
            "required": ["query"]
        }
    }
}]

def dispatch(tool_call):
    name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    if name == "web_search":
        return json.dumps(web_search(arguments["query"]))
    elif name == "web_fetch":
        return json.dumps(web_fetch(arguments["url"]))
    elif name == "discover_papers":
        import subprocess

        result = subprocess.run(
            [
                "python",
                "alphaxiv_search_cli.py",
                arguments["query"]
            ],
            capture_output=True,
            text=True
        )

        return result.stdout
    return json.dumps(
        {"error": f"Unknown tool: {name}"}
    )

def web_fetch(url: str) -> dict:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {
                "error": "Could not download page"
            }
        text = trafilatura.extract(downloaded)
        if not text:
            return {
                "error": "Could not extract content"
            }
        return {
            "url": url,
            "content": text[:8000]
        }
    except Exception as e:
        return {
            "error": str(e)
        }
    
def run_agent(user_message: str,tool_logger=None) -> str:
    messages = [
                {
            "role": "system",
            "content":
            """
            You are a research assistant.

            For ANY question involving:
            - current events
            - news
            - sports
            - elections
            - weather
            - recent facts
            - dates
            - match results

            YOU MUST call web_search before answering.

            Never answer these from memory.

            Use web_fetch to read webpages.

            Use discover_papers for academic papers and research.
            """
        },
        {"role": "user", "content": user_message},
    ]

    for _ in range(15):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "tool_calls":
            messages.append(message)
            for tool_call in message.tool_calls:
                tool_result = dispatch(tool_call)
                if tool_logger:
                    tool_logger(f"Using {tool_call.function.name}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,})
        if finish_reason == "stop":
            return message.content

    return f"[Agent stopped after 15 iterations without a final answer]"

if __name__ == "__main__":
    user_message = input("Enter your question for the research agent: ")
    answer = run_agent(user_message)
    print(f"Agent: {answer}")
#     print( 
#     web_fetch(
#         "https://home.iitd.ac.in"
#     )
# )
    # print(
    #     discover_papers_sync(
    #         "retrieval augmented generation"
    #     )[:500]
    # )