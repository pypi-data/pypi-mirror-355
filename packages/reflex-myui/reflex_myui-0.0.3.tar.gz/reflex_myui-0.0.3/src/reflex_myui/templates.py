"""Common templates used between pages in the app."""

from __future__ import annotations

import reflex as rx
from reflex.event import EventType
from typing import Callable

from .header import header, navbar_v2, NavItem
from .footer import footer

# Meta tags for the app.
default_meta = [
    {
        "name": "viewport",
        "content": "width=device-width, shrink-to-fit=no, initial-scale=1",
    },
]


def create_landing_template(
    logo_src: str,
    logo_type: str,
    nav_list: list,
    copyright_: str,
    footer_links_deep: list,
    footer_links_social: list,
):
    """Creates the landing page template."""

    def template(
        route: str | None = None,
        title: str | None = None,
        image: str | None = None,
        description: str | None = None,
        meta: str | None = None,
        script_tags: list[rx.Component] | None = None,
        on_load: EventType[()] | None = None,
    ) -> Callable[[Callable[[], rx.Component]], rx.Component]:
        """The template for each page of the app.

        Args:
            route: The route to reach the page.
            title: The title of the page.
            image: The favicon of the page.
            description: The description of the page.
            meta: Additionnal meta to add to the page.
            on_load: The event handler(s) called when the page load.
            script_tags: Scripts to attach to the page.

        Returns:
            The template with the page content.
        """

        def decorator(page_content: Callable[[], rx.Component]) -> rx.Component:
            """The template for each page of the app.

            Args:
                page_content: The content of the page.

            Returns:
                The template with the page content.
            """
            # Get the meta tags for the page.
            all_meta = [*default_meta, *(meta or [])]

            @rx.page(
                route=route,
                title=title,
                image=image,
                description=description,
                meta=all_meta,
                script_tags=script_tags,
                on_load=on_load,
            )
            def templated_page() -> rx.Component:
                return rx.vstack(
                    header(logo_src, logo_type, nav_list),
                    # navbar_v2(nav_links),
                    rx.vstack(
                        page_content(),
                        margin_top="50px",
                        width="100%",
                        max_width="80em",
                        height="100%",
                        min_height="calc(100vh - 50px)",
                        background=rx.color("sky", 3),
                        align="center",
                        justify="center",
                    ),
                    footer(
                        logo_type, copyright_, footer_links_deep, footer_links_social
                    ),
                    background=rx.color("sky", 3),
                    # class_name = rx.color_mode_cond(
                    #     light="theme-light",
                    #     dark="theme-dark",
                    # ),
                    align="center",
                    justify="center",
                    spacing="0",
                    padding="0rem 1rem 0rem 1rem",
                )

            return templated_page()

        return decorator

    return template
