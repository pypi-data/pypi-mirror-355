#extracthero.py


# to run python -m extracthero.extracthero

import re
# from typing import Any, Dict
from typing import List, Union, Dict, Any, Optional, Tuple
from time import time

from extracthero.myllmservice import MyLLMService
from extracthero.schemes import ExtractConfig
from extracthero.schemes import FilterOp, ParseOp, ExtractOp, ItemToExtract,PreprocessResult
from domreducer import HtmlReducer
from collections import OrderedDict
import json
from json import JSONDecodeError
# from string2Dict

from string2dict import String2Dict




class Extractor:
    def __init__(self, config: ExtractConfig = None, myllmservice=None):
        self.config = config or ExtractConfig()
        self.myllmservice = myllmservice or MyLLMService()


    
    def _prepare_corpus(
        self,
        text: str,
        text_type: Optional[str]
    ) -> PreprocessResult:
        """
        Parse/clean input once:
        - text_type="html" → corpus=stripped HTML
        - text_type="json" → corpus=parsed dict
        - else            → corpus=raw text
        """
        if text_type == "html":
            op = HtmlReducer(text).reduce()
            if op.success:
                return PreprocessResult(
                    corpus=op.reduced_data,
                    corpus_type="html",
                    reduced_html=op.reduced_data,
                    error=None
                )
            return PreprocessResult(
                corpus=text,
                corpus_type="html",
                reduced_html=None,
                error=None
            )

        if text_type == "json":
            parsed = String2Dict().run(text)
            if parsed is None:
                return PreprocessResult(
                    corpus=None,
                    corpus_type="json",
                    reduced_html=None,
                    error="Invalid JSON input"
                )
            return PreprocessResult(
                corpus=parsed,
                corpus_type="json",
                reduced_html=None,
                error=None
            )

        # plain text
        return PreprocessResult(
            corpus=text,
            corpus_type="text",
            reduced_html=None,
            error=None
        )
    

    def _wrap_filter_op(
        self,
        content: Any,
        usage: Optional[Dict],
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
    
    
    def _dispatch_filter_requests(
        self,
        corpus: str,
        items: Union[ItemToExtract, List[ItemToExtract]],
        separate: bool
    ):
        """
        Always returns a list of GenerationResult objects.
        - Single ItemToExtract & not separate → 1 call
        - List + separate=True    → 1 call per item
        - List + separate=False   → 1 combined call
        """
        # Normalize to list
        item_list = [items] if isinstance(items, ItemToExtract) else items

        if len(item_list) == 1 or not separate:
            # Combined prompt for one or many
            prompt = "\n\n".join(it.compile() for it in item_list)
            result = self.myllmservice.filter_via_llm(corpus, prompt)
            return [result]
    
        # separate == True & multiple items
        results = []
        for it in item_list:
            res = self.myllmservice.filter_via_llm(corpus, it.compile())
            results.append(res)
        return results

    
    def _assemble_filter_results(
        self,
        gen_results: List[GenerationResult],
        items_to_extract: Union[ItemToExtract, List[ItemToExtract]],
        filter_separately: bool
    ) -> Tuple[Any, Optional[Dict[str, int]]]:
        """
        Given a list of GenerationResults, produce the final content and aggregated usage.
        """
        # single-item or combined prompt branch
        if isinstance(items_to_extract, ItemToExtract) or not filter_separately:
            first = gen_results[0]
            return first.content, first.usage

        # per-item branch: map item.name -> its filtered text
        names = (
            [items_to_extract.name]
            if isinstance(items_to_extract, ItemToExtract)
            else [it.name for it in items_to_extract]
        )
        content_map: Dict[str, Any] = {
            name: res.content for name, res in zip(names, gen_results)
        }

        # aggregate usage by summing token counts, costs, etc.
        total_usage: Dict[str, int] = {}
        for res in gen_results:
            if res.usage:
                for k, v in res.usage.items():
                    total_usage[k] = total_usage.get(k, 0) + v

        usage_agg = total_usage or None
        return content_map, usage_agg


    def filter_with_llm(
        self,
        text: str,
        items_to_extract: Union[ItemToExtract, List[ItemToExtract]],
        text_type: Optional[str] = None,
        filter_separately: bool = False,
    ) -> FilterOp:
        start_ts = time()

        # 1. Preprocess
        pre = self._prepare_corpus(text, text_type)
        if pre.error:
            return self._wrap_filter_op(None, None, pre.reduced_html, False, pre.error, start_ts)

        # 2. JSON shortcut (no second parse)
        if pre.corpus_type == "json":
            data: Dict[str, Any] = pre.corpus  # already a dict
            keys = (
                [items_to_extract.name]
                if isinstance(items_to_extract, ItemToExtract)
                else [it.name for it in items_to_extract]
            )
            subset = {k: data.get(k) for k in keys}
            return self._wrap_filter_op(subset, None, None, True, None, start_ts)

        # 3. LLM-based filtering
        corpus_str = pre.corpus  # a str
        reduced_html = pre.reduced_html
        gen_results = self._dispatch_filter_requests(corpus_str, items_to_extract, filter_separately)

        # 4. Overall success
        if isinstance(items_to_extract, ItemToExtract) or not filter_separately:
            ok = gen_results[0].success
        else:
            ok = all(r.success for r in gen_results)

        # 5. Assemble and wrap
        content_final, usage_final = self._assemble_filter_results(gen_results, items_to_extract, filter_separately)
        return self._wrap_filter_op(
            content_final,
            usage_final,
            reduced_html,
            ok,
            None if ok else "LLM filter failed",
            start_ts
        )
    
    
    def parser(
        self,
        corpus: str,
        items_to_extract: Union[ItemToExtract, List[ItemToExtract]]
    ) -> ParseOp:
        start_ts = time()
        if isinstance(items_to_extract, ItemToExtract):
            prompt = items_to_extract.compile()
        else:
            prompt = "\n\n".join(it.compile() for it in items_to_extract)

        result = self.myllmservice.parse_via_llm(corpus, prompt)
        return ParseOp.from_result(
            config=self.config,
            content=result.content if result.success else None,
            usage=result.usage,
            start_time=start_ts,
            success=result.success,
            error=None if result.success else "LLM parse failed"
        )


    def extract(
            self,
            text: str,
            items_to_extract: Union[ItemToExtract, List[ItemToExtract]],
            text_type: str = None
        ) -> ExtractOp:
            filter_op = self.filter_with_llm(text, items_to_extract, text_type)
            if not filter_op.success:
                parse_op = ParseOp.from_result(
                    config=self.config,
                    content=None,
                    usage=None,
                    start_time=time(),
                    success=False,
                    error="Filter phase failed"
                )
                return ExtractOp(
                    filter_op=filter_op,
                    parse_op=parse_op,
                    content=None
                )

            parse_op = self.parser(filter_op.content, items_to_extract)
            return ExtractOp(
                filter_op=filter_op,
                parse_op=parse_op,
                content=parse_op.content
            )

    def check_if_contains_mandatory_keywords(self, text: str) -> bool:
        if not self.config.must_exist_keywords:
            return True
        flags = 0 if self.config.keyword_case_sensitive else re.IGNORECASE
        for kw in self.config.must_exist_keywords:
            pattern = (
                rf"\b{re.escape(kw)}\b"
                if self.config.keyword_whole_word
                else re.escape(kw)
            )
            if not re.search(pattern, text, flags):
                return False
        return True

    def confirm_that_content_theme_is_relevant_to_our_search(self, text: str) -> bool:
        if not self.config.semantics_exist_validation:
            return True
        result = self.myllmservice.confirm_that_content_theme_is_relevant_to_our_search(
            text, self.config.semantics_exist_validation
        )
        return bool(result.content)

    def isolate_relevant_chunk_only(self, text: str) -> str:
        result = self.myllmservice.isolate_relevant_chunk_only(
            text, self.config.semantic_chunk_isolation
        )
        return result.content

    def output_format_check_with_regex(self, results: Dict[str, Any]) -> bool:
        if not self.config.regex_validation:
            return True
        for field, pattern in self.config.regex_validation.items():
            value = results.get(field)
            if value is None or not re.fullmatch(pattern, str(value)):
                return False
        return True


def main():
    extractor = Extractor()
    # example usage...
    # sample_html = "<html>...</html>"

    sample_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Product Listing</title>
    </head>
    <body>
        <div class="product" id="prod-1001">
            <h2 class="title">Wireless Keyboard</h2>
            <p class="description">Ergonomic wireless keyboard with rechargeable battery</p>
            <span class="price">€49.99</span>
            <ul class="features">
                <li>Bluetooth connectivity</li>
                <li>Compact design</li>
            </ul>
        </div>
        <div class="product" id="prod-1002">
            <h2 class="title">USB-C Hub</h2>
            <p class="description">6-in-1 USB-C hub with HDMI and Ethernet ports</p>
            <span class="price">€29.50</span>
            <ul class="features">
                <li>4K HDMI output</li>
                <li>Gigabit Ethernet</li>
            </ul>
        </div>
    </body>
    </html>
    """
    # op = extractor.extract(sample_html, "Extract product names", text_type="html")
    op = extractor.extract(sample_html, "Extract product titles and prices", text_type="html")
    print(op.parse_op.content)

    print("reduced_html:")

    print(op.filter_op.content)

    print("")

    print("parse results:")
    print(op.parse_op.content)


if __name__ == "__main__":
    main()
