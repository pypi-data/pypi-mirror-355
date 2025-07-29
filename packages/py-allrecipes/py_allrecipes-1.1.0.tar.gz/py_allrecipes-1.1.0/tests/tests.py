import unittest
from unittest.mock import patch, Mock
import py_allrecipes


class TestPyAllrecipes(unittest.TestCase):
    @patch("py_allrecipes.search.requests.get")
    def test_search_recipes(self, mock_get):
        # Mock HTML response for search
        html = """<html><body>
        <a class="comp mntl-card-list-card--extendable mntl-universal-card mntl-document-card mntl-card card card--no-image" href="https://www.allrecipes.com/recipe/12345/test-cake/">Test Cake 123Ratings</a>
        </body></html>"""
        mock_get.return_value = Mock(status_code=200, text=html)
        results = py_allrecipes.search_recipes("test")
        self.assertIsInstance(results, list)
        self.assertEqual(results[0]["title"], "Test Cake")
        self.assertEqual(
            results[0]["url"], "https://www.allrecipes.com/recipe/12345/test-cake/"
        )
        self.assertEqual(results[0]["ratings"], 123)

    @patch("py_allrecipes.recipe.requests.get")
    def test_get_recipe(self, mock_get):
        # Mock HTML response for recipe
        html = """<html><body>
        <h1>Test Cake</h1>
        <ul><li class="mm-recipes-structured-ingredients__list-item">1 cup sugar</li></ul>
        <ol class="comp mntl-sc-block mntl-sc-block-startgroup mntl-sc-block-group--OL">
            <li class="comp mntl-sc-block mntl-sc-block-startgroup mntl-sc-block-group--LI"><span>Step 1</span>Mix ingredients.</li>
            <li class="comp mntl-sc-block mntl-sc-block-startgroup mntl-sc-block-group--LI"><span>Step 2</span>Bake.</li>
            <li class="comp mntl-sc-block mntl-sc-block-startgroup mntl-sc-block-group--LI"><span>Step 3</span>Eat.</li>
        </ol>
        <div class="mm-recipes-details__content">
            <div class="mm-recipes-details__label">Prep Time</div><div class="mm-recipes-details__value">10 mins</div>
            <div class="mm-recipes-details__label">Cook Time</div><div class="mm-recipes-details__value">20 mins</div>
            <div class="mm-recipes-details__label">Total Time</div><div class="mm-recipes-details__value">30 mins</div>
            <div class="mm-recipes-details__label">Servings</div><div class="mm-recipes-details__value">8</div>
            <div class="mm-recipes-details__label">Yield</div><div class="mm-recipes-details__value">1 cake</div>
        </div>
        </body></html>"""
        mock_get.return_value = Mock(status_code=200, text=html)
        url = "https://www.allrecipes.com/recipe/12345/test-cake/"
        recipe = py_allrecipes.get_recipe(url)
        self.assertEqual(recipe["title"], "Test Cake")
        self.assertIn("1 cup sugar", recipe["ingredients"])
        self.assertEqual(len(recipe["steps"]), 3)
        self.assertIn("Mix ingredients.", recipe["steps"][0])
        self.assertEqual(recipe["details"]["prep_time"], "10 mins")
        self.assertEqual(recipe["details"]["cook_time"], "20 mins")
        self.assertEqual(recipe["details"]["total_time"], "30 mins")
        self.assertEqual(recipe["details"]["servings"], "8")
        self.assertEqual(recipe["details"]["yield"], "1 cake")


if __name__ == "__main__":
    unittest.main()
