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

from schemas import AskRequest, AskResponse

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
  - Add a "search_anchor"—an exact phrase or distinctive wording (6–20 words) from the document that can be found by Ctrl+F.
  - Also, include the "page_number" field, which is the page number(s) (**int, list of int, or null**) where the search_anchor is found in the document.
  - If the search_anchor cannot be reliably mapped to a page, set "page_number" to null.

**For Blank/Missing Fields:**
- Clearly state if a field is unfilled, illegible, or redacted.
- Distinguish between "field not present" and "field present but empty".

**For Inferred Information:**
- Use logical deduction only when confident and contextually appropriate.
- Clearly mark inferred versus explicitly stated information.
- Provide reasoning for inferences.

**For Ambiguous Questions:**
- Request clarification for questions with multiple possible interpretations.
- Provide alternative interpretations and respective answers.

### 5. Data Validation & Quality Assurance
- Validate data against expected formats.
- Check for internal consistency.
- Flag potential data quality issues.

### 6. Confidence Assessment Criteria
- 0.9–1.0: Explicit, unambiguous information.
- 0.7–0.8: Clearly present with minor interpretation.
- 0.5–0.6: Inferred from context with reasonable confidence.
- 0.3–0.4: Uncertain or partial information.
- 0.0–0.2: No relevant information or highly uncertain.

### 7. Error Handling & Edge Cases
- Handle corrupted, low-quality documents gracefully.
- Provide meaningful responses for password-protected/inaccessible content.
- Address multi-language or mixed-content documents.
- Manage large, complex documents.

### 8. Security & Privacy Considerations
- Handle sensitive info (e.g., SSNs, account numbers) appropriately.
- Note when information is confidential or restricted.
- Maintain discretion with private data.

## Response Requirements

Return your result as a well-formatted JSON object with these fields:

{
  "question": "(string) - The original question as provided",
  "answer": "(string) - The extracted or inferred answer, or clear statement if not found",
  "confidence": "(number 0.0-1.0) - Confidence level (per above criteria)",
  "reasoning": "(string) - Detailed explanation (how info was found/inferred, or why not found)",
  "total_pages": "(int or null) - The total number of pages in the analyzed document. If not determinable, use null.",
  "source": {
    "location": "(string or null) - e.g., 'Page 2, Table 1, Row 3' or 'Section 4.2'",
    "search_anchor": "(string or null) - Exact phrase or wording found in the document (6–20 words), as it appears in the document for Ctrl+F discovery",
    "page_number": "(int, array of int, or null) - The page(s) of the document where search_anchor appears. If not determinable, use null.",
    "context": "(string or null) - Surrounding text or section context",
    "extraction_method": "(string or null) - 'explicit', 'inferred', 'cross-referenced', or 'not_found'"
  },
  "verified": "(boolean) - True if the answer was cross-verified",
  "data_quality_notes": "(string or null) - Notes on data quality, legibility, or completeness",
  "alternative_interpretations": "(array or null) - Other possible answers if the question was ambiguous"
}

- Always include the "total_pages" field at the top level of the response. If you cannot determine the total, set it to null.
- Always include a search_anchor and its respective page_number(s) when possible.

## Quality Standards
- Prioritize accuracy over speed.
- When uncertain, acknowledge limitations rather than guess.
- Provide actionable information even when the primary answer isn't available.
- Use consistent terminology and formatting.
- Be explicit about assumptions or interpretations.

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