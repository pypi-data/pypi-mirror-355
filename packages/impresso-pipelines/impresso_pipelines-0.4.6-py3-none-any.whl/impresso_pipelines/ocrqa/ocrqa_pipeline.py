from typing import List, Dict, Union, Optional
import unicodedata
from huggingface_hub import hf_hub_download, list_repo_files
from pybloomfilter import BloomFilter
import re
from functools import lru_cache

from impresso_pipelines.langident.langident_pipeline import LangIdentPipeline


@lru_cache(maxsize=1)
def cached_list_repo_files(repo_id: str):
    return list_repo_files(repo_id)


def get_bloomfilter(model_id: str, filename: str):
        return BloomFilter.open(hf_hub_download(repo_id=model_id, filename=filename))

class OCRQAPipeline:   
    def __init__(self):
        self.SUPPORTED_LANGUAGES = self.get_supported_languages()
        self.lang_model = LangIdentPipeline()  # Initialize LangIdentPipeline here
        self.bloomfilters = {}  # Cache for BloomFilter instances

    def get_supported_languages(self) -> set:
        repo_files = cached_list_repo_files("impresso-project/OCR-quality-assessment-unigram")
        languages = {file.split('-')[-1].split('.')[0] for file in repo_files if file.startswith("ocrqa-wp_v")}
        
        return languages

    def __call__(self, text, language=None, version=None, diagnostics=False, model_id=False, supported_languages=False):
        self.language = language
        self.version = version
        self.diagnostics = diagnostics
        self.model_id = model_id
        self.supported_languages = supported_languages
        
        if self.language is None:
            lang_result = self.lang_model(text)  # Use the initialized LangIdentPipeline
            self.language = lang_result["language"]

        if self.language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {self.language}")

        if self.version is None:
            repo_files = cached_list_repo_files("impresso-project/OCR-quality-assessment-unigram")
            versions = [
                re.search(r"_v(\d+\.\d+\.\d+)", file).group(1)
                for file in repo_files
                if file.startswith("ocrqa-wp_v") and file.endswith(f"-{self.language}.bloom")
            ]
            self.version = max(versions, key=lambda v: list(map(int, v.split('.'))))

        # Check if BloomFilter for the language and version is already cached
        bloomfilter_key = f"{self.language}_{self.version}"
        if bloomfilter_key not in self.bloomfilters:
            self.bloomfilters[bloomfilter_key] = get_bloomfilter(
                "impresso-project/OCR-quality-assessment-unigram", 
                f"ocrqa-wp_v{self.version}-{self.language}.bloom"
            )
        bf = self.bloomfilters[bloomfilter_key]

        output = self.filter_text(text, bf)

        if self.supported_languages:
            output["supported_languages"] = list(self.SUPPORTED_LANGUAGES)

        return output

    # Define normalization table
    QUOTES_PUNCT = "„•<>!\"#%&'’"
    ASCII_PUNCT = "()*,./:;?"
    BRACKETS_SPECIAL = "[]\\~_{}"
    UNICODE_PUNCT = "\xa1\xab\xb7\xbb\xbf"
    DASH_CARET = "—^`"
    SPECIAL_SYMBOLS = "¦§£="
    HYPHEN = "-"
    DIGITS = "0123456789"

    NORMALIZATION_TABLE = str.maketrans(
        {
            char: " "
            for char in (
                QUOTES_PUNCT
                + ASCII_PUNCT
                + BRACKETS_SPECIAL
                + UNICODE_PUNCT
                + DASH_CARET
                + SPECIAL_SYMBOLS
                + HYPHEN
            )
        }
        | {char: "0" for char in DIGITS}
    )


    def normalize_text(self, s: str, unicode_normalize: Optional[str] = "NFKC") -> str:
        """Normalize text by replacing punctuation with spaces and digits with '0'."""
        if unicode_normalize:
            s = unicodedata.normalize(unicode_normalize, s).lower()
        return s.translate(self.NORMALIZATION_TABLE)


    def filter(self, text: str, bloom_filter: BloomFilter):
        # Normalize and tokenize text
        normalized_text = self.normalize_text(text)
        tokens = normalized_text.split()

        # Check tokens against the bloom filter
        for token in tokens:
            if self.diagnostics:
                if token in bloom_filter:
                    print(f"'{token}' is in the bloom filter.")
                else:
                    print(f"'{token}' is NOT in the bloom filter.")


    def filter_text(self, DE_TEXT: str, bloom_filter: BloomFilter) -> Dict[str, Union[str, float, Dict[str, Union[List[str], str]]]]:
        """
        Filter the text using the bloom filter and return the score and diagnostics if enabled.

        Args:
            DE_TEXT (str): The input text to filter.
            bloom_filter (BloomFilter): The bloom filter to use for filtering.

        Returns:
            Dict[str, Union[str, float, Dict[str, Union[List[str, str]]]]]: The output containing language, score, and optionally diagnostics.
        """
        knowns = set()
        unknowns = set()

        # Normalize and tokenize text
        normalized_text = self.normalize_text(DE_TEXT)
        tokens = normalized_text.split()

        # Check tokens against the bloom filter
        for token in tokens:
            if token in bloom_filter:
                knowns.add(token)
            else:
                unknowns.add(token)

        # Compute the score
        score = len(knowns) / (len(knowns) + len(unknowns)) if (len(knowns) + len(unknowns)) > 0 else 0
        score = round(score, 1)

        output = {"language": self.language, "score": score}

        if self.diagnostics:
            output["diagnostics"] = {
                "known_tokens": list(knowns),
                "unknown_tokens": list(unknowns),
                "model_id": f"ocrqa-wp_v{self.version}-{self.language}"
            }
        elif self.model_id:
            output["model_id"] = f"ocrqa-wp_v{self.version}-{self.language}"

        return output
