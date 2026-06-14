"""
Build 3: Extend Your Week 1 Chatbot into a TUI
===============================================
Take the multi-turn chatbot you built in Week 1 and give it a full-screen terminal UI
using Textual. The chat logic stays the same; you're just changing the interface.

Requirements:
  - A scrollable chat log that shows conversation history
  - An input box at the bottom for the user to type
  - Keyboard shortcuts:
      Ctrl+L  →  clear the chat display (not the conversation history)
      Ctrl+K  →  compact: clear conversation history too (fresh start)
      Ctrl+Q  →  quit the application
  - Messages displayed with clear role labels: [You] and [Agent]
  - The UI must not freeze while waiting for an API response

Stretch goals:
  - Show the model name and token count in the Header or Footer
  - Add a Ctrl+S binding to save the conversation to a text file
  - Display a "thinking..." indicator while the API call is in progress

Important: API calls are blocking. Use run_worker(thread=True) to keep the UI alive
while waiting for responses. See Lesson 4 for the pattern.
"""

import os
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog
from textual.containers import Vertical
from week_2.project.agent import run_agent

load_dotenv()

MAX_HISTORY_TURNS = 20   # keep last N user+assistant pairs

# ---------------------------------------------------------------------------
# Chat logic (reuse / adapt from your Week 1 submission)
# ---------------------------------------------------------------------------

def trim_history(messages: list[dict], max_turns: int) -> list[dict]:
    max_messages = 2 * max_turns + 1
    if len(messages) <= max_messages:
        return messages
    else:
        return [messages[0]] + messages[-(max_messages-1):]


# ---------------------------------------------------------------------------
# TUI
# ---------------------------------------------------------------------------

class ChatApp(App):
    """A full-screen terminal chatbot."""

    TITLE = "Week 2 Chatbot - Perplexity Clone"
    CSS = """
    Screen {
        layout: vertical;
    }

    #chat_log {
    height: 3fr;
    border: solid green;
    }

    #tool_log {
        height: 1fr;
        border: solid yellow;
    }

    Input {
        dock: bottom;
        height: 3;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear display"),
        Binding("ctrl+k", "clear_history", "Clear history"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.messages: list[dict] = [
            {"role": "system", "content": "You are a helpful research assistant."}
        ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="chat_log", wrap=True, markup=True, highlight=True)
        yield RichLog(id="tool_log", wrap=True, markup=True, highlight=True)
        yield Input(placeholder="Type a message and press Enter...")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#chat_log", RichLog)
        log.write("[bold green]Chat started.[/bold green] Ctrl+Q to quit, Ctrl+L to clear.\n")
        self.query_one(Input).focus()

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Called when the user presses Enter."""
        user_text = event.value.strip()
        self.pending_message = user_text
        if not user_text:
            return

        event.input.clear()

        log = self.query_one("#chat_log", RichLog)
        log.write(f"[bold cyan][You][/bold cyan] {user_text}\n")
        log.write("[yellow][Agent][/yellow] Thinking...\n")

        # Append user message to history
        self.messages.append({"role": "user", "content": user_text})
        self.messages = trim_history(self.messages, MAX_HISTORY_TURNS)

        # Run the API call in a background thread so the UI stays responsive
        self.run_worker(self._get_response(),thread=True)

    async def _get_response(self) -> None:
        log = self.query_one("#chat_log", RichLog)
        tool_log = self.query_one("#tool_log", RichLog)
        try:
            reply = run_agent(
            self.pending_message,
            lambda msg: self.call_from_thread(
                tool_log.write,
                msg + "\n"
            )
)
            self.messages.append(
                {"role": "assistant","content": reply}
            )

            self.call_from_thread(
                log.write,
                f"[bold yellow][Agent][/bold yellow] {reply}\n"
            )

        except Exception as e:

            self.call_from_thread(
                log.write,
                f"[bold red]Error:[/bold red] {e}\n"
            )

    # -----------------------------------------------------------------------
    # Actions (bound to keyboard shortcuts)
    # -----------------------------------------------------------------------

    def action_clear_display(self) -> None:
        log = self.query_one("#chat_log", RichLog)
        log.clear()

    def action_clear_history(self) -> None:
        self.messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        log = self.query_one("#tool_log", RichLog)
        log.clear()
        log.write("[bold green]History cleared. Starting fresh.[/bold green]\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ChatApp().run()