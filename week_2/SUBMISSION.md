# SUBMISSION.md

## What I Built

For this week's project, I built a research assistant that runs completely inside the terminal. The user can ask questions and the agent is able to search the web, read webpages, and search research papers using the AlphaXiv MCP server before generating an answer.

The project uses an agent loop with tool calling. Instead of answering immediately, the model can decide to call tools such as `web_search`, `web_fetch`, and `discover_papers`. After a tool returns a result, the result is fed back to the model and it decides whether it needs more information or if it is ready to answer the user. This process continues until the model stops requesting tools.

I also built a Textual TUI for the project. It has a chat panel where the conversation is shown and a separate tool activity panel which displays the tools being used by the agent. Keyboard shortcuts are available for clearing the display, clearing history and quitting the application.

## Design Decision

One design decision I made was to separate web searching and webpage reading into two different tools. Searching and reading are different tasks, and keeping them separate gave the model more control over how much information it wanted to retrieve.

I also limited the amount of webpage text returned from `web_fetch`. Some pages contain a lot of content and sending everything to the model would waste tokens and make responses slower. Truncating the content seemed like a reasonable compromise.

## Something That Surprised Me

The most difficult part of this project was honestly the AlphaXiv MCP integration. At first I was getting 401 Unauthorized errors and I thought something was wrong with my implementation. Later I found out that OAuth authentication was required. Once I got the OAuth flow working and the tokens were being saved correctly, the MCP server started working without issues.

Another thing that surprised me was that the model would sometimes answer current-event questions from its own knowledge instead of calling `web_search`. I had to improve both the system prompt and the tool descriptions before it started using the search tool consistently.

## What I Would Improve

If I had more time, I would improve the conversation memory. Right now the agent works well for research queries, but it does not keep long-term context as effectively as a normal chatbot.

I would also like to implement `get_paper_content` more deeply so the agent can read complete papers instead of only searching for them. Another improvement would be better error handling for failed network requests and adding streaming responses in the TUI. I think that would make the application feel much more responsive and polished.

Overall, this project helped me understand how tool calling, agent loops and MCP actually work behind the scenes. Before this week I had only used chatbots, but now I understand the basic architecture of how research agents are built.
