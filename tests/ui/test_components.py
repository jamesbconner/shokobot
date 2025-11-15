"""Unit tests for UI components."""

import gradio as gr

from ui.components import create_examples, create_header, create_settings_panel


class TestCreateHeader:
    """Tests for create_header function."""

    def test_create_header_returns_markdown(self) -> None:
        """Test that create_header returns a Markdown component."""
        header = create_header()

        assert isinstance(header, gr.Markdown)

    def test_create_header_contains_title(self) -> None:
        """Test that header contains the title."""
        header = create_header()

        # Access the value attribute which contains the markdown text
        assert "ShokoBot" in header.value
        assert "🎌" in header.value

    def test_create_header_contains_description(self) -> None:
        """Test that header contains a description."""
        header = create_header()

        assert "anime" in header.value.lower()


class TestCreateExamples:
    """Tests for create_examples function."""

    def test_create_examples_returns_list(self) -> None:
        """Test that create_examples returns a list."""
        examples = create_examples()

        assert isinstance(examples, list)

    def test_create_examples_has_minimum_count(self) -> None:
        """Test that at least 5 examples are provided."""
        examples = create_examples()

        assert len(examples) >= 5

    def test_create_examples_all_strings(self) -> None:
        """Test that all examples are strings."""
        examples = create_examples()

        assert all(isinstance(ex, str) for ex in examples)

    def test_create_examples_diverse_types(self) -> None:
        """Test that examples cover diverse query types."""
        examples = create_examples()
        examples_text = " ".join(examples).lower()

        # Check for different query patterns
        assert "similar" in examples_text or "like" in examples_text
        assert "best" in examples_text or "recommend" in examples_text
        assert "about" in examples_text or "tell me" in examples_text

    def test_create_examples_non_empty(self) -> None:
        """Test that all examples are non-empty."""
        examples = create_examples()

        assert all(len(ex.strip()) > 0 for ex in examples)


class TestCreateSettingsPanel:
    """Tests for create_settings_panel function."""

    def test_create_settings_panel_returns_tuple(self) -> None:
        """Test that create_settings_panel returns a tuple."""
        result = create_settings_panel()

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_create_settings_panel_slider_type(self) -> None:
        """Test that first element is a Slider."""
        k_slider, _ = create_settings_panel()

        assert isinstance(k_slider, gr.Slider)

    def test_create_settings_panel_checkbox_type(self) -> None:
        """Test that second element is a Checkbox."""
        _, show_context = create_settings_panel()

        assert isinstance(show_context, gr.Checkbox)

    def test_slider_range(self) -> None:
        """Test that slider has correct range."""
        k_slider, _ = create_settings_panel()

        assert k_slider.minimum == 1
        assert k_slider.maximum == 20

    def test_slider_default_value(self) -> None:
        """Test that slider has correct default value."""
        k_slider, _ = create_settings_panel()

        assert k_slider.value == 10

    def test_slider_step(self) -> None:
        """Test that slider has correct step."""
        k_slider, _ = create_settings_panel()

        assert k_slider.step == 1

    def test_checkbox_default_value(self) -> None:
        """Test that checkbox has correct default value."""
        _, show_context = create_settings_panel()

        assert show_context.value is False

    def test_slider_has_label(self) -> None:
        """Test that slider has a label."""
        k_slider, _ = create_settings_panel()

        assert k_slider.label is not None
        assert len(k_slider.label) > 0

    def test_checkbox_has_label(self) -> None:
        """Test that checkbox has a label."""
        _, show_context = create_settings_panel()

        assert show_context.label is not None
        assert len(show_context.label) > 0
