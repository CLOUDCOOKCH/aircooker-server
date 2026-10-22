# Synthetic recipe images

`recipe-photo-en.png` and `recipe-photo-de.png` are project-generated test fixtures,
not user photos or third-party recipe screenshots. Pillow draws invented recipe text
in DejaVu Sans on a 1050×1000 white RGB canvas. Their PNG metadata identifies them as
synthetic. The fixture content is Apache-2.0 project material; DejaVu's rendered glyphs
are not a redistributed font file. No household content or personal metadata is present.

English: Lemon rice; Servings: 4; Ingredients: 200 g rice, 1 onion,
2 tablespoons olive oil. Instructions: Chop the onion. Cook the rice with the onion.
Stir in the olive oil.

German: Tomatenreis; Portionen: 2; Zutaten: 200 g Reis, 2 Tomaten,
1 Essloeffel Olivenoel. Zubereitung: Tomaten schneiden. Reis mit den Tomaten kochen.

Tests run the real local Tesseract engine with both `eng` and `deu` models. These clean,
straight text fixtures prove the pipeline, not arbitrary camera/handwriting accuracy.
