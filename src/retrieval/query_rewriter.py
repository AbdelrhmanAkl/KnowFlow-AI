from src.memory.conversation_memory import ConversationMemory


def rewrite_query(
    query: str,
    memory: ConversationMemory | None = None,
) -> str:
    """
    Rewrite a user query into a self-contained retrieval query
    using the current conversation history when available.

    This helps resolve follow-up references such as:
    "How many encoder layers does it have?"
    -> "How many encoder layers does the Transformer architecture have?"
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    cleaned_query = " ".join(query.strip().split())

    if memory is None:
        return cleaned_query

    messages = memory.get_messages()

    if not messages:
        return cleaned_query

    history = []

    for message in messages[-6:]:
        role = message["role"].capitalize()
        content = message["content"].strip()

        if content:
            history.append(f"{role}: {content}")

    conversation_history = "\n".join(history)

    # Only rewrite when there is actual conversational context.
    # The LLM will produce a standalone retrieval query.
    from src.generation.llm import create_llm

    prompt = f"""
You are a query rewriting component for a Retrieval-Augmented
Generation system.

Your job is to rewrite the user's latest question into a
self-contained search query for a vector database.

Rules:
- Preserve the exact intent of the latest question.
- Use previous conversation only to resolve references,
  pronouns, omitted subjects, and follow-up context.
- Do not answer the question.
- Do not add information that is not supported by the conversation.
- If the latest question is already self-contained, return it
  with only minimal cleanup.
- Return ONLY the rewritten search query.
- Do not use quotation marks.
- Do not explain your reasoning.

Conversation History:
{conversation_history}

Latest User Question:
{cleaned_query}
"""

    client = create_llm()

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    rewritten_query = response.text.strip()

    if not rewritten_query:
        return cleaned_query

    return rewritten_query