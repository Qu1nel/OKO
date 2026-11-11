from django.http import HttpRequest

THEME_COOKIE = "oko_theme"


def theme_context(request: HttpRequest) -> dict[str, str]:
    theme = "dark" if request.COOKIES.get(THEME_COOKIE) == "dark" else "light"
    return {"color_theme": theme, "color_theme_cookie": THEME_COOKIE}
