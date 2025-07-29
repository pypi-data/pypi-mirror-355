# canonmap/services/artifact_generator/_structure_parser_helper.py

from collections import defaultdict
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import json
import warnings
import re
import subprocess
import sys

import pandas as pd
import numpy as np
import spacy

from canonmap.utils.date_type_helpers import DATE_FORMATS, DOMINANCE_THRESHOLD

def download_spacy_model():
    """Download the spaCy model if not present."""
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    except subprocess.CalledProcessError:
        print("Warning: Failed to download spaCy model. You may need to run 'python -m spacy download en_core_web_sm' manually.")

class StructureParserHelper:
    """
    Internal helper class to replicate the robust cleaning, schema inference,
    and entity‐extraction logic. All methods are private except for parse_dataframe
    and build_known_entities.
    """

    def __init__(self, num_cores: int, nlp: Optional[spacy.Language] = None):
        self.all_ner_entities: set = set()
        self.num_cores = num_cores
        self.nlp = nlp  # Don't load the model here, just store the reference

    def _get_nlp(self) -> Optional[spacy.Language]:
        """Lazy load the spaCy model when needed."""
        if self.nlp is None:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                warnings.warn("spaCy model 'en_core_web_sm' not found. NER functionality will be disabled.")
                return None
        return self.nlp

    def parse_dataframe(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Union[str, Any]]], Dict[str, Dict[str, Any]]]:
        """
        Clean & format columns, then infer schema. Returns:
          - cleaned_df,
          - column_map { cleaned_col: { original_field_name, data_type, field_category } },
          - schema_map { cleaned_col: { "data_type": <type>, "date_format_in_database": <fmt or None> (only if DATE/DATETIME) } }
        """
        cleaned_df, column_map = self._clean_and_format_columns(df.copy())
        schema_map = self._infer_schema(cleaned_df)

        # Update column_map with the inferred data_type
        for col, info in schema_map.items():
            column_map[col]["data_type"] = info["data_type"]
            # field_category remains "Uncategorized"
        return cleaned_df, column_map, schema_map

    def build_known_entities(
        self,
        metadata: List[Dict[str, Any]],
        table_name: str,
        allowed_fields: Optional[set] = None,
        max_uniqueness_ratio: float = 0.95,
        max_avg_length: float = 50.0,
        normalize: bool = False
    ) -> Dict[str, List[str]]:
        """
        Build per‐column candidate entity lists from a list of row‐dicts:
          - Groups values by column
          - Computes "unsplit" vs "comma‐split" stats
          - Chooses the variant with lower uniqueness ratio unless heuristics override
          - Optionally runs spaCy NER on long text fields
          - Skips fields with avg length > max_avg_length or uniqueness ratio ≥ max_uniqueness_ratio
            unless always_include or name
        Returns { field_name: sorted_list_of_entities }
        """
        groups: Dict[str, List[str]] = defaultdict(list)

        for row in metadata:
            for key, val in row.items():
                if allowed_fields and key not in allowed_fields:
                    continue
                groups[key].append(str(val))

        candidate_entities: Dict[str, List[str]] = {}
        for field, values in groups.items():
            non_empty = [v for v in values if v.strip()]
            if not non_empty:
                continue

            tot_unsplit, _, ratio_unsplit, avg_unsplit = self._analyze_field_values(non_empty, split=False)
            tot_split, _, ratio_split, avg_split = self._analyze_field_values(non_empty, split=True)

            # is_always = field in always_include_fields
            is_name_field = self._is_likely_name_field(field)
            is_name_content = self._is_likely_name_content(non_empty)

            # Choose split vs unsplit
            if tot_split > 0 and ratio_split < ratio_unsplit:
                chosen_variant = "split"
                chosen_ratio = ratio_split
                chosen_avg = avg_split
                vals = {token.strip() for v in non_empty for token in v.split(",") if token.strip()}
            else:
                chosen_variant = "unsplit"
                chosen_ratio = ratio_unsplit
                chosen_avg = avg_unsplit
                vals = {v.strip() for v in non_empty if v.strip()}

            adjusted_ratio = max_uniqueness_ratio
            if is_name_field or is_name_content:
                adjusted_ratio = 0.99

            # Skip if avg length too large (and not name/always)
            if not (is_name_field or is_name_content):
                if chosen_avg > max_avg_length:
                    if self.nlp:
                        ner_set: set = set()
                        for v in non_empty:
                            ents = self._extract_entities_from_text(v)
                            ner_set.update(ents)
                            self.all_ner_entities.update(ents)
                        if ner_set:
                            vals.update(ner_set)
                            if normalize:
                                # ONLY strip whitespace, DO NOT lowercase
                                vals = {val.strip() for val in vals}
                            candidate_entities[field] = sorted(vals)
                    continue
                if chosen_ratio >= adjusted_ratio:
                    continue

            if normalize:
                # ONLY strip whitespace, DO NOT lowercase
                vals = {val.strip() for val in vals}
            candidate_entities[field] = sorted(vals)

        return candidate_entities

    # -----------------------------
    # Cleaning & formatting columns
    # -----------------------------
    def _clean_and_format_columns(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Dict[str, str]]]:
        cleaned_cols: List[str] = []
        column_map: Dict[str, Dict[str, str]] = {}

        for orig in df.columns:
            cleaned = self._clean_column_name(orig)
            cleaned_cols.append(cleaned)
            column_map[cleaned] = {
                "original_field_name": orig,
                "data_type": "STRING",
                "field_category": "Uncategorized"
            }

        df = df.rename(columns=dict(zip(df.columns, cleaned_cols)))

        for col in df.columns:
            lower = col.lower()
            dtype_before = df[col].dtype

            if 'name' in lower:
                df[col] = df[col].astype(str).apply(self._format_name)
            elif 'email' in lower:
                df[col] = df[col].astype(str).apply(self._format_email)
            elif 'phone' in lower or 'number' in lower:
                df[col] = df[col].astype(str).apply(self._format_phone)

            numeric_hints = ['cost', 'price', 'amount', 'total', 'value', 'estimate', 'num', 'qty', 'quantity']
            is_numeric_col = dtype_before == object or any(hint in lower for hint in numeric_hints)
            if is_numeric_col:
                s = df[col].astype(str)
                cleaned_s = (
                    s.str.replace(',', '', regex=False)
                     .str.replace('$', '', regex=False)
                     .str.replace('£', '', regex=False)
                     .str.replace('€', '', regex=False)
                     .str.replace('k', '', case=False, regex=False)
                     .str.replace('m', '', case=False, regex=False)
                )
                as_num = pd.to_numeric(cleaned_s, errors='coerce')
                mask = ~s.isna() & (s != '') & (s.str.lower() != 'null')
                if mask.any():
                    rate = (~as_num[mask].isna()).mean()
                    if rate >= 0.95:
                        df[col] = as_num

        return df, column_map

    # -----------------------------
    # Schema inference
    # -----------------------------
    def _infer_schema(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dict mapping each cleaned column name to:
          {
            "data_type": <"INTEGER" | "FLOAT64" | "BOOLEAN" | "STRING" | "DATE" | "DATETIME" | "JSON">,
            "date_format_in_database": <format string or None>   # only present for DATE/DATETIME
          }
        """
        schema: Dict[str, Dict[str, Any]] = {}
        for col in df.columns:
            series = df[col]
            entry: Dict[str, Any] = {"data_type": None}

            # 1) If pandas already thinks it's integer, float, or boolean
            if pd.api.types.is_integer_dtype(series.dtype):
                entry["data_type"] = "INTEGER"
                schema[col] = entry
                continue
            if pd.api.types.is_float_dtype(series.dtype):
                entry["data_type"] = "FLOAT64"
                schema[col] = entry
                continue
            if pd.api.types.is_bool_dtype(series.dtype):
                entry["data_type"] = "BOOLEAN"
                schema[col] = entry
                continue

            # 2) Otherwise, coerce to str and try numeric
            s = series.astype(str)
            mask = ~s.isna() & (s != "") & (s.str.lower() != "null")
            cleaned_s = s.str.replace(",", "", regex=False)
            as_num = pd.to_numeric(cleaned_s, errors="coerce")

            if mask.any():
                sub = as_num[mask]
                num_rate = sub.notna().mean()
            else:
                num_rate = 0.0

            if num_rate >= 0.95:
                # Mostly numeric → decide between INTEGER vs FLOAT
                if ((sub.dropna() % 1) == 0).all():
                    entry["data_type"] = "INTEGER"
                else:
                    entry["data_type"] = "FLOAT64"
                schema[col] = entry
                continue
            else:
                entry["data_type"] = "STRING"

            # 3) DATE / DATETIME detection on columns still marked STRING
            detected_type, detected_fmt = self._detect_datetime_type_and_format(series)
            if detected_type:
                entry["data_type"] = detected_type
                # Always include the key for date/datetime columns
                entry["date_format_in_database"] = detected_fmt
                schema[col] = entry
                continue

            # 4) JSON detection: test first 50 non-null strings
            sample_vals = series.dropna().astype(str).head(50)
            cnt = 0
            tot = 0
            for v in sample_vals:
                tot += 1
                try:
                    json.loads(v)
                    cnt += 1
                except Exception:
                    pass
            if tot > 0 and (cnt / tot) >= DOMINANCE_THRESHOLD:
                entry["data_type"] = "JSON"

            schema[col] = entry

        return schema

    # -----------------------------
    # Date detection helper (with simple pattern fallback)
    # -----------------------------
    def _detect_datetime_type_and_format(
        self,
        series: pd.Series,
        threshold: float = 0.9
    ) -> Tuple[Optional[str], Optional[str]]:
        r"""
        Attempt to parse a pandas Series of strings as dates/datetimes.
        Returns (dtype, format_string) or (None, None) if insufficient match.

        • Look at *all* non-null strings (cast to str) in this column.
        • For each candidate in ArtifactGenerator._DATE_FORMATS, parse that full list with errors="coerce",
          compute parse_rate = (# parsed notnull) / (total non-null).
        • Pick the candidate with the highest parse_rate. If best_rate ≥ 0.5,
          accept that as "best_fmt" and re‐parse the full column with format=best_fmt.
        • Otherwise, fallback to pandas' inference (dateutil), setting best_fmt = None.
        • Once dt_series (full column) is available:
          – If ≥ threshold (default 0.9) of *all* values parse (including null rows), return either
            ("DATE", best_fmt) if all non-null times are midnight, or
            ("DATETIME", best_fmt) otherwise.
          – If parse_rate < threshold, return (None, None).
        • If we fell back to dateutil (best_fmt is None) but parse_rate ≥ threshold,
          attempt a simple regex‐based heuristic on the original non-null strings:
            – If every non-null string matches r"^\d{4}-\d{2}-\d{2}$", set best_fmt = "%Y-%m-%d"
            – Else if every non-null string matches r"^\d{2}/\d{2}/\d{4}$", set best_fmt = "%m/%d/%Y"
            – Else if every non-null string matches r"^\d{8}$", set best_fmt = "%Y%m%d"
          In all other fallback cases, leave best_fmt = None.
        """
        all_strs = series.dropna().astype(str)
        total_non_null = len(all_strs)
        if total_non_null == 0:
            return None, None

        best_fmt: Optional[str] = None
        best_rate: float = 0.0

        for fmt in DATE_FORMATS:
            try:
                parsed = pd.to_datetime(all_strs, format=fmt, errors="coerce")
                rate = parsed.notnull().mean()
                if rate > best_rate:
                    best_rate = rate
                    best_fmt = fmt
            except Exception:
                continue

        if best_fmt is not None and best_rate >= 0.5:
            try:
                dt_series = pd.to_datetime(series, format=best_fmt, errors="coerce")
            except Exception:
                best_fmt = None
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    dt_series = pd.to_datetime(series, errors="coerce")
        else:
            best_fmt = None
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                dt_series = pd.to_datetime(series, errors="coerce")

        valid_rate = dt_series.notnull().mean()
        if valid_rate < threshold:
            return None, None

        if best_fmt is None:
            if all(re.match(r"^\d{4}-\d{2}-\d{2}$", s) for s in all_strs):
                best_fmt = "%Y-%m-%d"
            elif all(re.match(r"^\d{2}/\d{2}/\d{4}$", s) for s in all_strs):
                best_fmt = "%m/%d/%Y"
            elif all(re.match(r"^\d{8}$", s) for s in all_strs):
                best_fmt = "%Y%m%d"
            else:
                best_fmt = None

        non_null = dt_series.dropna()
        if (
            (non_null.dt.hour == 0).all()
            and (non_null.dt.minute == 0).all()
            and (non_null.dt.second == 0).all()
        ):
            return "DATE", best_fmt
        else:
            return "DATETIME", best_fmt

    # -----------------------------
    # Column name cleaning
    # -----------------------------
    def _clean_column_name(self, col: str) -> str:
        col_lower = col.lower()
        col_lower = re.sub(r'[\s\-./]+', '_', col_lower)
        col_lower = re.sub(r'\d+', lambda m: self._number_to_text(m.group()), col_lower)
        col_lower = re.sub(r'[^a-z_]', '', col_lower)
        col_lower = re.sub(r'_+', '_', col_lower)
        col_lower = col_lower.strip('_')
        if not col_lower or not col_lower[0].isalpha():
            col_lower = f"col_{col_lower}"
        return col_lower

    def _number_to_text(self, s: str) -> str:
        num_map = {
            '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
            '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
        }
        return ''.join(num_map.get(ch, ch) for ch in s)

    # -----------------------------
    # Simple formatters for name/email/phone
    # -----------------------------
    def _format_name(self, name: str) -> str:
        return name.strip().title()

    def _format_email(self, email: str) -> str:
        return email.strip().lower()

    def _format_phone(self, phone: str) -> str:
        digits = re.sub(r'\D', '', phone or "")
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) == 7:
            return f"{digits[:3]}-{digits[3:]}"
        return phone

    # -----------------------------
    # Entity detection heuristics
    # -----------------------------
    @staticmethod
    def _is_likely_name_field(field_name: str) -> bool:
        patterns = [
            r'.*name.*', r'.*author.*', r'.*owner.*', r'.*creator.*',
            r'.*user.*', r'.*person.*', r'.*customer.*', r'.*client.*', r'.*employee.*'
        ]
        fld = field_name.lower()
        return any(re.match(pat, fld) for pat in patterns)

    @staticmethod
    def _is_likely_name_content(values: List[str]) -> bool:
        sample_size = min(50, len(values))
        vals = list(values)
        try:
            if len(vals) > sample_size:
                indices = np.random.choice(len(vals), sample_size, replace=False)
                sample = [vals[i] for i in indices]
            else:
                sample = vals
        except Exception:
            sample = vals[:sample_size]

        patterns = [
            r'^[A-Z][a-z]+ [A-Z][a-z]+$',        # First Last
            r'^[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+$',# First M. Last
            r'^[A-Z][a-z]+$',                   # Single name
            r'^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+$'  # First Middle Last
        ]
        matches = 0
        total = len(sample)
        if total == 0:
            return False
        for v in sample:
            txt = str(v).strip()
            if any(re.match(pat, txt) for pat in patterns):
                matches += 1
        return (matches / total) > 0.3

    # -----------------------------
    # spaCy NER on a single string
    # -----------------------------
    def _extract_entities_from_text(self, text: str) -> Set[str]:
        """Extract entities from text using spaCy NER."""
        nlp = self._get_nlp()
        if not nlp:
            return set()
            
        doc = nlp(str(text))
        entities: Set[str] = set()
        for ent in doc.ents:
            txt = ent.text.strip()
            if 2 <= len(txt) <= 50 and txt.lower() not in nlp.vocab.strings:
                entities.add(txt)
                if ent.label_ == "PERSON":
                    parts = txt.split()
                    if len(parts) > 1:
                        entities.add(parts[-1])  # last name
                        entities.add(parts[0])   # first name
        return entities

    # -----------------------------
    # Analyze list of strings (split or unsplit)
    # -----------------------------
    @staticmethod
    def _analyze_field_values(values: List[str], split: bool = False) -> Tuple[int, int, float, float]:
        if split:
            tokens = [tok.strip() for v in values for tok in v.split(",") if tok.strip()]
            total = len(tokens)
            unique = len(set(tokens))
            avg_len = np.mean([len(tok) for tok in tokens]) if total > 0 else 0.0
        else:
            total = len(values)
            unique = len(set(values))
            avg_len = np.mean([len(v) for v in values]) if total > 0 else 0.0
        ratio = (unique / total) if total > 0 else 0.0
        return total, unique, ratio, avg_len