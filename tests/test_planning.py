from datetime import date
from decimal import Decimal
from uuid import uuid4

from aircooker.models import Ingredient, Meal, Recipe, Recurrence
from aircooker.planning import occurrences, scaled, week_start


def test_range_and_non_numeric_scaling():
    recipe = Recipe(
        title="Bread",
        servings=2,
        ingredients=[
            Ingredient(id=uuid4(), name="Flour", quantity="100", quantity_max="200", unit="g"),
            Ingredient(id=uuid4(), name="Salt", original_text="to taste"),
        ],
    )
    items = scaled(recipe, Decimal(3))
    assert items[0].quantity == 150 and items[0].quantity_max == 300
    assert items[1].quantity is None and items[1].original_text == "to taste"


def test_week_and_bounded_recurrence():
    assert week_start(date(2026, 10, 25)) == date(2026, 10, 19)
    meal = Meal(
        recipe_id=uuid4(),
        date=date(2026, 10, 19),
        category="dinner",
        recurrence=Recurrence(until=date(2027, 1, 1), exceptions=[date(2026, 10, 26)]),
    )
    assert occurrences(meal, date(2026, 10, 19), date(2026, 11, 2)) == [
        date(2026, 10, 19),
        date(2026, 11, 2),
    ]
