import os
import logging
import json
from typing import Any, Dict, List
import boto3
from decimal import Decimal
from dotenv import load_dotenv
from fastapi import HTTPException
from boto3.dynamodb.conditions import Key, Attr
import datetime
import httpx
import re
import time
from .utils import extract_json_from_llm_response
from .schemas import (
    AskRequest, AskResponse,AdaptiveExtractRequest, AdaptiveExtractResponse,
    ClassificationResult, FieldDefinition, FieldValueWithConfidence,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Helper function to convert floats to Decimals for DynamoDB
def floats_to_decimals(obj):
    if isinstance(obj, list):
        return [floats_to_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: floats_to_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        # Using str() is important for precision
        return Decimal(str(obj))
    return obj

load_dotenv()
logger = logging.getLogger(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_LLM_MODEL = os.getenv("MISTRAL_LLM_MODEL")
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL")
AWS_REGION = os.getenv("AWS_REGION")
METADATA_TABLE_NAME = os.getenv("DDB_TABLE")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
CONVERSATION_TABLE = os.getenv("DYNAMODB_CONVERSATION_TABLE", "IDPConversation")

REQUIRED_VARS = [
    MISTRAL_API_KEY, MISTRAL_LLM_MODEL, MISTRAL_API_URL, AWS_REGION,
    METADATA_TABLE_NAME, S3_BUCKET_NAME
]
if not all(REQUIRED_VARS):
    raise RuntimeError("One or more environment variables required for LLM are missing.")

PROMPT_TEMPLATE = """
You are an advanced document intelligence assistant specialized in extracting accurate, reliable information from uploaded documents, including insurance certificates, financial statements, contracts, legal documents, forms, and other structured or semi-structured materials.

## Core Analysis Framework

### 1. Document Assessment & Preprocessing
- Assess document quality, readability, and structure.
- Identify document type, layout, and organization.
- Note accessibility issues (scan quality, rotated text, watermarks, redactions).
- Catalog headers, footers, tables, forms, signatures, stamps, and annotations.

### 2. Comprehensive Content Analysis
- Systematically review all visible content:
  - Body text, tables, charts, form fields.
  - Headers, subheaders, dividers.
  - Checkboxes, radio buttons, selection indicators.
  - Signatures, stamps.
  - Footnotes, fine print, metadata, document properties.
  - Cross-references and related document mentions.

### 3. Multi-Document Coordination
- If there are multiple documents, establish relationships and cross-references.
- Prioritize primary documents.
- Flag contradictions or inconsistencies across documents.

### 4. Question Processing & Response Strategy

**For Explicit Information:**
- Extract exactly as written, preserving formatting.
- In the "source" section:
  - Add a "search_anchor" — an exact phrase (6–20 words) quoted directly from the document, preferably taken from or very close to the answer. It must appear verbatim in the document and help locate the content using Ctrl+F.
  - Also include the "page_number" — the exact page number (as a single integer) where both the answer and the search_anchor appear together in the document.
  - If the page number cannot be reliably identified, set it to null. Do not return a list — always return a single int or null.

**For Blank/Missing Fields:**
- Clearly state if a field is unfilled, illegible, or redacted.
- Distinguish between "field not present" and "field present but empty".

**For Inferred Information:**
- Use logical deduction only if confident.
- Clearly indicate that inference was used and explain the reasoning.

**For Ambiguous Questions:**
- Ask for clarification if the question has multiple valid interpretations.
- Provide alternative interpretations and respective answers when appropriate.

### 5. Data Validation & Quality Assurance
- Validate extracted data formats (dates, numbers, identifiers).
- Check for cross-reference consistency.
- Flag data quality issues or visual barriers to extraction.

### 6. Confidence Assessment Criteria
- 0.9–1.0: Explicit, unambiguous answer.
- 0.7–0.8: Requires mild interpretation.
- 0.5–0.6: Inferred from contextual clues.
- 0.3–0.4: Highly uncertain or partial.
- 0.0–0.2: No evidence or severely ambiguous.

### 7. Error Handling & Edge Cases
- Gracefully handle unreadable, encrypted, or damaged documents.
- Indicate when content is inaccessible.
- Accommodate multi-language or mixed-layout structure.

### 8. Security & Privacy Considerations
- Handle sensitive info (e.g., SSNs, account numbers) with care.
- Respect confidentiality and minimize exposure in explanations.

## Response Requirements

Return your result as a well-formatted JSON object with these fields:

{
  "question": "(string) - The original question as asked",
  "answer": "(string) - The response extracted or inferred from the document",
  "confidence": "(number 0.0–1.0) - Estimate of certainty using rubric above",
  "reasoning": "(string) - How the answer was derived, or why it was not",
  "total_pages": "(int or null) - Total number of pages in the analyzed document",
  "source": {
    "location": "(string or null) - e.g., 'Page 2, Table 1' or 'Section 3.1'",
    "search_anchor": "(string or null) - A 6–20 word phrase quoted directly from the document near or within the answer",
    "page_number": "(int or null) - The specific page number where both search_anchor and answer appear. Always a single integer or null — do not return a list.",
    "context": "(string or null) - Excerpt or paragraph surrounding the search_anchor",
    "extraction_method": "(string or null) - One of: 'explicit', 'inferred', 'cross-referenced', or 'not_found'"
  },
  "verified": "(boolean) - True if the answer was confidently verified against multiple parts of the document",
  "data_quality_notes": "(string or null) - Notes about document legibility or clarity",
  "alternative_interpretations": "(array or null) - Alternative valid answers if ambiguity exists"
}

- Always include the "total_pages" field in top-level response.
- search_anchor must be directly from the document and clearly support the answer.
- page_number must be the exact single page where both the answer and search_anchor were found. Return null only if not reliably determined.

## Quality Standards
- Prioritize accuracy and traceability.
- Do not guess or invent missing values.
- Use consistent structure and field names.
- Favor direct quotes and page-level traceability over summaries.

Now analyze the provided document(s) and answer this question: {question}
"""


def safe_format_prompt(template: str, question: str) -> str:
    """
    Safe prompt string formatting in case question contains curly braces.
    """
    return template.replace("{question}", question.replace("{", "{{").replace("}", "}}"))

def extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    """
    Extracts the JSON block from the LLM response.
    Returns a parsed dict.
    Raises HTTPException if block not found or not valid.
    """
    # Look for the first JSON object in the response
    json_block_pattern = re.compile(r"\{[\s\S]*\}")
    match = json_block_pattern.search(text)
    if not match:
        raise HTTPException(status_code=500, detail="No valid JSON block found in LLM response.")
    try:
        return json.loads(match.group(0))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse JSON from LLM response.")

async def process_question(payload: AskRequest, user: dict) -> AskResponse:
    """
    Process a user question by orchestrating S3, DynamoDB, similarity search, and LLM call.
    """
    try:
        # Retrieve metadata and verify S3 presence
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(METADATA_TABLE_NAME)
        user_id = user.get("sub") or user.get("Username")
        if not user_id:
            raise HTTPException(status_code=400, detail="User identifier not found in Cognito attributes")

        file_record = table.get_item(Key={"user_id": user_id, "hash": payload.file_hash})
        if "Item" not in file_record:
            raise HTTPException(status_code=404, detail="File not found for user.")

        s3_key = file_record["Item"].get("s3_key")
        if not s3_key:
            raise HTTPException(status_code=500, detail="S3 key not found in file metadata.")

        s3_client = boto3.client("s3", region_name=AWS_REGION)

        # Use converted PDF if available
        if not s3_key.lower().endswith(".pdf"):
            converted_key = s3_key + ".converted.pdf"
            try:
                s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
                s3_key = converted_key
            except Exception:
                pass  # If not, stick with the original

        s3_url = s3_client.generate_presigned_url(
            'get_object', Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key}, ExpiresIn=3600
        )

        # Similarity search for previous questions
        conversation_table = dynamodb.Table(CONVERSATION_TABLE)
        prev_items = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(payload.file_hash)
        )
        previous_questions = [item.get("question", "") for item in prev_items.get("Items", [])]
        if previous_questions:
            all_questions = previous_questions + [payload.question]
            vectorizer = TfidfVectorizer().fit(all_questions)
            vectors = vectorizer.transform(all_questions)
            sims = cosine_similarity(vectors[-1], vectors[:-1])
            if sims.size > 0 and sims.max() > 0.85:
                idx = sims[0].argmax()
                similar_item = prev_items["Items"][idx]
                return AskResponse(
                    question=similar_item.get("question", ""),
                    answer=similar_item.get("answer", ""),
                    confidence=float(similar_item.get("confidence", 0.0)),
                    reasoning=similar_item.get("reasoning", ""),
                    source=json.loads(similar_item.get("source")) if similar_item.get("source") else None,
                    verified=similar_item.get("verified", False),
                )

        # Prepare LLM API call
        try:
            prompt = safe_format_prompt(PROMPT_TEMPLATE, payload.question)
        except Exception as e:
            logger.exception("Prompt formatting error.")
            raise HTTPException(status_code=500, detail="Prompt formatting failed.")

        data = {
            "model": MISTRAL_LLM_MODEL,
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "document_url", "document_url": s3_url}
                ]}
            ],
            "document_image_limit": 8,
            "document_page_limit": 1000,
        }

        async with httpx.AsyncClient(timeout=180) as http_client:
            try:
                resp = await http_client.post(
                    MISTRAL_API_URL,
                    headers={
                        "Authorization": f"Bearer {MISTRAL_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=data
                )
            except Exception as e:
                logger.exception("Failed Mistral LLM API call")
                raise HTTPException(status_code=500, detail=f"Mistral API call failed: {str(e)}")

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        resp_json = resp.json()
        result_text = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        parsed = extract_json_from_llm_response(result_text)

        # Validate required fields
        required_fields = ["question", "answer", "confidence", "reasoning", "source", "verified"]
        for field in required_fields:
            if field not in parsed:
                raise HTTPException(status_code=500, detail=f"LLM response missing '{field}'.")

        # Type and range checks
        if not isinstance(parsed["question"], str):
            raise HTTPException(status_code=500, detail="LLM field 'question' must be string")
        if not isinstance(parsed["answer"], str):
            raise HTTPException(status_code=500, detail="LLM field 'answer' must be string")
        if (
            not isinstance(parsed["confidence"], (float, int))
            or not (0.0 <= float(parsed["confidence"]) <= 1.0)
        ):
            raise HTTPException(status_code=500, detail="LLM field 'confidence' out of range (0.0-1.0)")
        if not isinstance(parsed["reasoning"], str):
            raise HTTPException(status_code=500, detail="LLM field 'reasoning' must be string")
        if not isinstance(parsed["verified"], bool):
            raise HTTPException(status_code=500, detail="LLM field 'verified' must be bool")
        if parsed["source"] is not None and not isinstance(parsed["source"], dict):
            raise HTTPException(status_code=500, detail="LLM field 'source' must be dict or null")

        # Extra optional fields
        if "data_quality_notes" in parsed and parsed["data_quality_notes"] and not isinstance(parsed["data_quality_notes"], str):
            raise HTTPException(status_code=500, detail="LLM field 'data_quality_notes' must be string or null")
        if "alternative_interpretations" in parsed and parsed["alternative_interpretations"] and not isinstance(parsed["alternative_interpretations"], list):
            raise HTTPException(status_code=500, detail="LLM field 'alternative_interpretations' must be list or null")

        # Save to DynamoDB conversation table
        timestamp = datetime.datetime.now().isoformat()
        item = {
            "user_id": user_id,
            "file_hash_timestamp": f"{payload.file_hash}#{timestamp}",
            "file_hash": payload.file_hash,
            "question": parsed["question"],
            "answer": parsed["answer"],
            "confidence": Decimal(str(parsed["confidence"])),
            "reasoning": parsed["reasoning"],
            "source": json.dumps(parsed["source"]),
            "verified": parsed["verified"]
        }
        if "data_quality_notes" in parsed and parsed["data_quality_notes"]:
            item["data_quality_notes"] = parsed["data_quality_notes"]
        if "alternative_interpretations" in parsed and parsed["alternative_interpretations"]:
            item["alternative_interpretations"] = json.dumps(parsed["alternative_interpretations"])
        conversation_table.put_item(Item=item)

        # Return as Pydantic model
        return AskResponse(**parsed)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"process_question failed: {str(e)}")

# async def extract_adaptive_from_document(payload: AdaptiveExtractRequest, user: dict) -> AdaptiveExtractResponse:
#     try:
#         # === Step 0: Load PDF from S3, convert if needed ===
#         dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
#         table = dynamodb.Table(METADATA_TABLE_NAME)
#         user_id = user.get("sub") or user.get("Username")
#         item = table.get_item(Key={"user_id": user_id, "hash": payload.file_hash}).get("Item")
#         if not item:
#             raise HTTPException(status_code=404, detail="File not found")
#         s3_key = item.get("s3_key")
#         converted_key = s3_key + ".converted.pdf"
#         s3 = boto3.client("s3", region_name=AWS_REGION)
#         # Check for PDF conversion
#         try:
#             s3.head_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
#             s3_key = converted_key
#         except Exception:
#             pass
#         s3_url = s3.generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key}, ExpiresIn=300)

#         async with httpx.AsyncClient(timeout=180) as client:
#             # === Step 1: Dynamic, natural language classification ===
#             step1_prompt = """
# You're analyzing a document. Based solely on its content and layout, respond with:
# 1. document_type: a clear label describing the document's actual purpose (e.g., "bank statement", "flight itinerary", "medical prescription", etc.).
# 2. description: a 1-2 sentence summary of what this document represents and what data it likely contains.
# 3. confidence: float 0.0–1.0, your certainty in this classification.

# Output strictly in JSON as:
# {
#   "document_type": "...",
#   "description": "...",
#   "confidence": 0.0
# }
# """
#             step1_response = await client.post(
#                 MISTRAL_API_URL,
#                 headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
#                 json={
#                     "model": MISTRAL_LLM_MODEL,
#                     "messages": [{"role": "user", "content": [{"type": "text", "text": step1_prompt}, {"type": "document_url", "document_url": s3_url}]}],
#                     "response_format": {"type": "json_object"}
#                 }
#             )
#             step1_content = step1_response.json()["choices"][0]["message"]["content"]
#             classification = extract_json_from_llm_response(step1_content)

#             # === Step 2: Context-rich field discovery with confidences ===
#             full_classification_json = json.dumps(classification, indent=2)
#             step2_prompt = f"""
# You are analyzing a document classified as:
# {full_classification_json}

# Based on this document_type and description, list the most important fields (with precise names) that should be extracted from such a document.
# For each field, provide:
# - field: field name
# - description: short description
# - confidence: float (how important/relevant it is for this document type, 0.0-1.0)

# Output in JSON as:
# {{"fields_to_extract": [{{"field": "...", "description": "...", "confidence": 0.0}}]}}
# """
#             step2_response = await client.post(
#                 MISTRAL_API_URL,
#                 headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
#                 json={
#                     "model": MISTRAL_LLM_MODEL,
#                     "messages": [{"role": "user", "content": [{"type": "text", "text": step2_prompt}]}],
#                     "response_format": {"type": "json_object"}
#                 }
#             )
#             fields_obj = extract_json_from_llm_response(step2_response.json()["choices"][0]["message"]["content"])
#             fields_to_extract = fields_obj.get("fields_to_extract", [])

#             # === Step 3: Contextual field extraction with per-field confidence ===
#             field_block_json = json.dumps(fields_to_extract, indent=2)
#             step3_prompt = f"""
# You are an expert data extractor for insurance loss run reports.
# The document has been classified as:
# {full_classification_json}

# This document contains top-level policy information and a list of individual claims. Your task is to extract this information into a structured JSON object.

# First, extract the overall policy information.
# Next, iterate through EACH individual claim in the document and extract the following fields for each one:
# {field_block_json}

# Return a single JSON object. The JSON object must have a key "policy_information" for the main details, and a key "claims" which is a LIST of JSON objects, where each object represents a single claim.
# Ensure all monetary values are returned as numbers only, without '$' symbols or commas.

# Here is the required final format:
# {{
#   "policy_information": {{
#     "policy_number": "...",
#     "policy_period": "...",
#     "insured_entity_name": "...",
#     "insurance_carrier": "..."
#   }},
#   "claims": [
#     {{
#       "claim_number": "...",
#       "claim_date": "...",
#       "claim_status": "...",
#       "claim_description": "...",
#       "claimant_name": "...",
#       "loss_amount": 1234.56,
#       "expense_amount": 123.45,
#       "total_paid_amount": 1358.01,
#       "reserve_amount": 0
#     }}
#   ]
# }}
# """
#             step3_response = await client.post(
#                 MISTRAL_API_URL,
#                 headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
#                 json={
#                     "model": MISTRAL_LLM_MODEL,
#                     "messages": [{"role": "user", "content": [{"type": "text", "text": step3_prompt}, {"type": "document_url", "document_url": s3_url}]}],
#                     "response_format": {"type": "json_object"}
#                 }
#             )
#             extraction_data = extract_json_from_llm_response(step3_response.json()["choices"][0]["message"]["content"])

#             # Correctly handle the new structured response
#             policy_info = extraction_data.get("policy_information", {})
#             claims_list = extraction_data.get("claims", [])

#             final_field_values = {}
#             for key, value in policy_info.items():
#                 final_field_values[key] = FieldValueWithConfidence(value=value, confidence=0.95)
            
#             final_field_values["claims"] = FieldValueWithConfidence(value=claims_list, confidence=0.95)

#             return AdaptiveExtractResponse(
#                 classification=ClassificationResult(
#                     document_type=classification.get("document_type"),
#                     description=classification.get("description"),
#                     confidence=classification.get("confidence", 0.0)
#                 ),
#                 fields_to_extract=[
#                     FieldDefinition(
#                         field=f.get("field"),
#                         description=f.get("description"),
#                         confidence=f.get("confidence", 0.0)
#                     ) for f in fields_to_extract
#                 ],
#                 field_values=final_field_values,
#                 raw_extracted_text=step3_response.json()["choices"][0]["message"]["content"]
#             )

#     except Exception as e:
#         logger.exception("Adaptive extraction failed")
#         raise HTTPException(status_code=500, detail=str(e))

# This is the new, experimental single-call function and adding caching 
async def extract_adaptive_from_document(payload: AdaptiveExtractRequest, user: dict) -> dict:
    try:
        # === Step 0: Connect to DynamoDB and get the item ===
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(METADATA_TABLE_NAME)
        user_id = user.get("sub") or user.get("Username")
        item = None
        for i in range(5):  # Try up to 5 times
            print(f"--- Attempt {i+1} to get item from DynamoDB...")
            result = table.get_item(Key={"user_id": user_id, "hash": payload.file_hash})
            if "Item" in result:
                item = result["Item"]
                print("--- Successfully found item in DynamoDB.")
                break  # Exit the loop if we found it
            print("--- Item not found, waiting 2 seconds before retry...")
            time.sleep(2)  # Wait for 2 seconds

        if not item:
            # If we still haven't found it after all retries, then fail.
            logger.error("Failed to find item in DynamoDB after multiple retries.")
            raise HTTPException(status_code=404, detail="File not found in database after retries.")

        # === THE CACHING LOGIC (FAST PATH) ===
        if "extracted_data" in item:
            print("--- CACHE HIT: Returning saved data from DynamoDB. ---")
            return item["extracted_data"]

        # === THE SLOW PATH (if no cached data is found) ===
        print("--- CACHE MISS: Performing full AI extraction. ---")
        s3_key = item.get("s3_key")
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3_url = s3.generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key}, ExpiresIn=300)

        # The single, optimized prompt
        optimized_prompt = """
You are an expert data extraction engine. Your task is to perform a complete analysis of the provided document in a single step.

1.  First, classify the document. Determine its "document_type" (e.g., "insurance loss run report") and provide a short "description".
2.  Second, based on that classification, determine the most relevant fields to extract.
3.  Third, extract the values for those fields from the document. The document may contain top-level information and a list of items (like claims).

Your final output MUST be a single JSON object with a key "policy_information" for top-level details and a key "claims" which MUST be a LIST of JSON objects.
Ensure all monetary values are returned as numbers without currency symbols.

Example format:
{
  "policy_information": { "policy_number": "...", ... },
  "claims": [ { "claim_number": "...", ... } ]
}
"""
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                MISTRAL_API_URL,
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MISTRAL_LLM_MODEL,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": optimized_prompt}, {"type": "document_url", "document_url": s3_url}]}],
                    "response_format": {"type": "json_object"}
                }
            )
        
        extraction_data = extract_json_from_llm_response(response.json()["choices"][0]["message"]["content"])
        
        policy_info = extraction_data.get("policy_information", {})
        claims_list = extraction_data.get("claims", [])
        final_field_values = {}
        for key, value in policy_info.items():
            final_field_values[key] = {"value": value, "confidence": 0.9}
        final_field_values["claims"] = {"value": claims_list, "confidence": 0.9}

        # === SAVE THE NEW RESULT TO THE DATABASE ===
        try:
            print("--- SAVING to DynamoDB for next time... ---")
            # table.update_item(
            #     Key={
            #         'user_id': user_id,
            #         'hash': payload.file_hash
            #     },
            #     UpdateExpression="SET extracted_data = :data",
            #     ExpressionAttributeValues={
            #         # Use the helper function to convert the data before saving
            #         ':data': floats_to_decimals(final_field_values)
            #     }
            # )
            table.update_item(
                Key={'user_id': user_id, 'hash': payload.file_hash},
                UpdateExpression="SET metadata.extracted_adaptive_data = :data",
                ExpressionAttributeValues={':data': floats_to_decimals(final_field_values)}
            )
        except Exception as db_error:
            logger.error(f"Could not save extracted data to DynamoDB: {db_error}")
            # Temporarily raise an error to make it visible
            raise HTTPException(status_code=500, detail=f"DB_SAVE_FAILED: {str(db_error)}")

        return final_field_values

    except Exception as e:
        logger.exception("Optimized adaptive extraction failed")
        raise HTTPException(status_code=500, detail=str(e))
    
# new function to llm_services/mistral_llm.py
def get_cached_extraction(file_hash: str, user: dict):
    try:
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(METADATA_TABLE_NAME)
        user_id = user.get("sub") or user.get("Username")
        item = table.get_item(Key={"user_id": user_id, "hash": file_hash}).get("Item")

        # CORRECTED PATH: Look inside 'metadata' for 'extracted_adaptive_data'
        if item and "metadata" in item and "extracted_adaptive_data" in item["metadata"]:
            # If the data exists, return it
            return item["metadata"]["extracted_adaptive_data"]
        
        # If data is not ready yet, tell the frontend it's still processing
        return {"status": "processing"}

    except Exception as e:
        logger.error(f"Failed to get cached data: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve extraction data.")