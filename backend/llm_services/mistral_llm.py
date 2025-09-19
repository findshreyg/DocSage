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
from utils import extract_json_from_llm_response
from schemas import (
    AskRequest, AskResponse,AdaptiveExtractRequest, AdaptiveExtractResponse,
    ClassificationResult, FieldDefinition, FieldValueWithConfidence,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

async def process_question(payload: AskRequest, user: dict) -> AskResponse:
    """
    Process a user question by orchestrating S3, DynamoDB, similarity search, and LLM call.
    """
    try:
        # Input validation
        if not payload.file_hash or not payload.question.strip():
            raise HTTPException(status_code=400, detail="file_hash and question are required")
        
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
                logger.info(f"Using converted PDF: {converted_key}")
            except Exception:
                logger.info(f"No converted PDF found, using original: {s3_key}")

        s3_url = s3_client.generate_presigned_url(
            'get_object', Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key}, ExpiresIn=3600
        )

        # Similarity search for previous questions
        conversation_table = dynamodb.Table(CONVERSATION_TABLE)
        try:
            prev_items = conversation_table.query(
                KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(payload.file_hash)
            )
            previous_questions = [item.get("question", "") for item in prev_items.get("Items", [])]
            
            if previous_questions:
                all_questions = previous_questions + [payload.question]
                vectorizer = TfidfVectorizer().fit(all_questions)
                vectors = vectorizer.transform(all_questions)
                sims = cosine_similarity(vectors[-1], vectors[:-1])
                
                if sims.size > 0 and sims.max() > 0.75:
                    idx = sims[0].argmax()
                    similar_item = prev_items["Items"][idx]
                    logger.info(f"Found similar question with confidence {sims.max():.3f}")
                    
                    # Parse source safely
                    source = None
                    if similar_item.get("source"):
                        try:
                            source = json.loads(similar_item.get("source"))
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse source from similar question")
                    
                    return AskResponse(
                        question=similar_item.get("question", ""),
                        answer=similar_item.get("answer", ""),
                        confidence=float(similar_item.get("confidence", 0.0)),
                        reasoning=similar_item.get("reasoning", ""),
                        source=source,
                        verified=similar_item.get("verified", False),
                        total_pages=similar_item.get("total_pages"),
                        data_quality_notes=similar_item.get("data_quality_notes"),
                        alternative_interpretations=json.loads(similar_item.get("alternative_interpretations", "null"))
                    )
        except Exception as e:
            logger.warning(f"Similarity search failed, continuing with LLM call: {str(e)}")

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
            "response_format": {"type": "json_object"}  # Force JSON response
        }

        logger.info(f"Making LLM API call for question: {payload.question[:100]}...")
        
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
                resp.raise_for_status()  # This will raise an exception for HTTP errors
                
            except httpx.TimeoutException:
                logger.error("Mistral API call timed out")
                raise HTTPException(status_code=504, detail="LLM service timeout")
            except httpx.HTTPStatusError as e:
                logger.error(f"Mistral API HTTP error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=502, detail=f"LLM service error: {e.response.status_code}")
            except Exception as e:
                logger.exception("Failed Mistral LLM API call")
                raise HTTPException(status_code=500, detail=f"Mistral API call failed: {str(e)}")

        # Parse response
        try:
            resp_json = resp.json()
            result_text = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not result_text:
                logger.error("Empty response from LLM API")
                logger.error(f"Full response: {resp_json}")
                raise HTTPException(status_code=500, detail="Empty response from LLM service")
            
            logger.info(f"LLM response length: {len(result_text)} characters")
            parsed = extract_json_from_llm_response(result_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM API response as JSON: {str(e)}")
            raise HTTPException(status_code=500, detail="Invalid JSON response from LLM service")
        except Exception as e:
            logger.error(f"Error processing LLM response: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to process LLM response")

        # Validate required fields with better error messages
        required_fields = ["question", "answer", "confidence", "reasoning", "source", "verified"]
        missing_fields = [field for field in required_fields if field not in parsed]
        if missing_fields:
            logger.error(f"LLM response missing required fields: {missing_fields}")
            logger.error(f"Available fields: {list(parsed.keys())}")
            raise HTTPException(
                status_code=500, 
                detail=f"LLM response missing required fields: {', '.join(missing_fields)}"
            )

        # Type and range checks with better error handling
        try:
            # Validate types
            if not isinstance(parsed["question"], str):
                raise ValueError("'question' must be string")
            if not isinstance(parsed["answer"], str):
                raise ValueError("'answer' must be string")
            if not isinstance(parsed["confidence"], (float, int)):
                raise ValueError("'confidence' must be number")
            if not (0.0 <= float(parsed["confidence"]) <= 1.0):
                raise ValueError("'confidence' must be between 0.0 and 1.0")
            if not isinstance(parsed["reasoning"], str):
                raise ValueError("'reasoning' must be string")
            if not isinstance(parsed["verified"], bool):
                raise ValueError("'verified' must be boolean")
            if parsed["source"] is not None and not isinstance(parsed["source"], dict):
                raise ValueError("'source' must be dict or null")

            # Validate optional fields
            if "data_quality_notes" in parsed and parsed["data_quality_notes"] is not None:
                if not isinstance(parsed["data_quality_notes"], str):
                    raise ValueError("'data_quality_notes' must be string or null")
            
            if "alternative_interpretations" in parsed and parsed["alternative_interpretations"] is not None:
                if not isinstance(parsed["alternative_interpretations"], list):
                    raise ValueError("'alternative_interpretations' must be list or null")
            
            # Ensure total_pages is present and valid
            if "total_pages" not in parsed:
                parsed["total_pages"] = None
            elif parsed["total_pages"] is not None and not isinstance(parsed["total_pages"], int):
                try:
                    parsed["total_pages"] = int(parsed["total_pages"])
                except (ValueError, TypeError):
                    parsed["total_pages"] = None

        except ValueError as e:
            logger.error(f"LLM response field validation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Invalid LLM response: {str(e)}")

        # Save to DynamoDB conversation table
        try:
            timestamp = datetime.datetime.now().isoformat()
            item = {
                "user_id": user_id,
                "file_hash_timestamp": f"{payload.file_hash}#{timestamp}",
                "file_hash": payload.file_hash,
                "question": parsed["question"],
                "answer": parsed["answer"],
                "confidence": Decimal(str(parsed["confidence"])),
                "reasoning": parsed["reasoning"],
                "source": json.dumps(parsed["source"]) if parsed["source"] else None,
                "verified": parsed["verified"]
            }
            
            # Add optional fields if present
            if parsed.get("total_pages") is not None:
                item["total_pages"] = parsed["total_pages"]
            if parsed.get("data_quality_notes"):
                item["data_quality_notes"] = parsed["data_quality_notes"]
            if parsed.get("alternative_interpretations"):
                item["alternative_interpretations"] = json.dumps(parsed["alternative_interpretations"])
            
            conversation_table.put_item(Item=item)
            logger.info("Successfully saved conversation to DynamoDB")
            
        except Exception as e:
            logger.error(f"Failed to save conversation to DynamoDB: {str(e)}")
            # Don't fail the entire request if we can't save to DB
            # The user still gets their answer

        # Return as Pydantic model
        try:
            return AskResponse(**parsed)
        except Exception as e:
            logger.error(f"Failed to create AskResponse object: {str(e)}")
            logger.error(f"Parsed data: {parsed}")
            raise HTTPException(status_code=500, detail="Failed to create response object")

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in process_question: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error occurred")

async def extract_adaptive_from_document(payload: AdaptiveExtractRequest, user: dict) -> AdaptiveExtractResponse:
    try:
        # === Step 0: Load PDF from S3, convert if needed ===
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(METADATA_TABLE_NAME)
        user_id = user.get("sub") or user.get("Username")
        item = table.get_item(Key={"user_id": user_id, "hash": payload.file_hash}).get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="File not found")
        s3_key = item.get("s3_key")
        converted_key = s3_key + ".converted.pdf"
        s3 = boto3.client("s3", region_name=AWS_REGION)
        # Check for PDF conversion
        try:
            s3.head_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
            s3_key = converted_key
        except Exception:
            pass
        s3_url = s3.generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key}, ExpiresIn=300)

        async with httpx.AsyncClient(timeout=180) as client:
            # === Single Step: Classification + Extraction ===
            prompt = """
Analyze this document step-by-step:

1. First, determine the document type by examining layout, headers, and content structure
2. Then, identify the most critical fields that should be extracted for this specific document type
3. Finally, extract those field values with high precision

Think through each step carefully before providing your final answer.

Return JSON in this exact format:
{
  "document_type": "precise label for document type (e.g., 'bank statement', 'invoice', 'medical report')",
  "description": "brief description of document purpose and key contents", 
  "confidence": 0.95,
  "extracted_fields": {
    "field_name_1": {
      "value": "extracted value",
      "confidence": 0.9,
      "reasoning": "brief explanation of why this value was chosen"
    },
    "field_name_2": {
      "value": "extracted value", 
      "confidence": 0.8,
      "reasoning": "brief explanation of why this value was chosen"
    }
  }
}

Be conservative with confidence scores - only use high confidence (>0.8) when you're very certain.
Focus on extracting the most critical fields that would be valuable for this document type.
"""
            response = await client.post(
                MISTRAL_API_URL,
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MISTRAL_LLM_MODEL,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "document_url", "document_url": s3_url}
                        ]
                    }],
                    "response_format": {"type": "json_object"}
                }
            )
            
            result = extract_json_from_llm_response(response.json()["choices"][0]["message"]["content"])

        # Build simplified response
        return AdaptiveExtractResponse(
            classification=ClassificationResult(
                document_type=result.get("document_type"),
                description=result.get("description"),
                confidence=result.get("confidence", 0.0)
            ),
            field_values={
                field_name: FieldValueWithConfidence(
                    value=field_data.get("value"),
                    confidence=field_data.get("confidence", 0.0)
                ) for field_name, field_data in result.get("extracted_fields", {}).items()
            },
            raw_extracted_text=response.json()["choices"][0]["message"]["content"]
        )
        
    except Exception as e:
        logger.exception("Adaptive extraction failed")
        raise HTTPException(status_code=500, detail=str(e))