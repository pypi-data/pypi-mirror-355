"""Contains the demo app."""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

from __future__ import annotations

# from typing import cast

# Textual imports
from textual.app import App, ComposeResult
from textual import on
from textual.binding import Binding

from textual.widget import Widget
from textual.widgets import Header, Footer, Static, Button, RichLog
from textual.containers import Horizontal, Container

from textual_slidecontainer.slidecontainer import SlideContainer


class MySlideContainer(SlideContainer):

    def __init__(self) -> None:
        super().__init__(
            slide_direction="down",
            start_open=False,
            classes="slidecontainer bottom",
            id="bottom_slidecontainer",
        )

    def compose(self) -> ComposeResult:

        with Container():
            yield Button("Hide", id="button_bottom")
            yield Static(
                "Fade is [red]off.[/red] " "Default is [yellow]closed.[/yellow] " "Menu is [yellow]floating."
            )


class SlideContainerDemo(App[None]):

    CSS_PATH = "demostyles.tcss"

    BINDINGS = [
        Binding("ctrl+w", "toggle_container('top')", "Top menu"),
        Binding("ctrl+a", "toggle_container('left')", "Left menu"),
        Binding("ctrl+s", "toggle_container('bottom')", "Bottom menu"),
        Binding("ctrl+d", "toggle_container('right')", "Right menu"),
    ]

    TITLE = "Textual-SlideContainer Demo"

    def compose(self) -> ComposeResult:

        yield Header()

        self.main_container = Container(id="main_container")
        self.main_container.styles.opacity = 0.0  # the madlad loading screen
        with self.main_container:

            # There are 3 different ways to add children to a widget in Textual,
            # and all of them work with SlideContainer:
            # 1) Context manager
            # 2) Pass a list of widgets to the constructor
            # 3) Custom widget with compose method

            # 1) Context manager
            with SlideContainer(
                classes="slidecontainer top",
                id="top_slidecontainer",
                slide_direction="up",
                floating=False,  # Note this is True by default
                fade=True,  # and this is False by default
            ):
                yield Button("Hide", id="button_top")
                yield Static(
                    "Fade is [yellow]on.[/yellow] "
                    "Default is [yellow]open.[/yellow] "
                    "Menu is [red]not floating."
                )

            # 2) Create a list of widgets to pass to the next SlideContainer...
            window_widgets: list[Widget] = [
                Button("Hide", id="button_left"),
                Static(
                    "Fade is [red]off.[/red]\n"
                    "Default is [yellow]open.[/yellow]\n"
                    "Menu is [red]not floating."
                ),
            ]
            with Horizontal(id="horizontal_container"):

                # ...then pass a list of widgets to the constructor
                yield SlideContainer(
                    *window_widgets,
                    classes="slidecontainer leftright",
                    id="left_slidecontainer",
                    slide_direction="left",
                    floating=False,
                    duration=1.0,  # <-- you can change the animation duration.
                    easing_function="out_cubic",  # <-- you can change the easing function.
                )

                with Container(id="main_content"):
                    yield Static("This is content at the top left.", classes="top_docked")
                    yield Static(
                        "This is content \non the right \nthat can be blocked.", classes="right_docked"
                    )
                    yield RichLog()
                    yield Static(
                        "This is content at the bottom that can be blocked by the floating menu.",
                        classes="bottom_docked w_1fr",
                    )

                with SlideContainer(
                    classes="slidecontainer leftright",
                    id="right_slidecontainer",  # Floating mode is the default.
                    slide_direction="right",  # When floating, It'll auto-dock to the same direction.
                    start_open=False,
                    fade=True,
                ):
                    yield Button("Hide", id="button_right")
                    yield Static(
                        "Fade is [yellow]on.[/yellow]\n"
                        "Default is [red]closed.[/red]\n"
                        "Menu is [yellow]floating."
                    )

            # 3) Custom widget with compose method
            yield MySlideContainer()

        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted. This is a good place to set up event listeners."""
        self.query_one(RichLog).can_focus = False

    def action_toggle_container(self, direction: str) -> None:
        """Toggle the slidecontainer open and closed."""
        slidecontainer = self.query_one(f"#{direction}_slidecontainer", SlideContainer)
        slidecontainer.toggle()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Toggle the slidecontainer open and closed."""
        assert event.button.id  # for type checking
        direction = event.button.id.split("_")[1]  # remove the `button_` prefix
        self.action_toggle_container(direction)

    @on(SlideContainer.InitClosed)
    def finished_loading(self) -> None:
        """This is a madlad way of making a loading screen. The main container starts
        at opacity 0.0 and fades in to 1.0 when the slidecontainer is done loading."""

        self.main_container.styles.animate("opacity", value=1.0, duration=0.3)
        # self.main_container.styles.opacity = 1.0     # this would be the simpler way of doing it.

    @on(SlideContainer.SlideCompleted)
    def slide_completed(self, event: SlideContainer.SlideCompleted) -> None:

        rich_log = self.query_one(RichLog)
        rich_log.write(f"{event.container.id} {"opened" if event.state else "closed"}")


def run_demo() -> None:
    SlideContainerDemo().run()


if __name__ == "__main__":
    run_demo()
