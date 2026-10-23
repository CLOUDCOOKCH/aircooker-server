"""Navigate real PWA controls, including the account and nested pantry destinations."""

from playwright.sync_api import Page

LABELS = {"Home": "Today", "Start": "Heute", "Calendar": "Plan", "Kalender": "Plan"}


def destination(page: Page, label: str):
    if label in ("Settings", "Einstellungen"):
        return page.locator(".account-button")
    return page.get_by_role("navigation").get_by_role(
        "button", name=LABELS.get(label, label), exact=True
    )


def navigate(page: Page, label: str):
    if label in ("Pantry", "Vorrat"):
        shopping = "Shopping list" if label == "Pantry" else "Einkaufsliste"
        destination(page, shopping).click()
        page.locator(".shopping-page .header-actions").get_by_role(
            "button", name=label, exact=True
        ).click()
    else:
        destination(page, label).click()
