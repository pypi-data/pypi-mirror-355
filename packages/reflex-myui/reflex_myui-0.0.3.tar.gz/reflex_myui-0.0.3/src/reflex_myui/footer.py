import reflex as rx
from reflex_simpleicons import simpleicons


def _footer_brand(logo_type: str, copyright_: str) -> rx.Component:
    return rx.vstack(
        rx.text(logo_type, weight="bold", size="2"),
        rx.text(copyright_, weight="medium", size="2"),
        min_width="200px",
        padding="1em 0em",
    )


def _footer_links_deep(link_item: dict[str, str]) -> rx.Component:
    return rx.link(
        rx.text(
            link_item["name"].upper(),
            size="1",
            weight="medium",
            # color=rx.color("slate", 12)
        ),
        href=link_item["href"],
        text_decoration="none",
        # on_click=SiteRoutingState.toggle_page_change(data),
    )


def _footer_links_social(link_item: dict[str, str]) -> rx.Component:
    return rx.link(
        simpleicons(
            link_item["name"],
            # color=rx.color("slate", 12),
            size=22,
        ),
        href=link_item["href"],
        text_decoration="none",
        is_external=True,
        # on_click=SiteRoutingState.toggle_page_change(data),
    )


def footer_nav_deep(footer_links_deep: list, footer_links_social: list) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            *[_footer_links_deep(link_item) for link_item in footer_links_deep],
            rx.spacer(),
            *[_footer_links_social(link_item) for link_item in footer_links_social],
            width="100%",
            align="center",
            justify="between",
        ),
        width="100%",
        align="center",
        justify="between",
    )


def footer(
    logo_type: str,
    copyright_: str,
    footer_links_deep: list[dict[str, str]],
    footer_links_social: list[dict[str, str]],
) -> rx.Component:
    """
    Footer component for the app.

    This component is used to display the footer of the app.
    It includes the logo, copyright, and footer links.

    Args:
        logo_type (str): The brand logo displayed as text.
        copyright_ (str): The copyright text.
        footer_links_deep (list[dict[str, str]]): The footer links to be displayed.
            Each link is a dictionary with 'name' and 'href' keys.
            'name' is the text to be displayed and 'href' is the URL to navigate to.
            Example:
                [
                    {"name": "link_1", "href": "/"},
                    {"name": "link_2", "href": "/"},
                ]
    Returns:
        rx.Component: The footer component.


    """
    return rx.hstack(
        _footer_brand(logo_type, copyright_),
        # stack("Product", footer_data["product"]),
        # stack("Company", footer_data["company"]),
        # stack("Resources", footer_data["resources"]),
        # stack("Developers", footer_data["developers"]),
        # stack("Industries", footer_data["industries"]),
        rx.divider(),
        footer_nav_deep(footer_links_deep, footer_links_social),
        width="100%",
        height="100%",
        wrap="wrap",
        gap="1em",
        padding="1em",
        z_index="1000",
        background=rx.color("sky", 3),
    )
