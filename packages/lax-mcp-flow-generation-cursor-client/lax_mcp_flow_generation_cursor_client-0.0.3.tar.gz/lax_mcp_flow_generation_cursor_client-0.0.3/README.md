# Agent Architecture

1. **Prompt Expansion Agent**
- Clarifiying the flow requirements (with tools to re-prompt user)
- With access to the flow database and prompts for those flows
- Sytem prompt for flows as well

2. **Planning / Scaffolding Agent**
- GPT-4o or maybe Claude 3.5 with tools for node searching
- And also a tool for finding similar flows
- Ask it to not create a flow but plan for it with:
    - Connections (all of them should be aligned)
    - What are the inputs and outputs to each node
    - What are the nodes that are needed to be created
    - Maybe need like ReAct thinking to get the node, then find similar flows and understand the parameters
- Output in JSON format

3. **O1 Agent / Writer**
- Finally, pass all that information to the writer agent
- Prompt o1 to reason through and self-correct as well

4. **Critique Agent** (might not be needed)
- Have claude 3.5 or gpt-4o to critique the flow and give feedback (separated into critical and non-critical)
- Ask o1 to make the necessary changes
- Loop until 3.5 is satisfied (max 3 times until critical feedback is satisfied)

---

I do feel we kinda need a node-search agent to find the node, then find similar flows and understand the parameters.
