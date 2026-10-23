# Recipe ingredients and pantry

The recipe editor offers common units and optional ingredient-name suggestions from your
household's locally stored pantry and other recipes. This is a PWA extension; the native
app, API, database format and Bring! ownership identities are unchanged.

## Names and suggestions

Open or import a recipe, choose Edit, then Ingredients. Type a name to see up to six
matching household names, labelled Pantry or Recipes. Matches can include catalogue
aliases, English/German names and small spelling mistakes: `zwibel` can suggest an
existing `Zwiebeln` entry. A catalogue alias helps find a household name; it does not add
catalogue foods to your household.

Select a result by clicking or tapping it, or use Up/Down and Enter. Escape dismisses
the suggestions. Selection changes only that ingredient's name. Imported original text,
preparation and quantity remain available in the editor. Existing recipes and pantry
entries are never silently renamed or merged, and suggestions do not change Bring!
items or its ownership ledger.

You can always type a new name, such as `Dragon fruit`, and save it in the recipe.
This does not create a pantry entry. Suggestions are local, work offline with downloaded
household records and do not call an AI provider or external search service. An empty
local pantry/library simply leaves you free to type.

## Units and saving

The Unit menu includes no unit, g/kg/mg, ml/cl/dl/l, teaspoon, tablespoon, piece, cup,
pinch, clove, slice, can, pack and bunch. Labels follow the English/German interface;
the stored unit values stay stable, for example `tsp`, `tbsp` and `piece`.
Choosing a unit changes its identity without changing the entered quantity. There is
no guessed conversion between weight and volume or between ingredients.

Choose Other unit… / Andere Einheit… to enter your own unit. Unknown imported units,
such as `Handvoll`, stay in that custom field until you explicitly change them. Choosing
the custom option alone does not discard the previous value. A custom unit can also
be edited later.

The existing local draft protects unfinished editing, but you must choose Save /
Speichern to save the recipe. Offline saves use the existing durable outgoing queue
and synchronise when connected. Selecting a suggestion alone does not save a recipe.

## Compact pantry

Open Shopping → Pantry to manage existing pantry records or Choose pantry basics.
Rows align availability, ingredient name, this-week shopping inclusion and removal on
desktop. Normal desktop rows are 56px; ordinary phone rows are about 92px, with label
actions at least 44px high. Long household names can wrap and make a row taller.

Food emojis accompany names in the pantry and basics picker, as requested. Unknown
foods receive a generic bowl (🥣). These are decorative, hidden from assistive technology
and always paired with the ingredient text. They do not indicate stock or create records.
Existing availability and civil-week shopping inclusion controls retain their behavior.

## Evidence and availability

The [bounded review](validation/ingredient-picker-review.md) records a ship verdict with
zero material findings, representative genuine captures and attributed local validation.
This source is currently unpublished; `poc-20261023.4` is the candidate and `.3` remains
the latest published preview. CI and publication evidence are pending. Local Chromium
automation uses synthetic household and provider data; live AI/Bring!, physical iPhone
and Safari acceptance remain unverified.
