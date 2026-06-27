from pathlib import Path

from django.conf import settings
from playwright.sync_api import sync_playwright
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas


def build_in_the_sky_chart_url(event):
    if not event.event_date:
        return ""

    hour = 20
    minute = 0

    if event.start_time:
        hour = event.start_time.hour
        minute = event.start_time.minute

    return (
        "https://in-the-sky.org/skymap2.php?"
        f"day={event.event_date.day}"
        f"&month={event.event_date.month}"
        f"&year={event.event_date.year}"
        f"&hour={hour}"
        f"&min={minute}"
        "&town=4671654"
        "&limmag=4"
    )


def capture_star_chart_image(event):
    output_dir = Path(settings.MEDIA_ROOT) / "star_charts"
    output_dir.mkdir(parents=True, exist_ok=True)

    image_path = output_dir / f"event_{event.id}_chart.png"
    url = build_in_the_sky_chart_url(event)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        page = browser.new_page(
            viewport={"width": 1400, "height": 1200}
        )

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_selector(".PLhost", timeout=60000)
        page.wait_for_timeout(5000)

        try:
            page.evaluate("""
            () => {
                const colorSelector = document.querySelector('.pl_colors');

                if (colorSelector) {
                    colorSelector.value = "5";
                    colorSelector.dispatchEvent(
                        new Event('change', { bubbles: true })
                    );
                }
            }
            """)

            page.wait_for_timeout(3000)

        except Exception:
            pass

        try:
            page.evaluate("""
            () => {
                const stickFigures = document.querySelector('.chkcl');

                if (stickFigures) {
                    stickFigures.checked = true;
                    stickFigures.dispatchEvent(
                        new Event('change', { bubbles: true })
                    );
                }
            }
            """)

            page.wait_for_timeout(2000)

        except Exception:
            pass

        try:
            page.evaluate("""
            () => {
                const constellationNames = document.querySelector('.chkcn');

                if (constellationNames) {
                    constellationNames.checked = true;
                    constellationNames.dispatchEvent(
                        new Event('change', { bubbles: true })
                    );
                }
            }
            """)

            page.wait_for_timeout(2000)

        except Exception:
            pass

        try:
            page.evaluate("""
            () => {
                const planetLabels = document.querySelector('.chklp');

                if (planetLabels) {
                    planetLabels.checked = true;
                    planetLabels.dispatchEvent(
                        new Event('change', { bubbles: true })
                    );
                }
            }
            """)

            page.wait_for_timeout(2000)

        except Exception:
            pass

        try:
            page.evaluate("""
            () => {
                const deepSkyShow = document.querySelector('.chksn');
                const deepSkyLabels = document.querySelector('.chkln');

                if (deepSkyShow) {
                    deepSkyShow.checked = true;
                    deepSkyShow.dispatchEvent(
                        new Event('change', { bubbles: true })
                    );
                }

                if (deepSkyLabels) {
                    deepSkyLabels.checked = false;
                    deepSkyLabels.dispatchEvent(
                        new Event('change', { bubbles: true })
                    );
                }
            }
            """)

            page.wait_for_timeout(2000)

        except Exception:
            pass

        try:
            page.evaluate("""
            () => {
                const starsShow = document.querySelector('.chkss');
                const starLabels = document.querySelector('.chkls');

                if (starsShow) {
                    starsShow.checked = true;
                    starsShow.dispatchEvent(
                        new Event('change', { bubbles: true })
                    );
                }

                if (starLabels) {
                    starLabels.checked = false;
                    starLabels.dispatchEvent(
                        new Event('change', { bubbles: true })
                    );
                }
            }
            """)

            page.wait_for_timeout(2000)

        except Exception:
            pass
        
        page.evaluate("""
        () => {
            const selectors = [
                'nav',
                '.navbar',
                '.topnav',
                '.mainnav',
                '.its-topnav',
                '.site-header',
                '.header',
                '#header',
                '.navigation',
                '.navbar-dark',
                '.bannerfade',
                '.noprint',
                '.PLplace_div',
                '.br2_overlay',
                '.br3_overlay',
                '.information_holder',
                '.PLload',
                '.PLinstruct',
                '.PLcrosshair',
                'hr'
            ];

            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    el.style.display = 'none';
                });
            });
        }
        """)

        chart = page.locator(".PLhost").first
        chart.screenshot(path=str(image_path))

        browser.close()

    return image_path


def format_time_range(event):
    if event.start_time and event.end_time:
        return (
            f"{event.start_time.strftime('%I:%M %p').lstrip('0')} - "
            f"{event.end_time.strftime('%I:%M %p').lstrip('0')}"
        )

    return ""


def generate_star_chart_pdf(event):
    output_dir = Path(settings.MEDIA_ROOT) / "star_charts"
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / f"event_{event.id}_star_chart.pdf"
    chart_image_path = capture_star_chart_image(event)

    c = canvas.Canvas(str(pdf_path), pagesize=landscape(letter))
    width, height = landscape(letter)

    time_string = format_time_range(event)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(36, height - 36, "AAS Outreach Star Chart")

    c.setFont("Helvetica", 10)
    c.drawString(36, height - 54, f"Event: {event.event_name}")
    c.drawString(36, height - 68, f"Date: {event.event_date}")
    c.drawString(36, height - 82, f"Time: {time_string}")
    c.drawString(36, height - 96, f"Partner: {event.partner}")

    c.drawImage(
        str(chart_image_path),
        36,
        36,
        width=720,
        height=480,
        preserveAspectRatio=True,
        anchor="c",
    )

    c.save()

    return pdf_path