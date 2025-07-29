#schemes.py

import re
from typing import List, Union, Dict, Any, Optional
from dataclasses import dataclass
from typing import Any, Optional
import time


from dataclasses import dataclass, field
from typing import List, Optional

# 

@dataclass
class CorpusPayload:
    corpus:       str                # Text input or original JSON string
    corpus_type:  str                # "html", "json" or "text"
    reduced_html: Optional[str]      # Only when HTML is reduced

    error:        Optional[str] = None    # ← give a default


@dataclass
class ItemToExtract:
    name: str                            # Unique field identifier, e.g. "package_type"
    desc: Optional[str] = None          # Description of what the field represents
    regex_validator: Optional[str] = None  # Optional regex pattern to validate extracted value
    text_rules: List[str] = field(default_factory=list)  # Any additional extraction/validation rules
    example: Optional[str] = None       # An example value to guide extraction

    def compile(self) -> str:
        parts = [f"field name: {self.name}"]
        if self.desc:
            parts.append(f"field description: {self.desc}")
        if self.text_rules:
            rules = "; ".join(self.text_rules)
            parts.append(f"text rules: {rules}")
        if self.example:
            parts.append(f"example: {self.example}")
        return "\n".join(parts)


class ExtractConfig:
    def __init__(
        self,
        must_exist_keywords: Union[str, List[str]] = None,
        keyword_case_sensitive: bool = False,
        keyword_whole_word: bool = True,
        semantics_exist_validation: Union[str, List[str]] = None,
        semantics_model: str = "gpt-4o-mini",
        regex_validation: Dict[str, str] = None,
        semantic_chunk_isolation: Union[str, List[str]] = None,
    ):
      
        self.must_exist_keywords = (
            [must_exist_keywords] if isinstance(must_exist_keywords, str) else must_exist_keywords
        )
        self.keyword_case_sensitive = keyword_case_sensitive
        self.keyword_whole_word = keyword_whole_word
        self.semantics_exist_validation = (
            [semantics_exist_validation]
            if isinstance(semantics_exist_validation, str)
            else semantics_exist_validation
        )
        self.semantics_model = semantics_model
        self.regex_validation = regex_validation or {}
        self.semantic_chunk_isolation = (
            [semantic_chunk_isolation]
            if isinstance(semantic_chunk_isolation, str)
            else semantic_chunk_isolation
        )




@dataclass
class FilterOp:
    success: bool                   # Whether filtering succeeded
    content: Any                    # The filtered corpus (text) for parsing
    usage: Optional[Dict[str, Any]] # LLM usage stats (tokens, cost, etc.)
    elapsed_time: float             # Time in seconds that the filter step took
    config: ExtractConfig           # The ExtractConfig used for this filter run
    reduced_html: Optional[str]     # Reduced HTML (if HTMLReducer was applied)
    error: Optional[str] = None   

    @classmethod
    def from_result(
        cls,
        config: ExtractConfig,
        content: Any,
        usage: Optional[Dict[str, Any]],
        reduced_html: Optional[str],
        start_time: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> "FilterOp":
        elapsed = time.time() - start_time
        return cls(
            success=success,
            content=content,
            usage=usage,
            elapsed_time=elapsed,
            config=config,
            reduced_html=reduced_html,
            error=error
        )
    


@dataclass
class ParseOp:
    success: bool                                  # Whether parsing succeeded
    content: Any                                   # The parsed result (e.g. dict, list, etc.)
    usage: Optional[Dict[str, Any]]                # LLM usage stats for parsing step
    elapsed_time: float                            # Time in seconds that the parse step took
    config: ExtractConfig                          # The ExtractConfig used for this parse run
    error: Optional[str] = None                    # Optional error message if success=False

    @classmethod
    def from_result(
        cls,
        config: ExtractConfig,
        content: Any,
        usage: Optional[Dict[str, Any]],
        start_time: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> "ParseOp":
        elapsed = time.time() - start_time
        return cls(
            success=success,
            content=content,
            usage=usage,
            elapsed_time=elapsed,
            config=config,
            error=error
        )

    


@dataclass
class ExtractOp:
    filter_op: FilterOp
    parse_op: ParseOp
    content: Optional[Any] = None       


    @property
    def success(self) -> bool:
        return self.filter_op.success and self.parse_op.success

