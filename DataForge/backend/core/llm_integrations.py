import os
import json
import logging
from typing import Dict, Any, List, Optional

# Attempt to load Anthropic and Gemini packages
HAS_GEMINI = False
HAS_ANTHROPIC = False

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    try:
        import google.generativeai as genai_legacy
        HAS_GEMINI = "legacy"
    except ImportError:
        pass

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    pass

class LLMIntegrations:
    """
    Integrates Gemini and Anthropic LLMs for column inference, normalization, and rules.
    Gracefully falls back to mock/heuristic methods if API keys are missing.
    """
    def __init__(self):
        # Read API keys from environment
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        
        # Configure clients if keys are available
        self.gemini_client = None
        self.anthropic_client = None
        
        if self.gemini_key:
            if HAS_GEMINI == True:
                try:
                    self.gemini_client = genai.Client(api_key=self.gemini_key)
                except Exception as e:
                    logging.error(f"Failed to initialize modern google-genai: {e}")
            elif HAS_GEMINI == "legacy":
                try:
                    genai_legacy.configure(api_key=self.gemini_key)
                    self.gemini_client = "legacy"
                except Exception as e:
                    logging.error(f"Failed to configure legacy google-generativeai: {e}")
                    
        if self.anthropic_key and HAS_ANTHROPIC:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
            except Exception as e:
                logging.error(f"Failed to initialize Anthropic client: {e}")
                
        logging.info(f"LLM Services: Gemini active: {self.gemini_client is not None}, Claude active: {self.anthropic_client is not None}")

    def is_ai_active(self) -> bool:
        return self.gemini_client is not None or self.anthropic_client is not None

    def _call_gemini(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """Calls Gemini API (preferring the new SDK, falling back to legacy)."""
        if not self.gemini_client:
            return None
            
        try:
            if HAS_GEMINI == True and isinstance(self.gemini_client, genai.Client):
                config = types.GenerateContentConfig()
                if system_instruction:
                    config.system_instruction = system_instruction
                # Default to gemini-2.5-flash for speed and reliability
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=config
                )
                return response.text
            elif HAS_GEMINI == "legacy" and self.gemini_client == "legacy":
                model_name = 'gemini-1.5-flash'
                if system_instruction:
                    model = genai_legacy.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                else:
                    model = genai_legacy.GenerativeModel(model_name=model_name)
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            logging.error(f"Gemini call error: {e}")
        return None

    def _call_claude(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Calls Anthropic API."""
        if not self.anthropic_client:
            return None
            
        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1000,
                "messages": messages
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = self.anthropic_client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            logging.error(f"Claude call error: {e}")
        return None

    def _call_llm(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        """Utility wrapper that routes to active LLM, prioritizing Claude first if available, then Gemini."""
        if self.anthropic_client:
            res = self._call_claude(prompt, system_prompt=system)
            if res:
                return res
        if self.gemini_client:
            return self._call_gemini(prompt, system_instruction=system)
        return None

    def infer_column_metadata(self, column_name: str, sample_values: List[str], industry: str = "General") -> Dict[str, str]:
        """
        Uses LLM to understand ambiguous column names and suggest clean standardized equivalents.
        """
        if not self.is_ai_active():
            return self._heuristic_column_inference(column_name, sample_values)
            
        system = "You are a professional data architect. Translate cryptic column headers to clean, standardized snake_case headers."
        prompt = f"""
        Industry context: {industry}
        Raw Column Name: "{column_name}"
        Sample Values: {sample_values}
        
        Analyze the column name and sample values. Output a JSON object containing:
        1. "standardized_name": A clean snake_case equivalent (e.g., "carton_weight_grams", "material_composition", "order_date").
        2. "description": A short, 1-sentence explanation of what this data column represents.
        3. "clean_datatype": The target type ('int', 'float', 'str', 'datetime', 'boolean', 'category').
        
        Respond with ONLY the raw JSON string. Do not include markdown code block syntax.
        """
        
        res = self._call_llm(prompt, system=system)
        if res:
            try:
                # Strip markdown code blocks if the LLM output includes them
                cleaned_res = res.strip()
                if cleaned_res.startswith("```"):
                    lines = cleaned_res.split("\n")
                    if lines[0].startswith("```json"):
                        cleaned_res = "\n".join(lines[1:-1])
                    elif lines[0].startswith("```"):
                        cleaned_res = "\n".join(lines[1:-1])
                return json.loads(cleaned_res)
            except Exception:
                pass
                
        return self._heuristic_column_inference(column_name, sample_values)

    def normalize_column_values(self, raw_values: List[str], context: str) -> Dict[str, str]:
        """
        Uses LLM to intelligently map unstructured messy strings to clean standardized values.
        Returns a dictionary mapping of {original_value: normalized_value}.
        """
        unique_vals = list(set(raw_values))
        if not unique_vals:
            return {}
            
        if not self.is_ai_active():
            return self._heuristic_value_normalization(unique_vals, context)
            
        system = "You are a data cleaning assistant. Normalize messy data entries into standardized, consistent, clean categories or formats."
        prompt = f"""
        Context/Column Concept: {context}
        Raw messy values to normalize:
        {unique_vals}
        
        For each value, suggest a clean, standardized, normalized category.
        Return your response as a JSON dictionary mapping the original raw value to the normalized value.
        For example:
        {{
          "Org. Cotton (GOTS Cert.)": "organic_cotton",
          "organic cotton": "organic_cotton",
          "Polyester (recycled)": "recycled_polyester"
        }}
        
        Respond with ONLY the raw JSON mapping. Do not include code blocks or other text.
        """
        
        res = self._call_llm(prompt, system=system)
        if res:
            try:
                cleaned_res = res.strip()
                if cleaned_res.startswith("```"):
                    lines = cleaned_res.split("\n")
                    if lines[0].startswith("```json"):
                        cleaned_res = "\n".join(lines[1:-1])
                    elif lines[0].startswith("```"):
                        cleaned_res = "\n".join(lines[1:-1])
                return json.loads(cleaned_res)
            except Exception:
                pass
                
        return self._heuristic_value_normalization(unique_vals, context)

    def suggest_rules_with_llm(self, schema: Dict[str, Any], industry: str = "General") -> List[Dict[str, Any]]:
        """
        Analyzes full dataset schema and suggests validation rules.
        """
        if not self.is_ai_active():
            return [] # will fallback to deterministic rule suggestions
            
        system = "You are a data validation expert. Generate data validation rules from a schema profile."
        # Keep schema payload small
        compact_schema = {}
        for col, stats in schema.items():
            compact_schema[col] = {
                "inferred_type": stats.get("inferred_type"),
                "unique_count": stats.get("unique_count"),
                "sample_values": stats.get("sample_values"),
                "min": stats.get("min"),
                "max": stats.get("max")
            }
            
        prompt = f"""
        Industry target: {industry}
        Schema Profile:
        {json.dumps(compact_schema, indent=2)}
        
        Generate a list of validation rules in JSON format.
        Supported rule types:
        - "non_null": {{}}
        - "unique": {{}}
        - "range": {{"min": number, "max": number}}
        - "regex": {{"pattern": "...", "description": "..."}}
        - "in_set": {{"allowed": ["val1", "val2", ...]}}
        
        Format the output as a JSON array of objects:
        [
          {{"column": "col_name", "type": "non_null", "params": {{}}}},
          {{"column": "col_name", "type": "range", "params": {{"min": 0, "max": 100}}}}
        ]
        
        Respond with ONLY the raw JSON array.
        """
        
        res = self._call_llm(prompt, system=system)
        if res:
            try:
                cleaned_res = res.strip()
                if cleaned_res.startswith("```"):
                    lines = cleaned_res.split("\n")
                    if lines[0].startswith("```json"):
                        cleaned_res = "\n".join(lines[1:-1])
                    elif lines[0].startswith("```"):
                        cleaned_res = "\n".join(lines[1:-1])
                return json.loads(cleaned_res)
            except Exception:
                pass
                
        return []

    # --- Fallback Heuristics for Offline/No Key Demo Mode ---
    
    def _heuristic_column_inference(self, column_name: str, sample_values: List[str]) -> Dict[str, str]:
        """Determines standardized column names using local lookup lists."""
        col_clean = str(column_name).lower().strip().replace(" ", "_").replace("-", "_")
        
        # Hardcoded dictionaries mapping standard messy interview/demo inputs to standard values
        mappings = {
            "ctn_wgt": ("carton_weight_grams", "Weight of the carton or item in grams", "float"),
            "ctn_weight": ("carton_weight_grams", "Weight of the carton or item in grams", "float"),
            "item_wgt": ("item_weight_kg", "Weight of the item in kilograms", "float"),
            "org_cotton": ("organic_cotton_pct", "Percentage of organic cotton content", "float"),
            "cust_id": ("customer_id", "Unique identifier for the customer", "str"),
            "cust_name": ("customer_name", "Full name of the customer", "str"),
            "first_name": ("first_name", "First name of the customer", "str"),
            "eml": ("email_address", "Email address of the contact", "str"),
            "email": ("email_address", "Email address of the contact", "str"),
            "ph_num": ("phone_number", "Phone contact number", "str"),
            "ph": ("phone_number", "Phone contact number", "str"),
            "dt_joined": ("date_joined", "Date when the user or customer registered", "datetime"),
            "reg_date": ("registration_date", "Date when the registration was recorded", "datetime"),
            "txn_amt": ("transaction_amount", "Value of the transaction in currency", "float"),
            "amt": ("transaction_amount", "Value of the transaction in currency", "float"),
        }
        
        if col_clean in mappings:
            std, desc, dtype = mappings[col_clean]
            return {
                "standardized_name": std,
                "description": f"(Heuristic fallback) {desc}",
                "clean_datatype": dtype
            }
            
        # Generic fallback mapping
        std_name = "".join([c if c.isalnum() or c == '_' else '' for c in col_clean])
        std_name = "_".join(filter(None, std_name.split("_")))
        
        # Try to infer clean type from sample values
        inferred_type = "str"
        try:
            # Let's inspect samples
            has_floats = False
            has_ints = False
            for v in sample_values:
                val_str = str(v).strip()
                if val_str.replace('.', '', 1).isdigit() and '.' in val_str:
                    has_floats = True
                elif val_str.isdigit():
                    has_ints = True
            if has_floats:
                inferred_type = "float"
            elif has_ints:
                inferred_type = "int"
        except Exception:
            pass
            
        return {
            "standardized_name": std_name if std_name else "column_clean",
            "description": f"(Heuristic fallback) Auto-standardized representation of column '{column_name}'",
            "clean_datatype": inferred_type
        }

    def _heuristic_value_normalization(self, unique_vals: List[str], context: str) -> Dict[str, str]:
        """Provides heuristic mapping for common text anomalies in organic fashion or standard domains."""
        mapping = {}
        context_lower = str(context).lower()
        
        for val in unique_vals:
            val_clean = str(val).strip()
            val_lower = val_clean.lower()
            
            # Fashion material mappings
            if "cotton" in val_lower or "ctn" in val_lower:
                if "org" in val_lower or "gots" in val_lower:
                    mapping[val_clean] = "organic_cotton"
                else:
                    mapping[val_clean] = "standard_cotton"
            elif "poly" in val_lower or "pes" in val_lower:
                if "recy" in val_lower:
                    mapping[val_clean] = "recycled_polyester"
                else:
                    mapping[val_clean] = "polyester"
            elif "wool" in val_lower:
                if "recy" in val_lower:
                    mapping[val_clean] = "recycled_wool"
                else:
                    mapping[val_clean] = "wool"
            # Transaction Statuses
            elif "success" in val_lower or "paid" in val_lower or "complete" in val_lower or val_lower == "s":
                mapping[val_clean] = "completed"
            elif "fail" in val_lower or "decline" in val_lower or val_lower == "f":
                mapping[val_clean] = "failed"
            elif "pend" in val_lower or "wait" in val_lower or val_lower == "p":
                mapping[val_clean] = "pending"
            # Generic Snake Case mapping
            else:
                generic = val_lower.replace(" ", "_").replace("-", "_")
                generic = "".join([c if c.isalnum() or c == '_' else '' for c in generic])
                mapping[val_clean] = "_".join(filter(None, generic.split("_")))
                
        return mapping
