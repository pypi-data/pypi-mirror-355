# Py Allrecipes

Py Allrecipes is a Python package for searching and extracting structured recipe data from Allrecipes.com.

- Search for recipes by keyword
- Extract ingredients, steps, times, servings, and yield from any recipe page
- Output is robust and structured for easy use in your own projects

## Features
- `search_recipes(query)`: Search Allrecipes and get a list of recipe titles, URLs, and ratings
- `get_recipe(url)`: Fetch and parse a recipe page for all details (ingredients, steps, times, servings, yield)

## Quickstart
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

## Documentation
See the [full documentation](https://zacharyj12.github.io/py-allrecipes/) for more details and usage examples.

## License
MIT