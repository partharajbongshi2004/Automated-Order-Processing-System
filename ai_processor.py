import os
import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


class ExtractedOrder(BaseModel):
    product_name: str = Field(
        description="The closest matching product name from the store catalog."
    )
    size: str = Field(
        description="Clothing size normalized to S, M, L, or XL."
    )
    quantity: int = Field(
        description="Number of items requested by the customer. Defaults to 1 if unspecified."
    )


def _fallback_extract(message: str, available_products: List[str]) -> Dict:
    """
    Rule-based keyword & regex extraction when no Gemini API key is configured.
    """
    msg_lower = message.lower()

    # 1. Match product name by keyword overlap
    best_match = available_products[0] if available_products else "Classic Cotton T-Shirt"
    highest_score = 0

    for product in available_products:
        keywords = [w for w in product.lower().split() if len(w) > 2]
        score = sum(1 for kw in keywords if kw in msg_lower)
        # Handle common synonyms
        if "tee" in msg_lower and "t-shirt" in product.lower():
            score += 2
        if "hoodie" in msg_lower and "hoodie" in product.lower():
            score += 2
        if "jeans" in msg_lower and "jeans" in product.lower():
            score += 2
        if "jacket" in msg_lower and "jacket" in product.lower():
            score += 2

        if score > highest_score:
            highest_score = score
            best_match = product

    # 2. Extract size (supports words like 'large' or codes like 'L', 'XL')
    size = "M"
    size_patterns = [
        (r"\b(extra large|x-large|xl)\b", "XL"),
        (r"\b(large|l)\b", "L"),
        (r"\b(medium|med|m)\b", "M"),
        (r"\b(small|sm|s)\b", "S"),
    ]
    for pattern, normalized_size in size_patterns:
        if re.search(pattern, msg_lower):
            size = normalized_size
            break

    # 3. Extract quantity (supports digits and basic number words)
    quantity = 1
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }
    digit_match = re.search(r"\b(\d+)\b", msg_lower)
    if digit_match:
        quantity = int(digit_match.group(1))
    else:
        for word, num in word_to_num.items():
            if re.search(rf"\b{word}\b", msg_lower):
                quantity = num
                break

    return {
        "product_name": best_match,
        "size": size,
        "quantity": max(1, quantity),
        "extraction_method": "Fallback Rule Engine (No API Key)",
    }


def extract_order_details(
    message: str,
    available_products: List[str],
    api_key: Optional[str] = None,
) -> Dict:
    """
    Extract product_name, size, and quantity from a raw customer message using Gemini API.
    Falls back to rule-based extraction if no API key is provided.
    """
    resolved_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()

    if not resolved_key:
        return _fallback_extract(message, available_products)

    try:
        client = genai.Client(api_key=resolved_key)

        catalog_str = ", ".join(f'"{p}"' for p in available_products)
        prompt = f"""
        You are an order processing assistant for a clothing store.
        Extract the ordered item details from the customer's message below.

        Available Store Catalog: [{catalog_str}]

        Rules:
        1. Map the requested item to the closest exact product name from the Available Store Catalog.
        2. Normalize the clothing size to one of: S, M, L, XL. (If unspecified, default to M).
        3. Extract the integer quantity requested. (If unspecified, default to 1).

        Customer Message:
        "{message}"
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedOrder,
                temperature=0.1,
            ),
        )

        parsed: ExtractedOrder = response.parsed
        return {
            "product_name": parsed.product_name,
            "size": parsed.size.upper(),
            "quantity": parsed.quantity,
            "extraction_method": "Gemini 2.5 Flash AI",
        }

    except Exception as e:
        fallback_result = _fallback_extract(message, available_products)
        fallback_result["extraction_method"] = f"Fallback Engine (API Error: {str(e)})"
        return fallback_result
