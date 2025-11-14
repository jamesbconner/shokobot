"""Main Gradio application for ShokoBot web interface."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

import gradio as gr
from langchain_core.documents import Document

from services.app_context import AppContext
from ui.components import create_examples, create_header, create_settings_panel
from ui.utils import format_error_message, initialize_rag_chain, validate_environment

logger = logging.getLogger(__name__)

# Global state for RAG chain (initialized once)
_rag_chain: Callable[[str], tuple[str, list[Document]]] | None = None
_app_context: AppContext | None = None


def get_or_create_context() -> AppContext:
    """Get or create application context (singleton).

    Returns:
        Application context instance.
    """
    global _app_context
    if _app_context is None:
        _app_context = AppContext.create()
    return _app_context


def get_or_create_chain() -> Callable[[str], tuple[str, list[Document]]]:
    """Get or create RAG chain (singleton).

    Returns:
        RAG chain callable.
    """
    global _rag_chain
    if _rag_chain is None:
        ctx = get_or_create_context()
        _rag_chain = initialize_rag_chain(ctx)
    return _rag_chain


def format_context(docs: list[Document]) -> str:
    """Format retrieved documents as HTML.

    Args:
        docs: Retrieved documents with metadata.

    Returns:
        HTML string with formatted context.
    """
    if not docs:
        return "<p><em>No context documents available.</em></p>"

    html_parts = ["<div style='margin-top: 20px;'>", "<h3>📚 Retrieved Context</h3>"]

    for i, doc in enumerate(docs, 1):
        metadata = doc.metadata
        title = metadata.get("title_main", "Unknown Title")
        anime_id = metadata.get("anime_id", "N/A")
        distance = metadata.get("_distance_score", 0.0)

        # Convert distance to similarity score (lower distance = higher similarity)
        # For display purposes, show as percentage
        similarity = max(0, 100 - (distance * 100))

        # Truncate content for display
        content = doc.page_content[:300]
        if len(doc.page_content) > 300:
            content += "..."

        html_parts.append(
            f"""
            <details style='margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px;'>
                <summary style='cursor: pointer; font-weight: bold;'>
                    {i}. {title} (ID: {anime_id}) - Similarity: {similarity:.1f}%
                </summary>
                <div style='margin-top: 10px; padding: 10px; background: #f9f9f9;'>
                    <p>{content}</p>
                </div>
            </details>
            """
        )

    html_parts.append("</div>")
    return "".join(html_parts)


async def query_handler(
    message: str,
    history: list[tuple[str, str]],
    k: int,
    show_context: bool,
) -> tuple[str, str]:
    """Handle user queries and return responses.

    Args:
        message: User's question.
        history: Conversation history.
        k: Number of documents to retrieve.
        show_context: Whether to show retrieved context.

    Returns:
        Tuple of (answer, context_html).
    """
    # Validate input
    if not message or not message.strip():
        return "Please enter a question.", ""

    try:
        # Get RAG chain
        chain = get_or_create_chain()

        # Update retrieval k in context
        ctx = get_or_create_context()
        ctx.retrieval_k = k

        logger.info(f"Processing query: {message[:100]}... (k={k})")

        # Execute chain (it's async)
        answer, docs = await chain(message)

        # Format context if requested
        context_html = ""
        if show_context and docs:
            context_html = format_context(docs)

        logger.info(f"Query processed successfully, returned {len(docs)} documents")
        return answer, context_html

    except ValueError as e:
        error_msg = format_error_message(e)
        return f"❌ {error_msg}", ""
    except Exception as e:
        error_msg = format_error_message(e)
        return f"❌ {error_msg}", ""


def create_app() -> gr.Blocks:
    """Create and configure the Gradio application.

    Returns:
        Configured Gradio Blocks application.
    """
    # Validate environment before creating app
    try:
        validate_environment()
    except EnvironmentError as e:
        logger.error(f"Environment validation failed: {e}")
        # Create a simple error app
        with gr.Blocks(title="🎌 ShokoBot - Configuration Error") as error_app:
            gr.Markdown("# ⚠️ Configuration Error")
            gr.Markdown(f"**{e}**")
            gr.Markdown(
                """
                Please ensure:
                1. `OPENAI_API_KEY` is set in your `.env` file
                2. You have run `shokobot ingest` to initialize the vector database
                """
            )
        return error_app

    # Create main application
    with gr.Blocks(
        title="🎌 ShokoBot - Anime Recommendations",
        theme=gr.themes.Soft(),
    ) as demo:
        # Header
        create_header()

        # Main chat interface
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Chat",
                    height=500,
                    show_copy_button=True,
                    type="messages",  # Use OpenAI-style messages format
                )

                msg = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask me anything about anime...",
                    lines=2,
                )

                with gr.Row():
                    submit = gr.Button("Send", variant="primary")
                    clear = gr.Button("Clear")

                # Examples
                gr.Examples(
                    examples=create_examples(),
                    inputs=msg,
                    label="Try these examples:",
                )

            # Settings panel
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Settings")
                k_slider, show_context_checkbox = create_settings_panel()

        # Context display area
        context_display = gr.HTML(label="Context", visible=True)

        # Define interaction logic
        def user_message(
            user_msg: str, history: list[dict[str, str]]
        ) -> tuple[str, list[dict[str, str]]]:
            """Add user message to history."""
            return "", history + [{"role": "user", "content": user_msg}]

        def bot_response(
            history: list[dict[str, str]],
            k: int,
            show_context: bool,
        ) -> tuple[list[dict[str, str]], str]:
            """Generate bot response."""
            if not history or history[-1].get("role") != "user":
                return history, ""

            user_msg = history[-1]["content"]

            # Convert history to tuple format for query_handler
            tuple_history = [
                (msg["content"], history[i + 1]["content"])
                for i, msg in enumerate(history[:-1])
                if msg.get("role") == "user" and i + 1 < len(history)
            ]

            # Run async query handler
            answer, context_html = asyncio.run(
                query_handler(user_msg, tuple_history, k, show_context)
            )

            # Add assistant response to history
            history.append({"role": "assistant", "content": answer})
            return history, context_html

        # Wire up events
        msg.submit(
            user_message,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
            queue=False,
        ).then(
            bot_response,
            inputs=[chatbot, k_slider, show_context_checkbox],
            outputs=[chatbot, context_display],
        )

        submit.click(
            user_message,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
            queue=False,
        ).then(
            bot_response,
            inputs=[chatbot, k_slider, show_context_checkbox],
            outputs=[chatbot, context_display],
        )

        clear.click(lambda: ([], ""), outputs=[chatbot, context_display], queue=False)

    return demo


if __name__ == "__main__":
    app = create_app()
    app.launch()
