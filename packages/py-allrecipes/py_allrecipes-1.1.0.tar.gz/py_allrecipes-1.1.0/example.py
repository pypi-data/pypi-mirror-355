import py_allrecipes

search = input("Enter a search term: ")
url = py_allrecipes.search_recipes(search)[0]["url"]
recipe = py_allrecipes.get_recipe(url)

print(recipe)
