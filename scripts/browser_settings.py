"""Navigate the real Settings disclosures without altering their visibility in the DOM."""

from playwright.sync_api import Page, expect


def settings_section(page: Page, title: str):
    summary = page.locator(".settings-disclosure > summary").filter(
        has=page.get_by_text(title, exact=True)
    )
    expect(summary).to_have_count(1)
    section = summary.locator("..")
    if section.get_attribute("open") is None:
        summary.click()
    return section
