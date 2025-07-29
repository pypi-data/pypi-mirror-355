# extracthero

Extract **accurate, structured facts** from messy real-world content — raw HTML, screenshots, PDFs, JSON blobs or plain text — with *almost zero compromise.*

---

## Why extracthero?

| Pain-point                                                       | extracthero’s answer                                                                                                                                                                                        |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| *DOM spaghetti* (ads, nav bars, JS widgets) pollutes extraction. | **DomReducer** reduces the most-common HTML tags into a compact, linear corpus, stripping layout noise and script cruft while keeping the text you care about.                                              |
| HTML→Markdown conversions drop dynamic/JS-rendered elements.     | DomReducer’s tag-level reduction keeps content that markdown pass-throughs often lose.                                                                                                                      |
| LLM prompts that just say “extract price” are brittle.           | Extracthero asks you to fill an **`ItemToExtract`** dataclass that includes the field’s `name`, `desc`, and optional `text_rules`, so the LLM knows the full context and returns *sniper-accurate* results. |
| One-shot LLM calls are hard to debug and expensive.              | Two-phase pipeline: **FilterHero** isolates the minimal fragment; **ParseHero** turns it into JSON. Fail fast and retry only the phase that broke.                                                          |
| Post-hoc validation is messy.                                    | Regex/type guards live inside each `ItemToExtract`; a failed field flips `success=False`, so you can retry or send to manual review.                                                                        |

---

## Key ideas

### 1  Schema-first extraction

```python
from extracthero import ItemToExtract

price = ItemToExtract(
    name="price",
    desc="currency-prefixed current product price",
    regex_validator=r"€\d+\.\d{2}",
    text_rules=[
        "Ignore crossed-out promotional prices.",
        "Return the live price only."
    ],
    example="€49.99"
)
```

### 2  DomReducer > HTML→Markdown

* Works directly on the DOM tree.
* Removes scripts, ads, banners; keeps relevant tags.
* Shrinks a 40 kB e-commerce page to <3 kB of clean, LLM-ready text.

### 3  Two-phase pipeline

```
Raw input  ──▶  FilterHero  (shrinks & isolates)  ──▶  ParseHero  (JSON) ──▶  dict + metrics
```

---

## Features

* **Multi-modal input** – raw HTML, JSON, Python dicts, screenshots (vision LLM in roadmap).
* **Spatial context** – layout coordinates stored so an LLM “sees” element proximity.
* **LLM-agnostic** – default wrapper targets OpenAI; swap in any `.filter_via_llm` / `.parse_via_llm` service.
* **Per-field validation** – regex, required/optional, custom lambdas.
* **Usage metering** – token counts & cost returned with every operation.
* **Opt-in strictness** – force LLM even for dicts (`enforce_llm_based_*`) or skip HTML reduction (`reduce_html=False`).

---

## Installation

```bash
pip install extracthero
```

---

## Quick-start

```python
from extracthero import Extractor, ItemToExtract

html = open("product-page.html").read()

fields = [
    ItemToExtract(name="title", desc="product title", example="Wireless Keyboard"),
    ItemToExtract(
        name="price",
        desc="currency-prefixed price",
        regex_validator=r"€\d+\.\d{2}",
        example="€49.99"
    ),
]

hero   = Extractor()
result = hero.extract(html, fields, text_type="html")

print("✅ success:", result.success)
print(result.parse_op.content)
```

---

## Typical HTML workflow

1. **Scrape or load** the raw HTML.
2. **DomReducer** trims it to a minimal fragment but keeps required tags.
3. **FilterHero** sees only that reduced text, calling the LLM once (or per-field) to keep the lines that mention title, price, SKU, etc.
4. **ParseHero** builds a schema-driven prompt and emits strict JSON.
5. **Regex guard** – invalid prices (`"129.50"`) are rejected for lacking “€”.
6. **ExtractOp** bundles both steps plus token/cost metrics for budgeting.

---

## Roadmap

| Status | Feature                                          |
| ------ | ------------------------------------------------ |
| ✅      | Sync FilterHero & ParseHero                      |
| 🟡     | Async heroes for high-throughput pipelines       |
| 🟡     | Built-in key\:value fallback parser              |
| 🟡     | Vision-LLM screenshot mode                       |
| 🟡     | Pydantic schema-driven auto-prompts & auto-regex |

---


