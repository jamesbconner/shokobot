"""Reusable UI components for Gradio interface."""

import gradio as gr


def create_header() -> gr.Markdown:
    """Create the header with title and description.

    Returns:
        Gradio Markdown component with header content.
    """
    header_text = """
    # 🎌 ShokoBot - Anime Recommendations
    
    Ask me anything about anime from your collection! I use semantic search and AI
    to help you discover new shows based on your preferences.
    """
    return gr.Markdown(header_text)


def create_examples() -> list[str]:
    """Return list of example queries.

    Returns:
        List of example query strings.
    """
    return [
        "What anime are similar to Cowboy Bebop?",
        "Best mecha anime?",
        "Tell me about Steins;Gate",
        "Recommend action anime",
        "What's a good starter anime?",
    ]


def create_settings_panel() -> tuple[gr.Slider, gr.Checkbox]:
    """Create the configuration panel with k slider and context checkbox.

    Returns:
        Tuple of (slider, checkbox) components.
    """
    k_slider = gr.Slider(
        minimum=1,
        maximum=20,
        value=10,
        step=1,
        label="Documents to retrieve (k)",
        info="Number of anime to search for context",
    )

    show_context = gr.Checkbox(
        label="Show retrieved context",
        value=False,
        info="Display the anime documents used to generate the answer",
    )

    return k_slider, show_context
