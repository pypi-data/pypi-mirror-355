# py_allrecipes.search_recipes

Search for recipes on Allrecipes.com by keyword.

**Example:**

```python
import py_allrecipes
results = py_allrecipes.search_recipes('chocolate cake')
for recipe in results:
    print(recipe['title'], recipe['url'], recipe.get('ratings'))
```

**Returns:**
- List of dicts: `{ 'title': str, 'url': str, 'ratings': int|None }`

---

# py_allrecipes.get_recipe

Fetch and parse a recipe page from Allrecipes.com.

**Example:**

```python
import py_allrecipes
url = py_allrecipes.search_recipes('chocolate cake')[0]['url']
recipe = py_allrecipes.get_recipe(url)
print(recipe['title'])
print(recipe['ingredients'])
print(recipe['steps'])
print(recipe['details'])
```

**Returns:**
- Dict with keys:
  - `title`: str
  - `url`: str
  - `ingredients`: list of str
  - `steps`: list of str (grouped into logical steps)
  - `details`: dict with prep_time, cook_time, additional_time, total_time, servings, yield

---

# Usage Notes
- `search_recipes` scrapes Allrecipes search results for recipe links and titles.
- `get_recipe` scrapes a recipe page for all structured data (ingredients, steps, times, servings, yield).
- Both functions are robust to changes in Allrecipes layout, with fallbacks for older markup.
