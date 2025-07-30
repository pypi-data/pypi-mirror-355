import reflex as rx
from .state import DrawerState
from typing import TypedDict, Optional


def _logo_icon(logo_src: str) -> rx.Component:
    return rx.image(
        src=logo_src,
        width="22px",
        height="22px",
        border_radius="100%",
        object_fit="fit",
        border=f"1px solid {rx.color('slate', 12)}",
        display=["none", "none", "none", "none", "flex", "flex"],
    )


def _logo_type(logo_type: str) -> rx.Component:
    return rx.link(
        rx.heading(
            logo_type.upper(),
            font_size="0.9em",
            font_weight="800",
            cursor="pointer",
        ),
        href="/",
        text_decoration="none",
        # on_click=SiteRoutingState.toggle_page_change(data)
    )


def identity(logo_src: str, logo_type: str) -> rx.Component:
    return rx.hstack(
        _logo_icon(logo_src),
        _logo_type(logo_type),
        align="center",
    )


def _link_item(link_item) -> rx.Component:
    return rx.link(
        link_item["name"],
        href=link_item["href"],
        text_decoration="none",
        underline="none",
    )


def _menu_item(menu_item: dict) -> rx.Component:
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.text(
                    menu_item["name"],
                ),
                rx.icon("chevron-down"),
                weight="medium",
                variant="ghost",
            ),
        ),
        rx.menu.content(
            *[rx.menu.item(_link_item(item)) for item in menu_item["href"]],
        ),
    )


def nav_item(nav_item: dict) -> rx.Component:
    if isinstance(nav_item["href"], str):
        return _link_item(nav_item)
    elif isinstance(nav_item["href"], list):
        return _menu_item(nav_item)
    else:
        raise ValueError("Invalid href type")


def navbar(nav_list: list) -> rx.Component:
    return rx.hstack(
        *[nav_item(item) for item in nav_list],
        align="center",
        display=["none", "none", "none", "none", "flex", "flex"],
        spacing="5",
    )


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


def _header_color_mode() -> rx.Component:
    return __header_icon(
        rx.el.button(
            rx.color_mode_cond(
                light=rx.icon(
                    "moon",
                    size=14,
                    # color=rx.color("slate", 12),
                ),
                dark=rx.icon(
                    "sun",
                    size=14,
                    # color=rx.color("slate", 12),
                ),
            ),
            on_click=rx.toggle_color_mode,
        ),
    )


def _header_drawer_button() -> rx.Component:
    return __header_icon(
        rx.el.button(
            rx.icon(tag="align-right", size=15),
            on_click=DrawerState.toggle_drawer,
            size="1",
            variant="ghost",
            # color_scheme="gray",
            cursor="pointer",
            display=["flex", "flex", "flex", "flex", "none", "none"],
        )
    )


def _link_sidebar(nav_item: dict) -> rx.Component:
    return rx.link(
        rx.hstack(
            # rx.icon(icon),
            rx.text(nav_item["name"], size="4"),
            width="100%",
            padding_x="1rem",
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
        href=nav_item["href"],
        underline="none",
        weight="medium",
        width="100%",
    )


def _menu_sidebar(menu_item: dict) -> rx.Component:
    return rx.accordion.root(
        rx.accordion.item(
            header=rx.text(menu_item["name"], size="4", weight="medium"),
            content=rx.vstack(
                *[_link_sidebar(item) for item in menu_item["href"]],
                spacing="1",
                width="100%",
            ),
            # weight="medium",
        ),
        collapsible=True,
        variant="ghost",
    )


def sidebar_item(nav_item: dict) -> rx.Component:
    if isinstance(nav_item["href"], str):
        return _link_sidebar(nav_item)
    elif isinstance(nav_item["href"], list):
        return _menu_sidebar(nav_item)
    else:
        raise ValueError("Invalid href type")


def sidebar(logo_src, logo_type, nav_links) -> rx.Component:
    return rx.box(
        rx.drawer.root(
            rx.drawer.trigger(
                __header_icon(
                    rx.el.button(
                        rx.icon(tag="align-right", size=15),
                        on_click=DrawerState.toggle_drawer,
                        size="1",
                        variant="ghost",
                        # color_scheme="gray",
                        cursor="pointer",
                        display=["flex", "flex", "flex", "flex", "none", "none"],
                    ),
                ),
            ),
            rx.drawer.overlay(z_index="1000"),
            rx.drawer.portal(
                rx.drawer.content(
                    rx.vstack(
                        rx.box(
                            rx.drawer.close(
                                __header_icon(
                                    rx.el.button(
                                        rx.icon(tag="x", size=20),
                                        on_click=DrawerState.toggle_drawer,
                                        size="1",
                                        variant="ghost",
                                        # color_scheme="gray",
                                        cursor="pointer",
                                    ),
                                ),
                            ),
                            align="right",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.link(
                                rx.heading(
                                    logo_type.upper(),
                                    font_size="2em",
                                    font_weight="800",
                                    cursor="pointer",
                                ),
                                href="/",
                                text_decoration="none",
                                padding="1em",
                            ),
                            *[sidebar_item(item) for item in nav_links],
                            spacing="1",
                            width="100%",
                        ),
                        spacing="5",
                        width="100%",
                    ),
                    top="auto",
                    right="auto",
                    height="100%",
                    width="20em",
                    padding="1.5em",
                    background=rx.color("sky", 3),
                ),
                width="100%",
            ),
            open=DrawerState.is_open,
            direction="left",
        ),
        padding="1em",
    )


def utility(logo_src: str, logo_type: str, nav_links: list) -> rx.Component:
    return rx.hstack(
        _header_color_mode(),
        align="center",
    )


def header(
    logo_src: str,
    logo_type: str,
    navigation_list: list,
) -> rx.Component:
    """
    Header component for the app.

    This component includes a logo, a navigation bar, and utility items.

    Args:
        logo_src (str): The source URL for the logo image.
        logo_type (str): The type of the logo, displayed as text.
        navigation_list (list): A list of dictionaries representing the navigation items.
            Each dictionary should have a 'name' and 'href' key. The 'href' can be a string or a list of dictionaries. If it's a list, each dictionary in the list should also have 'name' and 'href' keys.

            Example:
                [
                    {"name": "link_1", "href": "/"},
                    {"name": "link_2", "href": "/"},
                    {"name": "menu_1", "href": [{"name": "link_1", "href": "/"}, {"name": "link_2", "href": "/"}]}
                ]

    Returns:
        rx.Component: The header component.
    """
    return rx.hstack(
        rx.hstack(
            sidebar(logo_src, logo_type, navigation_list),
            identity(logo_src, logo_type),
            rx.spacer(),
            navbar(navigation_list),
            rx.spacer(),
            utility(logo_src, logo_type, navigation_list),
            width="100%",
            max_width="80em",
            height="50px",
            align="center",
            # justify="between",
        ),
        align="center",
        background=rx.color("sky", 3),
        justify="center",
        padding="0rem 1rem 0rem 1rem",
        position="fixed",
        top="0",
        width="100%",
        z_index="1000",
    )

class SubLink(TypedDict):
    text: str
    href: str
    is_external: bool

class NavItem(rx.Base):
    """A navigation item for the navbar."""
    text: str
    href: str
    is_external: bool
    sub_links: Optional[list[SubLink]]

def _branding() -> rx.Component:
    return rx.box(
        rx.link(
            rx.box(
                rx.icon(
                    "git-branch-plus",
                    class_name="branding-icon",
                ),
                rx.text(
                    "MYUI",
                    as_="span",
                    class_name=rx.color_mode_cond(
                        light="branding-text light",
                        dark="branding-text dark",
                    ),
                ),
                class_name="branding-box",
            ),
            href="/",
            class_name="branding-link",
        ),
        class_name="branding-container",
    )

def dropdown_button(link: rx.Var[NavItem]) -> rx.Component:
       return rx.el.button(
            link["text"],
            rx.icon(
                "chevron-down",
                class_name=rx.cond(
                    State.active_dropdown == link["text"],
                    "h-4 w-4 ml-1 transition-transform transform rotate-180",
                    "h-4 w-4 ml-1 transition-transform",
                ),
            ),
            class_name=rx.cond(
                State.is_dark,
                "flex items-center text-stone-400 hover:text-emerald-400 font-medium h-full",
                "flex items-center text-gray-500 hover:text-emerald-500 font-medium h-full",
            ),
        )

def dropdown_list(link: rx.Var[NavItem]) -> rx.Component:
    return         rx.cond(
            State.active_dropdown == link["text"],
            rx.el.div(
                rx.el.div(
                    rx.foreach(
                        link.to(NavItem)["sub_links"],
                        lambda sub_link: rx.el.a(
                            sub_link["text"],
                            href=sub_link["href"],
                            class_name=rx.cond(
                                State.is_dark,
                                "block px-4 py-2 text-sm text-stone-300 hover:bg-zinc-700",
                                "block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100",
                            ),
                        ),
                    ),
                    class_name=rx.cond(
                        State.is_dark,
                        "w-48 bg-zinc-800 border border-zinc-700 rounded-md shadow-lg py-1",
                        "w-48 bg-white border border-gray-200 rounded-md shadow-lg py-1",
                    ),
                ),
                class_name="absolute top-full pt-2 z-10",
            ),
        )

# rx.menu.root(
#     rx.menu.trigger(
#         rx.button(
#             rx.text(
#                 "Services",
#                 size="4",
#                 weight="medium",
#             ),
#             rx.icon("chevron-down"),
#             weight="medium",
#             variant="ghost",
#             size="3",
#         ),
#     ),
#     rx.menu.content(
#         rx.menu.item("Service 1"),
#         rx.menu.item("Service 2"),
#         rx.menu.item("Service 3"),
#     ),
# ),

def dropdown_menu(link: rx.Var[NavItem]) -> rx.Component:
    """A dropdown menu for a navigation link."""
    return rx.el.div(
        dropdown_button(link),
        dropdown_list(link),
        class_name="relative h-full flex items-center",
        on_mouse_enter=lambda: State.set_active_dropdown(link["text"]),
        on_mouse_leave=State.clear_active_dropdown,
    )

def _nav_link_component(link: NavItem) -> rx.Component:
    """A component to render a navigation link."""
    return rx.cond(
        link.sub_links,
        rx.text("dropdown link"),
        # rx.text("regular link"),
        # dropdown_menu(link),
        rx.link(
            link.text,
            href=link.href,
            is_external=link.is_external,
            class_name=rx.color_mode_cond(
                light="nav-link-component dark",
                dark="nav-link-component light",
            ),
        ),
    )

def _nav(nav_links: list[NavItem]) -> rx.Component:
    return rx.el.nav(
        rx.foreach(
            nav_links,
            _nav_link_component
        ),
        as_="nav",
        class_name="nav-container",
    )

def navbar_v2(nav_links: list[NavItem], is_sticky: bool = True):
    return rx.el.header(
        rx.box(
            _branding(),
            _nav(nav_links),
            class_name="navbar-box",
        ),
        class_name=rx.cond(
            is_sticky,
            rx.color_mode_cond(
                light="navbar light sticky",
                dark="navbar dark sticky",
            ),
            rx.color_mode_cond(
                light="navbar light relative",
                dark="navbar dark relative",
            ),
        ),
    )
