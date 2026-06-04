import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

bot_name=input("Enter your assistant's name, choose from 1: Owl Alpha, 2: NVIDIA Nemotron 3 Nano Omni, 3: Poolside: Laguna (Just enter the number):\n")
if bot_name=='1':
    bot_name='Owl Alpha'
    bot_model="openrouter/owl-alpha"
elif bot_name=='2':
    bot_name='NVIDIA Nemotron 3 Nano Omni'
    bot_model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
elif bot_name=='3':
    bot_name='Poolside: Laguna'
    bot_model="poolside/laguna-m.1:free"
else:
    print("Invalid input. Defaulting to Owl Alpha.")
    bot_name='Owl Alpha'
    bot_model="openrouter/owl-alpha"
turns=int(input("Enter the number of turns for the conversation: \n"))
print(f"\nChat started with {bot_name} with {turns} turns. Type 'exit' to quit.\n")

class ChatAgent:

    def __init__(self, model):
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1",api_key=os.environ["OPENROUTER_API_KEY"],)
        self.model=model
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
    def summarize(self, messages):
        # Using the model itself to summarize the conversation which is older than 2 turns into a single system prompt.
        summary_prompt = "Summarize the following conversation in a concise way. Keep important facts, preferences, names, and context.\n"
        for msg in messages[1:len(messages)-4]:  # Skip the initial system prompt and last 4 messages (2 user-assistant pairs)
            summary_prompt += f"{msg['role']}: {msg['content']}\n"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": f"You are a helpful assistant. Summary of the conversation so far: {summary_prompt}"}],
        )
        return {"role":"system", "content":response.choices[0].message.content.strip()}
    def compaction(self,msgs):
        # Compaction strategy: Keep the system prompt and the last 2 user-assistant pairs, the rest are summarized into a single system prompt that says "The conversation so far has been about X, Y, Z."
        if len(msgs) <= 5:
            return msgs
        else:
            return [msgs[0],self.summarize(msgs)] + msgs[-4:]
    def run_chatbot(self):
        response=None
        while True:
            user_input = input("You: ")
            if user_input.lower()=='/reset':
                self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
                print("\nHistory reset.\n")
                continue        
            if user_input.lower()=='/tokens':
                if response is not None:
                    print(f"\nToken usage: {response.usage}\n")
                    continue
                else:
                    print("\nNo API call made yet.\n")
                    continue
            if user_input.lower() in ['exit', 'quit']:
                print("\nChat ended. Thank You.\n")
                break
            self.messages.append({"role": "user", "content": user_input})
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )
            bot_reply=response.choices[0].message.content
            print()
            print(f"Assistant: {bot_reply}\n")
            self.messages.append({"role": "assistant", "content": bot_reply})
            if len(self.messages)>2*turns+1:
                self.messages=self.compaction(self.messages)


agent=ChatAgent(model=bot_model)
agent.run_chatbot()