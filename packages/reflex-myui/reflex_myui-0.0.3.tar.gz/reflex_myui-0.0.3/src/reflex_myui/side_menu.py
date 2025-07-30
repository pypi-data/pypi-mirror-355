import reflex as rx
from .header import identity
from .state import DrawerState


def __header_icon(component: rx.Component) -> rx.Component:
    return rx.badge(
        component,
        # color_scheme="gray",
        variant="soft",
        width="21px",
        height="21px",
        display="flex",
        align_items="center",
        justify_content="center",
        background="none",
    )


def sidebar_item(text: str, href: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            # rx.icon(icon),
            rx.text(text, size="4"),
            width="100%",
            padding_x="0.5rem",
            padding_y="0.75rem",
            align="center",
            # style={
            #     "_hover": {
            #         "bg": rx.color("accent", 4),
            #         "color": rx.color("accent", 11),
            #     },
            #     "border-radius": "0.5em",
            # },
        ),
        href=href,
        underline="none",
        weight="medium",
        width="100%",
    )


def sidebar_items() -> rx.Component:
    return rx.vstack(
        sidebar_item("Dashboard", "/#"),
        sidebar_item("Projects", "/#"),
        sidebar_item("Analytics", "/#"),
        sidebar_item("Messages", "/#"),
        spacing="1",
        width="100%",
    )


def side_menu() -> rx.Component:
    return rx.drawer.root(
        rx.drawer.trigger(rx.button("Open Drawer")),
        rx.drawer.overlay(),
        rx.drawer.portal(
            rx.drawer.content(
                rx.flex(
                    rx.drawer.close(rx.box(rx.button("Close"))),
                    align_items="start",
                    direction="column",
                ),
                # top="auto",
                # right="auto",
                # height="100%",
                width="20em",
                padding="2em",
                background_color="#FFF",
                as_child=True,
                # background_color=rx.color("green", 3)
            ),
            as_child=True,
        ),
        direction="left",
        as_child=True,
    )
