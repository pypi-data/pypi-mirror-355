# filterhero.py

# run with: python -m extracthero.filterhero
"""
FilterHero — the “filter” phase of ExtractHero.
  • Normalises raw input (HTML / JSON / dict / plain text).
  • Optionally reduces HTML to visible text.
  • Fast-path key extraction for JSON/dict, unless `enforce_llm_based_filter=True`.
  • Otherwise builds LLM-prompts (combined or per-field) and returns a FilterOp.
"""

from __future__ import annotations

from time import time
from typing import Any, Dict, List, Optional, Tuple, Union

from llmservice import GenerationResult
from extracthero.myllmservice import MyLLMService
from extracthero.schemes import ExtractConfig, FilterOp, ItemToExtract, CorpusPayload
from domreducer import HtmlReducer
from string2dict import String2Dict
import json as _json  # used only when we need to stringify dicts for LLM


class FilterHero:
    # ─────────────────────────────── init ────────────────────────────────
    def __init__(
        self,
        config: Optional[ExtractConfig] = None,
        llm: Optional[MyLLMService] = None,
    ):
        self.config = config or ExtractConfig()
        self.llm = llm or MyLLMService()

    # ─────────────────────────────── public ──────────────────────────────
    def run(
        self,
        text: str | Dict[str, Any],
        items: ItemToExtract | List[ItemToExtract],
        text_type: Optional[str] = None,
        filter_separately: bool = False,
        reduce_html: bool = True,
        enforce_llm_based_filter: bool = False,
    ) -> FilterOp:
        """
        Parameters
        ----------
        text   : raw HTML / JSON string / dict / plain text
        items  : one or many ItemToExtract
        text_type : "html" | "json" | "dict" | None (auto=text)
        filter_separately : run one LLM call per item (True) or combined (False)
        reduce_html : when text_type="html", strip to visible text if True
        enforce_llm_based_filter : even for JSON/dict, stringify & send to LLM
        """
        start_ts = time()

        # 1. preprocess once
        pre = self._prepare_corpus(text, text_type, reduce_html)
        if pre.error:
            return self._wrap_filter_op(None, None, pre.reduced_html, False, pre.error, start_ts)

        # 2. JSON/dict fast-path (skip LLM) unless user forces LLM route
        if pre.corpus_type == "json" and not enforce_llm_based_filter:
            data: Dict[str, Any] = pre.corpus  # already a dict
            keys = [items.name] if isinstance(items, ItemToExtract) else [it.name for it in items]
            subset = {k: data.get(k) for k in keys}
            return self._wrap_filter_op(subset, None, None, True, None, start_ts)

        # 3. Build text for LLM (stringify dict if needed)
        if pre.corpus_type == "json":                     # && enforce=True
            corpus_for_llm: str = _json.dumps(pre.corpus, ensure_ascii=False, indent=2)
        else:
            corpus_for_llm: str = pre.corpus              # already str
        reduced_html = pre.reduced_html                  # may be None

        # 4. Dispatch LLM filter calls
        gen_results = self._dispatch_filter_requests(
            corpus=corpus_for_llm,
            items=items,
            separate=filter_separately,
        )

        # 5. Determine overall success
        ok = (
            gen_results[0].success
            if isinstance(items, ItemToExtract) or not filter_separately
            else all(r.success for r in gen_results)
        )

        # 6. Assemble content & usage
        content_final, usage_final = self._assemble_filter_results(gen_results, items, filter_separately)

        # 7. Wrap FilterOp
        return self._wrap_filter_op(
            content_final,
            usage_final,
            reduced_html,
            ok,
            None if ok else "LLM filter failed",
            start_ts,
        )

    # ──────────────────────────── helpers ──────────────────────────────
    def _prepare_corpus(
        self,
        text: str | Dict[str, Any],
        text_type: Optional[str],
        reduce_html: bool,
    ) -> CorpusPayload:
        if text_type == "html":
            if reduce_html:
                op = HtmlReducer(str(text)).reduce()

                print("reducement_details: ", op.reducement_details)

                return CorpusPayload(
                    corpus=op.reduced_data if op.success else str(text),
                    corpus_type="html",
                    reduced_html=op.reduced_data if op.success else None,
                )
            return CorpusPayload(corpus=str(text), corpus_type="html", reduced_html=None)

        if text_type == "json":
            parsed = String2Dict().run(str(text))
            if parsed is None:
                return CorpusPayload(corpus=None, corpus_type="json", reduced_html=None, error="Invalid JSON input")
            return CorpusPayload(corpus=parsed, corpus_type="json", reduced_html=None)

        if text_type == "dict":
            if not isinstance(text, dict):
                return CorpusPayload(corpus=None, corpus_type="json", reduced_html=None, error="dict type mismatch")
            return CorpusPayload(corpus=text, corpus_type="json", reduced_html=None)

        # default: plain text
        return CorpusPayload(corpus=str(text), corpus_type="text", reduced_html=None)

    # ------------------------------------------------------------------
    def _dispatch_filter_requests(
        self,
        corpus: str,
        items: ItemToExtract | List[ItemToExtract],
        separate: bool,
    ) -> List[GenerationResult]:
        it_list = [items] if isinstance(items, ItemToExtract) else items
        if len(it_list) == 1 or not separate:
            prompt = "\n\n".join(it.compile() for it in it_list)
            return [self.llm.filter_via_llm(corpus, prompt)]
        return [self.llm.filter_via_llm(corpus, it.compile()) for it in it_list]

    # ------------------------------------------------------------------
    def _assemble_filter_results(
        self,
        gen_results: List[GenerationResult],
        items: ItemToExtract | List[ItemToExtract],
        separate: bool,
    ) -> Tuple[Any, Optional[Dict[str, int]]]:
        if isinstance(items, ItemToExtract) or not separate:
            first = gen_results[0]
            return first.content, first.usage

        names = [it.name for it in items]
        content_map = {n: r.content for n, r in zip(names, gen_results)}

        usage_tot: Dict[str, int] = {}
        for r in gen_results:
            if r.usage:
                for k, v in r.usage.items():
                    usage_tot[k] = usage_tot.get(k, 0) + v
        return content_map, (usage_tot or None)

    # ------------------------------------------------------------------
    def _wrap_filter_op(
        self,
        content: Any,
        usage: Optional[Dict[str, Any]],
        reduced_html: Optional[str],
        success: bool,
        error: Optional[str],
        start_ts: float,
    ) -> FilterOp:
        return FilterOp.from_result(
            config=self.config,
            content=content,
            usage=usage,
            reduced_html=reduced_html,
            start_time=start_ts,
            success=success,
            error=error,
        )



def main() -> None:
    cfg = ExtractConfig()
    hero = FilterHero(cfg)

    items = [
        ItemToExtract(name="title", desc="Product title", example="Wireless Keyboard"),
        ItemToExtract(name="price", desc="Product price", regex_validator=r"€\d+\.\d{2}", example="€49.99"),
    ]

    html_doc = """
    <html><body>
      <div class="product"><h2 class="title">Wireless Keyboard</h2><span class="price">€49.99</span></div>
      <div class="product"><h2 class="title">USB-C Hub</h2><span class="price">€29.50</span></div>
      <div class="product"><h2 class="title">ABCHS</h2><span class="price">$129.50</span></div>
      <div class="product"><h2 class="title">enes</h2><span class="weight">129.50</span></div>
    </body></html>
    """

    f_op = hero.run(html_doc, items, text_type="html")
    print("Filtered corpus:\n", f_op.content)
    print("Success:", f_op.success)
    if f_op.usage:
        print("Usage:", f_op.usage)


if __name__ == "__main__":
    main()