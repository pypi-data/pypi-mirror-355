import requests
from bs4 import BeautifulSoup
import re


class SearchRecipesError(Exception):
    """Custom exception for search errors."""

    pass


def __verify_search_results(results: list):
    final_results = []
    for recipe in results:
        if __verify_search_url(recipe["url"]):
            final_results.append(recipe)
    if final_results:
        return final_results
    else:
        raise SearchRecipesError("No results found. (Only recipes)")


def __get_search_url(query: str) -> str:
    """Constructs the search URL for Allrecipes."""
    return f"https://www.allrecipes.com/search?q={query}"


def __verify_search_url(url: str) -> bool:
    """Verifies if the search URL is valid."""
    return url.startswith("https://www.allrecipes.com/recipe/")


def search_recipes(query: str) -> list:
    """Searches for recipes on Allrecipes and returns a list of recipe titles, URLs, and ratings (if available).
    Raises SearchRecipesError on network or parsing errors.
    """
    url = __get_search_url(query)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        if "404" in str(e):
            raise SearchRecipesError("No results found for the given query.")
        else:
            raise SearchRecipesError(f"Network error while searching recipes: {e}")
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        recipe_elements = soup.find_all(
            "a",
            class_="comp mntl-card-list-card--extendable mntl-universal-card mntl-document-card mntl-card card card--no-image",
        )
        recipes = []
        for element in recipe_elements:
            text = element.get_text(strip=True)
            element_str = str(element)
            href_match = re.search(r'href=["\'](.*?)["\']', element_str)
            link = href_match.group(1) if href_match else None
            if "Ratings" in text:
                parts = text.rsplit("Ratings", 1)
                title = parts[0].strip()
                ratings = None
                match = re.search(r"(\d+[\,\d]*)$", title)
                if match:
                    ratings = int(match.group(1).replace(",", ""))
                    title = title[: match.start()].strip()
            else:
                title = text
                ratings = None
            recipe = {"title": title, "url": link}
            if ratings is not None:
                recipe["ratings"] = ratings
            recipes.append(recipe)
        # Verify search results
        try:
            recipes = __verify_search_results(recipes)
        except SearchRecipesError as e:
            raise SearchRecipesError(f"Search failed: {e}")
        return recipes
    except Exception as e:
        raise SearchRecipesError(f"Error parsing search results: {e}")
