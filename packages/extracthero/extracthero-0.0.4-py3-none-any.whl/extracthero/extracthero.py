# extracthero.py
# run with: python -m extracthero.extracthero

from __future__ import annotations

from time import time
from typing import List, Union, Optional

from extracthero.myllmservice import MyLLMService
from extracthero.schemes import (
    ExtractConfig,
    ExtractOp,
    FilterOp,
    ParseOp,
    ItemToExtract,
)
from extracthero.filterhero import FilterHero


class ExtractHero:
    """High-level orchestrator that chains FilterHero → LLM parse phase."""

    def __init__(self, config: ExtractConfig | None = None, llm: MyLLMService | None = None):
        self.config = config or ExtractConfig()
        self.llm = llm or MyLLMService()
        self.filter_hero = FilterHero(self.config, self.llm)

    # ────────────────────────── parse phase ──────────────────────────
    def _parser(
        self,
        corpus: str,
        items: ItemToExtract | List[ItemToExtract],
    ) -> ParseOp:
        start_ts = time()
        prompt = (
            items.compile()
            if isinstance(items, ItemToExtract)
            else "\n\n".join(it.compile() for it in items)
        )
        gen = self.llm.parse_via_llm(corpus, prompt)
        return ParseOp.from_result(
            config=self.config,
            content=gen.content if gen.success else None,
            usage=gen.usage,
            start_time=start_ts,
            success=gen.success,
            error=None if gen.success else "LLM parse failed",
        )

    # ─────────────────────────── public API ──────────────────────────
    def extract(
        self,
        text: str | dict,
        items: ItemToExtract | List[ItemToExtract],
        text_type: Optional[str] = None,
        reduce_html: bool = True,
        enforce_llm_based_filter: bool = False,
        filter_separately: bool = False,
    ) -> ExtractOp:
        """
        End-to-end extraction pipeline.

        Parameters
        ----------
        text : raw HTML / JSON string / dict / plain text
        items: one or many ItemToExtract
        text_type : "html" | "json" | "dict" | None
        reduce_html : strip HTML to visible text (default True)
        enforce_llm_based_filter : force JSON/dict inputs through LLM
        filter_separately : one LLM call per item (default False)
        """
        # Phase-1: filtering
        filter_op: FilterOp = self.filter_hero.run(
            text,
            items,
            text_type=text_type,
            filter_separately=filter_separately,
            reduce_html=reduce_html,
            enforce_llm_based_filter=enforce_llm_based_filter,
        )

        if not filter_op.success:
            # short-circuit parse phase
            parse_op = ParseOp.from_result(
                config=self.config,
                content=None,
                usage=None,
                start_time=time(),
                success=False,
                error="Filter phase failed",
            )
            return ExtractOp(filter_op=filter_op, parse_op=parse_op, content=None)

        # Phase-2: parsing
        parse_op = self._parser(filter_op.content, items)
        return ExtractOp(
            filter_op=filter_op,
            parse_op=parse_op,
            content=parse_op.content,
        )


# ─────────────────────────── simple demo ───────────────────────────
def main() -> None:
    extractor = ExtractHero()

    # define what to extract
    items = [
        ItemToExtract(
            name="title",
            desc="Product title",
            example="Wireless Keyboard",
        ),
        ItemToExtract(
            name="price",
            desc="Product price with currency symbol",
            regex_validator=r"€\d+\.\d{2}",
            example="€49.99",
        ),
    ]

    sample_html = """
    <html><body>
      <div class="product">
        <h2 class="title">Wireless Keyboard</h2>
        <span class="price">€49.99</span>
      </div>
      <div class="product">
        <h2 class="title">USB-C Hub</h2>
        <span class="price">€29.50</span>
      </div>
    </body></html>
    """
    
    op = extractor.extract(sample_html, items, text_type="html")
    print("Filtered corpus:\n", op.filter_op.content)
    print("Parsed result:\n", op.parse_op.content)


if __name__ == "__main__":
    main()
