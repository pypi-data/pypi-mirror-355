from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage, BaseMessage


OUTPUT_GENERATION_PROMPT = """
# Final Result Aggregation & Presentation Agent

## Objective
You are a **Final Result Aggregation & Presentation Agent**. Your task is to extract and reformat final outcomes, conclusions, and key decisions directly from the provided multi-modal conversation context. You do **not** generate new ideas or summaries—only **present** what has already been concluded.

### Provided Inputs (this is for your context never add this in output):
- **Call Summary**:  
  `{call_summary}`

- **Call Transcript**:  
  `{call_transcript}`

- **Agent Conversation Transcript**:  
  `{agent_conversation_transcript}`

## Operational Constraints
- **DO NOT** add new interpretations, summaries, or speculative commentary.
- **DO NOT** change the meaning of any result or conclusion.
- **DO** format and structure the results in clean Markdown for presentation.
- **DO** merge overlapping or similar outputs from multiple agents into one coherent, non-redundant result item—**as long as their meaning aligns**.
- Each merged result must still reflect all contributing sources through attribution.

## Output Format (Strict Markdown)

```
## Introduction
Brief explanation of the purpose of the report and what the reader can expect.

## Context
High-level overview of the source materials used to compile this report (e.g., transcript, summary, agent discussion, Orchestrator guidance).

## Results
This section must contain all finalized results, outcomes, and conclusions directly extracted from conversation history or outputs.
- Aggregate the results from all the agents into coherent, concise points while covering all essential content.
- If agents have kind of similar points or reasoning, you must merge them into one point.
- The report should NOT be very long, and you cannot just copy-paste responses from every agent. It should look like a single agent has generated the report but based on insights from all.
- If there is some error or some agent has not given any presentable output, skip that instead of showing error messages or questions asked by that agent.
- Format content into readable bullets, tables, or subheadings.
- **DO NOT** summarize, rewrite, or omit essential content.
- **DO** merge points that are duplicative or semantically equivalent, while preserving the original meaning and full attribution.
- Attribute merged content using phrases like:  
  _“As concluded by both Agent A and Agent B…”_ or  
  _“Supported by multiple agents including [X, Y]…”_
- There should not be any section like Follow up actions, next steps, etc. This is a strict instruction.

## Viewpoints
This section should capture where agents agreed or disagreed on specific topics.
- Write in third-person objective style.
- Clearly describe differing positions, even if unresolved.
- Only include points where there's clear contrast or alignment.
- Use patterns such as:  
  _“Agent A argued that [...], while Agent B disagreed, stating that [...]”_  
  _“Both Agent C and Agent D supported the approach of [...].”_
```

## Example Transformation

**Input 1 (Agent A):**  
“We should prioritize automating reporting.”  
**Input 2 (Agent B):**  
“Automated reporting could be an early win.”

**Output (Merged in Results):**
- **Automation Priority:** Reporting automation identified as a key early win and strategic priority.  
  _– As suggested by both Agent A and Agent B._

**Output (Viewpoints):**
- Both Agent A and Agent B agreed that reporting automation should be prioritized early for impact and efficiency.

"""


class Report(BaseModel):
    markdown_formatted_report: str = Field(
        description="The markdown formatted comprehensive report which will be showned to user"
    )


def parse_base_messages_to_transcript(messages: list[BaseMessage]) -> str:
    transcript = []

    last_tool_agent = ""
    for message in messages:
        if isinstance(message, HumanMessage):
            transcript.append(f"**User:** {message.text()}")
        elif isinstance(message, AIMessage):
            transcript.append(f"**Host Agent:** {message.text()}")
            for tool_call in message.tool_calls:
                if tool_call.get("name") and tool_call.get("name") == "send_task":
                    last_tool_agent = tool_call.get("args").get("agent_name")
                    message_to_send = tool_call.get("args").get("message")
                    transcript.append(
                        f"**Host Agent to {last_tool_agent}:** {message_to_send}"
                    )
        elif isinstance(message, ToolMessage):
            transcript.append(f"**{last_tool_agent} Responds:** {message.text()}")
        else:
            pass

    return "\n\n".join(transcript)


def generate_final_response(
    call_summary: str,
    call_transcript: str,
    conversation_history: list[BaseMessage],
) -> str:
    """
    Generate a final comprehensive report based on the call summary, transcript, and conversation history.

    Args:
        call_summary: Summary of the call
        call_transcript: Transcript of the call
        conversation_history: List of messages from the conversation (can be BaseMessage objects or dictionaries)

    Returns:
        A formatted markdown report
    """

    # Create the prompt template and model
    try:
        prompt = ChatPromptTemplate.from_template(OUTPUT_GENERATION_PROMPT)
        model = ChatOpenAI(model="gpt-4o", temperature=0)
        structured_llm = model.with_structured_output(Report)
        chain = prompt | structured_llm

        # Invoke the chain with all inputs
        response = chain.invoke(
            {
                "call_summary": call_summary,
                "call_transcript": call_transcript,
                "agent_conversation_transcript": parse_base_messages_to_transcript(
                    conversation_history
                ),
            }
        )

        return response.markdown_formatted_report
    except Exception as e:
        print(f"Error generating final response: {e}")
        return f"Error generating report: {str(e)}"
