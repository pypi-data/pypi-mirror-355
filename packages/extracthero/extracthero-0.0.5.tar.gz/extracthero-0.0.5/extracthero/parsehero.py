# parsehero.py
# run with: python -m extracthero.parsehero


"""
ParseHero — the “parse” phase of ExtractHero.
  • Converts a filtered corpus into structured data keyed by ItemToExtract specs.
  • Skips the LLM when the corpus is already a dict, unless you force it.
  • Performs per-field regex validation after parsing.
  • Returns a ParseOp.
"""

from __future__ import annotations

import json as _json
from time import time
from typing import Any, Dict, List, Optional, Tuple, Union

from llmservice.generation_engine import GenerationResult
from extracthero.myllmservice import MyLLMService
from extracthero.schemes import ExtractConfig, ParseOp, ItemToExtract


class ParseHero:
    # ───────────────────────── init ─────────────────────────
    def __init__(
        self,
        config: Optional[ExtractConfig] = None,
        llm: Optional[MyLLMService] = None,
    ):
        self.config = config or ExtractConfig()
        self.llm = llm or MyLLMService()

    # ───────────────────────── public ───────────────────────
    def run(
        self,
        corpus: str | Dict[str, Any],
        items: ItemToExtract | List[ItemToExtract],
        enforce_llm_based_parse: bool = False,
    ) -> ParseOp:
        """
        Parameters
        ----------
        corpus : filtered text (str) or dict (from JSON fast-path).
        items  : one or more ItemToExtract.
        enforce_llm_based_parse : stringify dict and parse with LLM even when
                                  corpus is already a dict.
        """
        start_ts = time()

        # 1. dict fast-path (no LLM) unless caller forces an LLM parse
        if isinstance(corpus, dict) and not enforce_llm_based_parse:
            subset = self._subset_dict(corpus, items)
            ok, err = self._regex_validate(subset, items)
            return ParseOp.from_result(
                config=self.config,
                content=subset if ok else None,
                usage=None,
                start_time=start_ts,
                success=ok,
                error=err,
            )

        # 2. ensure we hand a **string** to the LLM
        if isinstance(corpus, dict):
            # serialise dict to JSON text
            corpus_str: str = _json.dumps(corpus, ensure_ascii=False, indent=2)
        elif isinstance(corpus, str):
            corpus_str: str = corpus
        else:
            return ParseOp.from_result(
                config=self.config,
                content=None,
                usage=None,
                start_time=start_ts,
                success=False,
                error=f"Unsupported corpus type: {type(corpus).__name__}",
            )

        # 3. build combined prompt
        prompt = (
            items.compile()
            if isinstance(items, ItemToExtract)
            else "\n\n".join(it.compile() for it in items)
        )

        # 4. call LLM
        gen: GenerationResult = self.llm.parse_via_llm(corpus_str, prompt)

        print("gen.content:", gen.content)

        if not gen.success:
            return ParseOp.from_result(
                config=self.config,
                content=None,
                usage=gen.usage,
                start_time=start_ts,
                success=False,
                error="LLM parse failed",
            )

        # 5. parse LLM JSON output

        parsed_dict=gen.content
        # try:
        #     parsed_dict: Dict[str, Any] = _json.loads(gen.content)

        # except Exception:
        #     print("parsed_dict not okay..........")
        #     return ParseOp.from_result(
        #         config=self.config,
        #         content=None,
        #         usage=gen.usage,
        #         start_time=start_ts,
        #         success=False,
        #         error="LLM returned non-JSON",
        #     )
        
        # 6. regex validation
       # print("parsed_dict okay..........")
        ok, err = self._regex_validate(parsed_dict, items)
        #print("regex ok..........", ok)
        
        return ParseOp.from_result(
            config=self.config,
            content=parsed_dict if ok else None,
            usage=gen.usage,
            start_time=start_ts,
            success=ok,
            error=err,
        )

    # ───────────────────── helper utilities ─────────────────────
    @staticmethod
    def _subset_dict(
        data: Dict[str, Any],
        items: ItemToExtract | List[ItemToExtract],
    ) -> Dict[str, Any]:
        keys = [items.name] if isinstance(items, ItemToExtract) else [it.name for it in items]
        return {k: data.get(k) for k in keys}

    @staticmethod
    def _regex_validate(
        data: Dict[str, Any],
        items: ItemToExtract | List[ItemToExtract],
    ) -> Tuple[bool, Optional[str]]:
        item_list = [items] if isinstance(items, ItemToExtract) else items
        import re

        for it in item_list:
            if it.regex_validator and it.name in data:
                if data[it.name] is None or not re.fullmatch(it.regex_validator, str(data[it.name])):
                    return False, f"Field '{it.name}' failed regex validation"
        return True, None
    

        # ───────────────────────── public (async) ───────────────────────
    
    async def run_async(
        self,
        corpus: str | Dict[str, Any],
        items: ItemToExtract | List[ItemToExtract],
        enforce_llm_based_parse: bool = False,
    ) -> ParseOp:
        """
        Same semantics as `run`, but non-blocking.
        Requires your `MyLLMService` to expose `parse_via_llm_async`.
        """
        start_ts = time()

        # 1. dict fast-path (skip LLM) unless caller forces an LLM parse
        if isinstance(corpus, dict) and not enforce_llm_based_parse:
            subset = self._subset_dict(corpus, items)
            ok, err = self._regex_validate(subset, items)
            return ParseOp.from_result(
                config=self.config,
                content=subset if ok else None,
                usage=None,
                start_time=start_ts,
                success=ok,
                error=err,
            )

        # 2. stringify non-str corpora
        if isinstance(corpus, dict):
            corpus_str: str = _json.dumps(corpus, ensure_ascii=False, indent=2)
        elif isinstance(corpus, str):
            corpus_str = corpus
        else:
            return ParseOp.from_result(
                config=self.config,
                content=None,
                usage=None,
                start_time=start_ts,
                success=False,
                error=f"Unsupported corpus type: {type(corpus).__name__}",
            )

        # 3. prompt
        prompt = (
            items.compile()
            if isinstance(items, ItemToExtract)
            else "\n\n".join(it.compile() for it in items)
        )

        # 4. call async LLM
        gen: GenerationResult = await self.llm.parse_via_llm_async(corpus_str, prompt)

        if not gen.success:
            return ParseOp.from_result(
                config=self.config,
                content=None,
                usage=gen.usage,
                start_time=start_ts,
                success=False,
                error="LLM parse failed",
            )

        # 5. decode JSON
        try:
            parsed_dict: Dict[str, Any] = _json.loads(gen.content)
        except Exception:
            return ParseOp.from_result(
                config=self.config,
                content=None,
                usage=gen.usage,
                start_time=start_ts,
                success=False,
                error="LLM returned non-JSON",
            )

        # 6. regex validation
        ok, err = self._regex_validate(parsed_dict, items)

        return ParseOp.from_result(
            config=self.config,
            content=parsed_dict if ok else None,
            usage=gen.usage,
            start_time=start_ts,
            success=ok,
            error=err,
        )


# ────────────────────────── demo ───────────────────────────
def main() -> None:
    cfg = ExtractConfig()
    hero = ParseHero(cfg)

    items = [
        ItemToExtract(name="title", desc="Product title", example="Wireless Keyboard"),
        ItemToExtract(name="price", desc="Product price", regex_validator=r"€\d+\.\d{2}", example="€49.99"),
    ]

    filtered_text = """
    title: Wireless Keyboard
    price: €49.99
    ---
    title: USB-C Hub
    price: €29.50
    """

    p_op = hero.run(filtered_text, items, enforce_llm_based_parse=True)
    print("Success:", p_op.success)
    print("Parsed dict:", p_op.content)


if __name__ == "__main__":
    main()
