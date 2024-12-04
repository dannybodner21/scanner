from xml.dom import VALIDATION_ERR
from django.core.exceptions import ValidationError

from django.test import TestCase
from .models import Recipe

class RecipeTest(TestCase):
    def setUp(self):
        self.recipe = Recipe(
            title = "Breakfast Cereal",
            ingredients = """8,oz,milk
1,cup,Lucky Charms""",
            instructions = """pour milk
warm it up if needed
pour cereal in""",
            prepMinutes = 5,
            cookMinutes = 1,
            servings = 1
        )

    def test_recipe_creation(self):
        """Test that a Recipe instance is created correctly"""
        self.assertEqual(self.recipe.title, "Breakfast Cereal")
        self.assertEqual(self.recipe.ingredients, """8,oz,milk
1,cup,Lucky Charms""")
        self.assertEqual(self.recipe.instructions, """pour milk
warm it up if needed
pour cereal in""")
        self.assertEqual(self.recipe.prepMinutes, 5)
        self.assertEqual(self.recipe.cookMinutes, 1)
        self.assertEqual(self.recipe.servings, 1)


    def test_clean_line(self):
        self.assertEqual(self.recipe.clean_line("a,b,c"), "a b c")

    def test_formattedIngredients(self):
        self.assertEqual(self.recipe.getIngredients(),
                         "<ul><li>8 oz milk</li><li>1 cup Lucky Charms</li></ul>")

    def test_formattedInstructions(self):
        self.assertEqual(self.recipe.getInstructions(),
                         "<ol><li>pour milk</li><li>warm it up if needed</li><li>pour cereal in</li></ol>")

    def test_convert_mins_to_hhmm(self):
        self.assertEqual(self.recipe.convert_mins_to_hhmm(90), "1:30")
        self.assertNotEquals(self.recipe.convert_mins_to_hhmm(65), "1:5")

    def test_combine_times(self):
        self.assertEqual(self.recipe.combine_times(), "0:06")
        self.assertNotEquals(self.recipe.combine_times(), "0:6")

    def test_no_title(self):
        with self.assertRaises(ValidationError):
            recipe = Recipe(
                ingredients = "1,,food",
                instructions = "cook",
                prepMinutes = 60,
                cookMinutes = 30,
                servings = 2
            )
            recipe.full_clean()

    def test_no_ingredients(self):
        with self.assertRaises(ValidationError):
            recipe = Recipe(
                title = "my recipe",
                instructions = "cook",
                prepMinutes = 60,
                cookMinutes = 30,
                servings = 2
            )
            recipe.full_clean()

    def test_no_instructions(self):
        with self.assertRaises(ValidationError):
            recipe = Recipe(
                title = "my recipe",
                ingredients = "1,,food",
                prepMinutes = 60,
                cookMinutes = 30,
                servings = 2
            )
            recipe.full_clean()

    def test_no_prepMinutes(self):
        with self.assertRaises(ValidationError):
            recipe = Recipe(
                title = "my recipe",
                ingredients = "1,,food",
                instructions = "cook",
                cookMinutes = 30,
                servings = 2
            )
            recipe.full_clean()

    def test_no_cookMinutes(self):
        with self.assertRaises(ValidationError):
            recipe = Recipe(
                title = "my recipe",
                ingredients = "1,,food",
                instructions = "cook",
                prepMinutes = 60,
                servings = 2
            )
            recipe.full_clean()

    def test_no_servings(self):
        with self.assertRaises(ValidationError):
            recipe = Recipe(
                title = "my recipe",
                ingredients = "1,,food",
                instructions = "cook",
                prepMinutes = 60,
                cookMinutes = 30
            )
            recipe.full_clean()

