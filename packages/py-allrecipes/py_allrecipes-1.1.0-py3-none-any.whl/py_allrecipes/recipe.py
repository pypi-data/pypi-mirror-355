import requests
from bs4 import BeautifulSoup


class RecipeScraperError(Exception):
    """Custom exception for recipe scraper errors."""

    pass


def get_recipe(url: str) -> dict:
    """Fetches and parses a recipe page from Allrecipes, returning details like title, ingredients, steps, times, servings, and yield.
    Raises RecipeScraperError on network or parsing errors.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RecipeScraperError(f"Network error while fetching recipe: {e}")
    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # Title
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Ingredients
        ingredients = []
        # New: Use the modern Allrecipes class for the ingredient list
        for li in soup.select(".mm-recipes-structured-ingredients__list-item"):
            txt = li.get_text(strip=True)
            if txt:
                ingredients.append(txt)

        # Steps
        steps = []
        ols = soup.select(
            "ol.comp.mntl-sc-block.mntl-sc-block-startgroup.mntl-sc-block-group--OL"
        )
        if ols:
            for ol in ols:
                lis = ol.select(
                    "li.comp.mntl-sc-block.mntl-sc-block-startgroup.mntl-sc-block-group--LI"
                )
                for li in lis:
                    # Only keep text nodes that are not part of images or figure captions
                    texts = []
                    for child in li.contents:
                        # If it's a NavigableString, keep it
                        if hasattr(child, "strip"):
                            txt = str(child).strip()
                            if txt:
                                texts.append(txt)
                        # If it's a tag and not an image or figure, get its text
                        elif getattr(child, "name", None) not in [
                            "img",
                            "figure",
                            "figcaption",
                            "script",
                            "style",
                        ]:
                            # Only get text from tags that are not images/figures, and skip if the tag is a script/style
                            # Remove any HTML tags from the text
                            txt = child.get_text(separator=" ", strip=True)
                            # Remove any HTML tags that may have been left
                            from bs4 import BeautifulSoup as BS

                            txt = BS(txt, "html.parser").get_text(
                                separator=" ", strip=True
                            )
                            if txt and not txt.lower().startswith("dotdash meredith"):
                                texts.append(txt)
                    # Remove step label if present
                    if texts and texts[0].lower().startswith("step"):
                        texts = texts[1:]
                    step_text = " ".join(texts).strip()
                    # Remove trailing 'Dotdash Meredith' or similar credits
                    step_text = (
                        step_text.replace("Dotdash Meredith Food Studios", "")
                        .replace("DOTDASH MEREDITH FOOD STUDIOS", "")
                        .strip()
                    )
                    # Remove any remaining HTML tags
                    from bs4 import BeautifulSoup as BS

                    step_text = BS(step_text, "html.parser").get_text(
                        separator=" ", strip=True
                    )
                    if step_text:
                        steps.append(step_text)
        if steps:
            # Group steps into 3 logical steps if more than 3 exist
            if len(steps) > 3:
                n = len(steps) // 3
                grouped = [
                    " ".join(steps[:n]),
                    " ".join(steps[n : 2 * n]),
                    " ".join(steps[2 * n :]),
                ]
                steps = [s.strip() for s in grouped if s.strip()]
        if not steps:
            # fallback for older markup
            for step in soup.select("[data-instruction-step]"):
                txt = step.get_text(strip=True)
                if txt:
                    steps.append(txt)
            if not steps:
                for li in soup.select("li.instruction"):
                    txt = li.get_text(strip=True)
                    if txt:
                        steps.append(txt)

        # Times and servings
        details = {}
        # Use the modern Allrecipes class for details
        details_section = soup.select_one("div.mm-recipes-details__content")
        if details_section:
            labels = details_section.select(".mm-recipes-details__label")
            values = details_section.select(".mm-recipes-details__value")
            for label, value in zip(labels, values):
                label_text = label.get_text(strip=True)
                value_text = value.get_text(strip=True)
                if "Prep" in label_text and "Time" in label_text:
                    details["prep_time"] = value_text
                elif "Cook" in label_text and "Time" in label_text:
                    details["cook_time"] = value_text
                elif "Additional" in label_text and "Time" in label_text:
                    details["additional_time"] = value_text
                elif "Total" in label_text and "Time" in label_text:
                    details["total_time"] = value_text
                elif "Servings" in label_text:
                    details["servings"] = value_text
                elif "Yield" in label_text:
                    details["yield"] = value_text
        # Fallback to old method if not found
        if (
            "prep_time" not in details
            or "cook_time" not in details
            or "total_time" not in details
        ):

            def get_time(label):
                for div in soup.find_all("div"):
                    if div.get_text(strip=True) == label:
                        next_div = div.find_next("div")
                        if next_div:
                            return next_div.get_text(strip=True)
                return None

            if "prep_time" not in details:
                details["prep_time"] = get_time("Prep Time:")
            if "cook_time" not in details:
                details["cook_time"] = get_time("Cook Time:")
            if "additional_time" not in details:
                details["additional_time"] = get_time("Additional Time:")
            if "total_time" not in details:
                details["total_time"] = get_time("Total Time:")
            if "servings" not in details:
                details["servings"] = get_time("Servings:")
            if "yield" not in details:
                details["yield"] = get_time("Yield:")

        result = {
            "title": title,
            "url": url,
            "ingredients": ingredients,
            "steps": steps,
            "details": {
                "prep_time": details.get("prep_time"),
                "cook_time": details.get("cook_time"),
                "additional_time": details.get("additional_time"),
                "total_time": details.get("total_time"),
                "servings": details.get("servings"),
                "yield": details.get("yield"),
            },
        }
        return result
    except Exception as e:
        raise RecipeScraperError(f"Error parsing recipe page: {e}")
