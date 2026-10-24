# Missing ingredients: Calbee Pizza Potato / automatic source research

Reported JAN: 4901330581985. The previous worldwide/community record identified the product but had no ingredient text, so the engine displayed UNKNOWN. The missing ingredient evidence was a coverage gap, not a HALAL finding.

An exact-JAN reviewed evidence record now precedes empty catalogue metadata. Calbee’s indexed official Pizza Potato page explicitly declares サラミ風チップ（豚肉を含む）. The official page covers the 64g variant; Sugoi Mart’s product variant data separately identifies JAN 4901330581985. The displayed ingredient text is explicitly a prohibited-ingredient excerpt, not a fabricated full formula. No alcohol assumption is included. The live Calbee page returned its maintenance notice during this review; the record discloses that the ingredient evidence comes from the reviewed indexed official declaration.

Sources:
- https://www.calbee.co.jp/products/detail/?p=20210513141859
- https://www.sugoimart.com/products/pizza-potato

The protected catalogue endpoint also now follows a private exact-JAN TOPVALU discovery lead to the current public official product page when no ingredient-bearing record is available. It reads only explicitly labelled 原材料名 and 添加物; on-page JAN, product heading and food nutrition are required. Conflicting ingredient declarations, unsupported page layouts, maintenance, redirects and unavailable sources return no new verdict. Unrelated allergen dictionaries, scripts and marketing text cannot become an ingredient declaration. Only a current successful official extraction sets the ingredient-declaration-reviewed flag; it never sets halal certification.

This is a bounded source integration for TOPVALU, not universal web-search/AI grounding across all manufacturers. Existing licensed OFF data remains separately attributed. Private source records are used only as URL discovery leads, not exported as a bulk ingredient database. No anonymous table policy or credential permission changed.

Validation: 123 tests (including prior regressions and new exact-source/parser checks); production build passed. Live backend checks for 4549414000160 and 4549414087208 returned exact-JAN ingredients from TOPVALU’s official pages. Backup is recoverable from the previous main commit. Scanner camera code is unchanged.
