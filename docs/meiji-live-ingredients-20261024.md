# Meiji online ingredient retrieval

Added bounded on-demand official-source retrieval for Meiji ice cream and yogurt using observed JAN-specific product URL patterns. When the protected catalogue lacks an ingredient declaration, the endpoint fetches the two official categories with a 2.8 second per-request timeout. It requires an exact matching og:url, a product heading, a unique labelled 原材料名 table cell, and a nutrition section. Scripts and general allergen dictionaries are excluded; maintenance, redirects and conflicting labels are rejected. No certification or flavor carrier origin is inferred.

Verified the current official Meiji Super Vanilla 200ml page for JAN 4902705125308 on 2026-10-24. Its declaration includes 香料 and does not list pork, gelatin or emulsifier. This establishes the public ingredient declaration, not alcohol content or halal certification. The parser was checked against the fetched official HTML; all 126 existing and new tests passed. robots.txt allows the requested product paths. Source text is returned per product with attribution; this change does not bulk republish the manufacturer catalogue or claim reuse permission.

Sources: https://www.meiji.co.jp/products/icecream/4902705125308.html ; https://www.meiji.co.jp/products/yogurt/4902705133099.html ; https://www.meiji.co.jp/robots.txt

This is a Meiji category integration, not unrestricted web search across every Japanese food. The scanner and decision rules are unchanged.
