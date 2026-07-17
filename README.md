# The "Sugar Trap": Market Gap Analysis

**Client:** Helix CPG Partners
**Analyst:** Jayden
**Data:** Open Food Facts

---

## A. Executive Summary

The European snack aisle is roughly ten to one against healthy snacking. Of 166,811 products,
70.7% are high-sugar and low-protein, while just 6.8% manage low sugar and high protein. Four
sweet categories (cakes, chocolate, biscuits, confectionery) take up 72% of the shelf between
them. Nuts, seeds and dried fruit together account for 2.0%.

The opening is in savoury snacks. Chips and crackers have already solved the sugar problem: 68%
of the category is low-sugar and fails on protein alone. Adding a few grams of protein to a
cracker is a far easier brief than stripping 35g of sugar out of a chocolate bar and keeping it
edible. The products already sitting in that quadrant are supermarket own-brand and small
regional producers, mostly breadsticks and crackers whose protein comes from wheat gluten by
accident rather than design. No global snack manufacturer appears in the top 15 brands.

One important caveat came out of stress-testing the recommendation against Nutri-Score. Savoury
means salt, and the blue-ocean savoury products carry 1.78g of it per 100g, scoring an A or B
only 9.2% of the time. So the brief for R&D has three numbers rather than two: **15g protein,
under 5g sugar, and under 1.0g salt.**

---

## B. Project Links

| | |
|---|---|
| **Notebook** | [Google Colab](https://colab.research.google.com/drive/1s7Rnh1Fs8mzUAKSj9haxdWUfMamm1-qX) · also in [`notebooks/`](notebooks/) |
| **Dashboard** | [sugar-trap-market-gap-jayden.streamlit.app](https://sugar-trap-market-gap-jayden.streamlit.app) |
| **Presentation** | PASTE_SLIDES_LINK |
| **PDF export** | [`exports/market_gap_analysis.pdf`](exports/) |

---

## C. Technical Explanation

### Data cleaning

The biggest decision in this project wasn't really about cleaning at all. It was about scope.

41% of snack rows had no sugar or protein value, which is a lot to throw away without asking
why. So before dropping anything I checked whether the missingness was random. It wasn't.
Nutrition coverage runs between 86% and 95% across every European market in the data. In the
United States it's 5.3%.

That's not a gradient, it's a cliff, and it changes what a `dropna()` actually does. Dropping
the nulls doesn't trim a global dataset evenly — it deletes the American market almost entirely
while leaving Europe intact. Worse, whatever survived from the US would be the 5% of products
where somebody chose to fill in a nutrition panel, which is not a random sample of anything.
The US looks like the biggest gap in the data, but that's an artefact of how Open Food Facts
collects information, not a market opportunity.

I scoped the analysis to eight European markets. The data is reliable there, and the EU is a
single regulatory and consumer market, so a recommendation actually means something. A blended
EU-plus-US "world" figure wouldn't be something R&D could build against.

I dropped the remaining nulls rather than imputing them. Filling a missing sugar value with a
category median would invent the exact number the entire recommendation rests on, and a product
whose sugar figure I made up can't be evidence of anything.

**Outliers turned out to be a non-problem.** Only 465 rows (0.27%) failed the plausibility
checks — nutrients between 0 and 100g, macros summing to no more than 100g, energy under 900
kcal/100g. Deduplicating on barcode removed exactly zero rows, which says something good about
how Open Food Facts is keyed.

The failures were interesting though. A lot of them had repeating decimals: Haribo Banana at
1283.33g sugar, Caramello Koala at 355.56g. That's the signature of OFF deriving its per-100g
figures by scaling a per-serving value against a serving size somebody entered wrong by an order
of magnitude. One product claimed 74,000g of sugar per 100g, which is a milligram/gram mix-up.
These are propagated calculation errors rather than typos.

**The removals that actually mattered were about what counts as a snack.** Two groups had
inherited an `en:snacks` tag through the crowd-sourced category tree without belonging there.

Dry baking mixes were the important one. Cake mix, muffin mix, brownie mix — 1,119 rows, all
measured as sold, which is to say as flour and powder. Nobody eats them in that state, and once
you add egg, milk and oil and bake the thing the numbers look completely different. What made
them dangerous is where they land: at the extremes of both axes. "CHIA SEED MUFFIN MIX" reads
4.3g sugar and 32.5g protein, which puts it squarely in the blue ocean this analysis exists to
find. Left in, they'd have corrupted the headline. Baby food (846 rows) is a smaller version of
the same problem — deliberately low-sugar, regulated differently, aimed at a consumer who isn't
the client's target.

Tags are matched as exact set membership rather than substrings. An earlier substring version
flagged Mott's Applesauce, because "sauces" is inside "applesauces".

The full audit trail runs 331,907 → 166,811. Half the rows are gone, but 97% of that loss comes
from the two scope decisions above, both of which are documented in the notebook.

### Candidate's Choice: stress-testing the recommendation

Story 4 says where the gap is. It doesn't say whether the gap is real, or whether the product I'm
recommending would survive contact with the outside world. So I ran two tests nobody asked for.
Both are in the notebook, including the one that didn't work.

**Test 1: is the blue ocean quietly owned by retailer own-brand?** The top brands are all
supermarkets — Carrefour, Auchan, Picard, Casino — which looked like a story. It isn't.
Private-label penetration is flat across all four quadrants, sitting between 12% and 16%
everywhere. Brand concentration is flat too: the top 10 brands hold 9.0% of the blue ocean and
8.4% of the sugar trap.

I've left the null result in rather than quietly deleting the cell. Open Food Facts is a product
census, not a sales panel — it records that a product exists and nothing about volume, shelf
space or revenue. A brand with 78 SKUs might own the category or might be invisible in it. Brand
concentration in this dataset can't answer a market-share question, and I should have worked
that out before running it rather than after.

**Test 2: would the product actually look healthy on the shelf?** This one paid off. I'm
recommending savoury snacks, savoury means salt, and Nutri-Score penalises salt heavily. If
high-protein crackers grade C or D, the client ships something that's nutritionally sound and
looks unhealthy on the front of the pack, which kills the whole premise of a healthy snacking
launch.

`nutriscore_grade` had been sitting in the dataset since ingestion, unused, with 93% coverage.
It's externally defined, independent of every threshold I picked, and it's computed over exactly
the products I'm recommending.

The good news first: it validates the quadrants. The sugar trap is 77.3% grade E, and the blue
ocean has the highest A+B share of any quadrant. An algorithm that knows nothing about my 10g/10g
cut-offs orders them the same way I did.

The bad news is that my own recommendation scores worst inside my own blue ocean. Savoury blue-
ocean products earn an A or B just 9.2% of the time, against 13.5% for the blue ocean overall
and 20.0% for Nuts & Seeds. The cause is salt: Chips & Savoury has the highest median salt of
any category at 1.40g/100g, ten times chocolate, and the blue-ocean subset is saltier still at
1.78g.

I did test whether protein and salt are coupled within that group, on the theory that the protein
arrives via cheese and cured meat. The correlation is weak (r = 0.105), so the mechanism isn't
established — the salt problem is real descriptively but I can't claim to know why. Either way
the constraint stands, and it's why the recommendation ended up with three numbers instead of
two.

None of this overturns the finding. Chips & Savoury still has 6,126 blue-ocean products against
1,650 for nuts, 17,370 products sitting one variable away from the target, and 25,541 products
of category scale. But without the check, the client could have hit both stated targets and
shipped a product graded D, competing on a health platform against confectionery that grades no
worse. That failure would have surfaced at the packaging stage, after the money was spent.

Three hypotheses tested across the project, three came back weaker than I expected, all reported
as found.
