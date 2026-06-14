# import re
# import json
# def read_file(file_path):
#     with open(file_path, 'r') as file:
#         return file.read()

# def write_file(file_path, content):
#     with open(file_path, 'w') as file:
#         file.write(content)
#     return "File written successfully"
# # response_text = """
# # <tool_call>
# # {
# #     "name":"read_file",
# #     "arguments":{
# #         "file_path":"notes.txt"
# #     }
# # }
# # </tool_call>
# # """
# def parse_tool_call(response_text):
#     match=re.search(r"<tool_call>(.*?)</tool_call>", response_text, re.DOTALL)
#     tool_json=match.group(1)
#     text_json=json.loads(tool_json)
#     return text_json

# def dispatch(name, args):
#     if name=="read_file":
#         return read_file(args["file_path"])
#     elif name=="write_file":
#         return write_file(args["file_path"], args["content"])
#     else:
#         return "Unknown tool"
    
# def run_agent():

# """
# Build 1: Custom Tool Call Parser
# =================================
# Before modern SDKs handled tool calls natively, developers used custom text formats
# that the model was prompted to emit. This build has you implement that pattern from
# scratch: prompt the model to emit tool calls in a structured format, parse them, run
# the corresponding Python function, and feed the result back.

# This is NOT the production way to do it (Build 2 is). But doing it manually first
# makes the mechanics obvious. The SDK is doing exactly this, just more robustly.

# The format we'll use:
#     The model emits tool calls wrapped in <tool_call> tags, like:

#         I need to read the file first.

#         <tool_call>
#         {"name": "read_file", "arguments": {"path": "notes.txt"}}
#         </tool_call>

#     Your code finds the tag, parses the JSON, runs the function, and injects
#     the result back as a <tool_response> in the next message.

# Tasks:
#   1. Complete `parse_tool_call` to extract name + arguments from a model response
#   2. Complete `dispatch` to route a tool call to the right Python function
#   3. Complete `run_agent` to implement the back-and-forth loop

# Tools to implement:
#   - read_file(path: str) -> dict    reads a file from disk and returns its content
#   - write_file(path: str, content: str) -> dict    writes content to a file on disk

# Before running, create a file called `sample.txt` with some text in it.
# """

import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "nex-agi/nex-n2-pro:free"

SYSTEM_PROMPT = """You are a helpful file assistant with access to the following tools:

- read_file(path: str): reads a file from disk and returns its content
- write_file(path: str, content: str): writes content to a file on disk

When you need to use a tool, emit EXACTLY this format and nothing else after it:

<tool_call>
{"name": "TOOL_NAME", "arguments": {"arg1": "value1"}}
</tool_call>

IMPORTANT:
When calling a tool, ALWAYS include BOTH opening and closing tags.

BAD:
<tool_call> {...}

GOOD:
<tool_call>
{...}
</tool_call>

After you receive the tool result in a <tool_response> block, continue your response
normally. Do not emit a tool_call and prose in the same turn. Pick one or the other.
"""

def read_file(path: str) -> dict:
    try:
        with open(path, "r") as file:
            return{
                "content": file.read(),
                "path": path
            }
    except Exception as e:
        return {"error": str(e)}


def write_file(path: str, content: str) -> dict:
    try:
        with open(path, "w") as file:
            bytes_written = file.write(content)

        return {
            "success": True,
            "path": path,
            "bytes_written": bytes_written
        }

    except Exception as e:
        return {"error": str(e)}

def parse_tool_call(response_text: str) -> dict | None:
    match = re.search(r"<tool_call>(.*?)</tool_call>",response_text,re.DOTALL)
    if not match:
        return None
    tool_data = json.loads(match.group(1))
    return tool_data


def strip_tool_call(response_text: str) -> str:
    return re.sub(r"<tool_call>.*?</tool_call>", "", response_text, flags=re.DOTALL).strip()

TOOL_REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
}

def dispatch(name: str, arguments: dict) -> str:
    if name=="read_file":
        return json.dumps(read_file(arguments["path"]))
    elif name=="write_file":
        return json.dumps(write_file(arguments["path"], arguments["content"]))
    else:
        return json.dumps({"error": "Unknown tool"})

MAX_ITERATIONS = 6

def run_agent(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for iteration in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages)
        response_text = response.choices[0].message.content
        tool_call = parse_tool_call(response_text)
        if tool_call is None:
            return strip_tool_call(response_text)
        name=tool_call["name"]
        arguments=tool_call["arguments"]
        tool_result = dispatch(name, arguments)
        messages.append({"role": "assistant", "content": response_text})
        messages.append({"role": "user", "content": f"<tool_response>\n{tool_result}\n</tool_response>"})

    return f"[Agent stopped after {MAX_ITERATIONS} iterations]"
    

if __name__ == "__main__":
    with open("sample.txt", "w") as f:
        f.write("The Indian Institute of Technology Delhi (IIT Delhi) is an internationally renowned center of excellence for science, engineering, and technology training. Established in 1961, this premier institution is strategically located in the heart of South Delhi. Over the decades, it has solidified its reputation through rigorous academics, cutting-edge research, and a distinguished global alumni network.Functioning as a premier institute of national importance, IIT Delhi IIT Delhi consistently ranks among the top engineering schools globally. The 320-acre residential campus is home to a dynamic community of students, research scholars, and eminent faculty. The institute offers a multitude of undergraduate, postgraduate, and doctoral programs that blend fundamental sciences with applied technology.Beyond academics, the institute fosters holistic development through extensive student-led events. Notable fests like Rendezvous (a cultural festival) and Tryst (a technical event) attract massive participation from across the nation. Its strategic location in the national capital also enables students to actively collaborate with leading industries, policymakers, and global researchers.Ultimately, IIT Delhi is not just an educational hub; it is a profound catalyst for technological advancement and entrepreneurship, nurturing students into global leaders, scientists, and innovators.")

    test_queries = [
        "Read sample.txt and summarise what it says.",
        "Read sample.txt and write a one-sentence version of its content to summary.txt.",
        "Read summary.txt and give its content."
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        result = run_agent(query)
        print(f"Answer: {result}")