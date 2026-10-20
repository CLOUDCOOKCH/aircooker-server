CREATE TABLE recipe (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, servings TEXT NOT NULL, rating INTEGER,
 deleted INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE recipe_ingredient (
 recipe_id TEXT NOT NULL REFERENCES recipe(id), id TEXT NOT NULL, position INTEGER NOT NULL,
 name TEXT NOT NULL, quantity TEXT, quantity_max TEXT, unit TEXT NOT NULL,
 preparation TEXT NOT NULL, original_text TEXT NOT NULL,
 PRIMARY KEY(recipe_id,id), UNIQUE(recipe_id,position)
);
CREATE INDEX ingredient_name ON recipe_ingredient(name);
CREATE TABLE recipe_step (
 recipe_id TEXT NOT NULL REFERENCES recipe(id), position INTEGER NOT NULL,
 instruction TEXT NOT NULL, PRIMARY KEY(recipe_id,position)
);
CREATE TABLE leftover (
 id TEXT PRIMARY KEY, recipe_id TEXT NOT NULL REFERENCES recipe(id),
 portions TEXT NOT NULL, produced_on TEXT NOT NULL, discarded INTEGER NOT NULL,
 deleted INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE meal_plan_entry (
 id TEXT PRIMARY KEY, recipe_id TEXT NOT NULL REFERENCES recipe(id),
 planned_date TEXT NOT NULL, category TEXT NOT NULL CHECK(category IN ('breakfast','lunch','dinner')),
 servings TEXT NOT NULL, leftover_id TEXT REFERENCES leftover(id),
 deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX meal_date ON meal_plan_entry(planned_date,category);
CREATE TABLE pantry_item (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, available INTEGER NOT NULL,
 include_this_week INTEGER NOT NULL, deleted INTEGER NOT NULL DEFAULT 0
);
