import reflex as rx


def calculator() -> rx.Component:
    return rx.card(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Tab 1", value="tab1"),
                rx.tabs.trigger("Tab 2", value="tab2"),
            ),
            rx.tabs.content(
                rx.text("item on tab 1"),
                value="tab1",
            ),
            rx.tabs.content(
                rx.text("item on tab 2"),
                value="tab2",
            ),
            default_value="tab1",
            orientation="vertical",
        ),
    )
