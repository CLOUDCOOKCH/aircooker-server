# Normalised, indexed domain projections share the sync transaction. JSON entity
# snapshots preserve exact wire values and serve the versioned change stream.
def project(db, kind, eid, payload, deleted):
    table = {
        "recipe": "recipe",
        "meal": "meal_plan_entry",
        "pantry": "pantry_item",
        "leftover": "leftover",
    }.get(kind)
    if deleted:
        if table:
            db.execute(f"UPDATE {table} SET deleted=1 WHERE id=?", (eid,))
        return
    if kind == "recipe":
        db.execute(
            "INSERT INTO recipe VALUES (?,?,?,?,0) ON CONFLICT(id) DO UPDATE SET title=excluded.title,servings=excluded.servings,rating=excluded.rating,deleted=0",
            (eid, payload["title"], payload["servings"], payload["rating"]),
        )
        db.execute("DELETE FROM recipe_ingredient WHERE recipe_id=?", (eid,))
        db.execute("DELETE FROM recipe_step WHERE recipe_id=?", (eid,))
        for position, item in enumerate(payload["ingredients"]):
            db.execute(
                "INSERT INTO recipe_ingredient VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    eid,
                    item["id"],
                    position,
                    item["name"],
                    item["quantity"],
                    item["quantity_max"],
                    item["unit"],
                    item["preparation"],
                    item["original_text"],
                ),
            )
        for position, text in enumerate(payload["steps"]):
            db.execute("INSERT INTO recipe_step VALUES (?,?,?)", (eid, position, text))
    elif kind == "leftover":
        db.execute(
            "INSERT INTO leftover VALUES (?,?,?,?,?,0) ON CONFLICT(id) DO UPDATE SET recipe_id=excluded.recipe_id,portions=excluded.portions,produced_on=excluded.produced_on,discarded=excluded.discarded,deleted=0",
            (
                eid,
                payload["recipe_id"],
                payload["portions"],
                payload["produced_on"],
                payload["discarded"],
            ),
        )
    elif kind == "meal":
        db.execute(
            "INSERT INTO meal_plan_entry VALUES (?,?,?,?,?,?,0) ON CONFLICT(id) DO UPDATE SET recipe_id=excluded.recipe_id,planned_date=excluded.planned_date,category=excluded.category,servings=excluded.servings,leftover_id=excluded.leftover_id,deleted=0",
            (
                eid,
                payload["recipe_id"],
                payload["date"],
                payload["category"],
                payload["servings"],
                payload["leftover_id"],
            ),
        )
    elif kind == "pantry":
        db.execute(
            "INSERT INTO pantry_item VALUES (?,?,?,?,0) ON CONFLICT(id) DO UPDATE SET name=excluded.name,available=excluded.available,include_this_week=excluded.include_this_week,deleted=0",
            (eid, payload["name"], payload["available"], payload["include_this_week"]),
        )
