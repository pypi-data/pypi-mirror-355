# Welcome to Py Allrecipes documentation

Py Allrecipes is a Python package for searching and extracting recipes from Allrecipes.com.

## What can you do?
- **Search recipes** by keyword and get structured results (title, url, ratings)
- **Extract full recipe details**: ingredients, steps (grouped logically), prep/cook/total time, servings, and yield

## Example Usage
```python
import py_allrecipes
results = py_allrecipes.search_recipes('chocolate cake')
url = results[0]['url']
recipe = py_allrecipes.get_recipe(url)
print(recipe['title'])
print(recipe['ingredients'])
print(recipe['steps'])
print(recipe['details'])
```

## More Information
- See the [Search & Recipe API](search.md) for full API documentation and usage notes.
- Robust to changes in Allrecipes layout, with fallbacks for older markup.



