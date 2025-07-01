import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv
from models.schemas import AskRequest, AskResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_LLM_MODEL = os.getenv("MISTRAL_LLM_MODEL")
MISTRAL_API_URL =os.getenv("MISTRAL_API_URL")

PROMPT_TEMPLATE = """
You are an intelligent assistant helping users answer questions strictly based on the content of the attached insurance certificate document.

Your task:
1. Carefully review all visible sections, including tables, headers, checkboxes, and form fields.
2. If the question refers to a specific field (e.g., limit, date, name), and the field is present but the value is blank or illegible, acknowledge that the field exists but is not filled in.
3. If the answer is present, extract it exactly as shown in the document.
4. Format your response as a JSON object with the following structure:
{{
  "question": (string),
  "answer": (string),
  "confidence": (number between 0.0 and 1.0),
  "reasoning": (string),
  "source": (object or null),
  "verified": (boolean)
}}

Now answer this question:
{question}
"""

async def process_question(payload: AskRequest, user: dict) -> AskResponse:
    """
    Process a question by calling Mistral LLM with a secure S3 document URL.
    Uses the authenticated user's ID from the access token.
    """
    import boto3
    import os
    import httpx
    import json
    import re
    from fastapi import HTTPException
    from boto3.dynamodb.conditions import Key, Attr
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import datetime
    from decimal import Decimal

    try:
        dynamodb = boto3.resource("dynamodb")
        METADATA_TABLE_NAME = os.getenv("DDB_TABLE")
        S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
        AWS_REGION = os.getenv("AWS_REGION")

        user_id = user["sub"]

        table = dynamodb.Table(METADATA_TABLE_NAME)
        file_record = table.get_item(Key={"user_id": user_id, "hash": payload.file_hash})
        if "Item" not in file_record:
            logger.warning(f"File not found for user")
            raise HTTPException(status_code=404, detail="File not found for user.")
        s3_key = file_record["Item"]["s3_key"]
        s3_client = boto3.client("s3", region_name=AWS_REGION)

        import tempfile
        import subprocess

        def download_from_s3(bucket, key, local_path):
            s3_client.download_file(bucket, key, local_path)

        def upload_to_s3(bucket, key, local_path):
            s3_client.upload_file(local_path, bucket, key)

        def convert_to_pdf(input_path: str) -> str:
            output_path = input_path.rsplit(".", 1)[0] + ".pdf"
            subprocess.run([
                "libreoffice", "--headless", "--convert-to", "pdf",
                "--outdir", os.path.dirname(input_path),
                input_path
            ], check=True)
            return output_path

        content_type = file_record["Item"].get("content_type")
        if not content_type:
            logger.warning(f"Missing content_type for s3_key={s3_key}. Inferring from extension.")
            ext = s3_key.lower().split(".")[-1]
            if ext in ["ppt", "pptx", "odp"]:
                content_type = "application/vnd.ms-powerpoint"
            elif ext in ["xls", "xlsx", "ods"]:
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                content_type = "application/pdf"
        needs_conversion = content_type in [
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]

        if needs_conversion:
            converted_key = s3_key + ".converted.pdf"

            try:
                s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
                logger.info(f"Reusing existing converted PDF")
                s3_key_to_use = converted_key

            except s3_client.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    logger.info(f"No converted PDF found — converting to PDF now")

                    with tempfile.TemporaryDirectory() as tmpdir:
                        local_path = os.path.join(tmpdir, os.path.basename(s3_key))
                        download_from_s3(S3_BUCKET_NAME, s3_key, local_path)
                        converted_path = convert_to_pdf(local_path)
                        upload_to_s3(S3_BUCKET_NAME, converted_key, converted_path)

                    s3_key_to_use = converted_key
                else:
                    raise
        else:
            s3_key_to_use = s3_key

        s3_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key_to_use},
            ExpiresIn=3600
        )

        conversation_table = dynamodb.Table("IDPConversation")

        past_items = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(payload.file_hash)
        )

        previous_questions = [item["question"] for item in past_items.get("Items", [])]
        if previous_questions:
            vectorizer = TfidfVectorizer().fit(previous_questions + [payload.question])
            vectors = vectorizer.transform(previous_questions + [payload.question])
            sims = cosine_similarity(vectors[-1], vectors[:-1])
            max_sim_idx = sims.argmax()
            max_sim_val = sims[0, max_sim_idx]

            if max_sim_val > 0.85:
                similar_item = past_items["Items"][max_sim_idx]
                logger.info(f"Returning similar previous answer")
                return AskResponse(
                    question=similar_item["question"],
                    answer=similar_item["answer"],
                    confidence=similar_item["confidence"],
                    reasoning=similar_item["reasoning"],
                    source=json.loads(similar_item["source"]),
                    verified=similar_item["verified"]
                )

        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = PROMPT_TEMPLATE.format(question=payload.question)

        data = {
            "model": MISTRAL_LLM_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "document_url",
                            "document_url": s3_url
                        }
                    ]
                }
            ],
            "document_image_limit": 8,
            "document_page_limit": 1000
        }

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(MISTRAL_API_URL, headers=headers, json=data)

            if resp.status_code != 200:
                logger.error(f"LLM API error: {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail=resp.text)

            result_text = resp.json()["choices"][0]["message"]["content"]

            match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if not match:
                logger.error("No valid JSON block found in LLM response.")
                raise HTTPException(status_code=500, detail="No valid JSON block found.")

            parsed = json.loads(match.group(1).strip())

            # Type checks for parsed fields
            if not isinstance(parsed.get("question"), str):
                logger.error("Invalid LLM response: missing or invalid 'question'")
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'question'")
            if not isinstance(parsed.get("answer"), str):
                logger.error("Invalid LLM response: missing or invalid 'answer'")
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'answer'")
            if not isinstance(parsed.get("confidence"), (float, int)):
                logger.error("Invalid LLM response: missing or invalid 'confidence'")
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'confidence'")
            if not isinstance(parsed.get("reasoning"), str):
                logger.error("Invalid LLM response: missing or invalid 'reasoning'")
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'reasoning'")
            # source can be None or dict
            if "source" not in parsed:
                logger.error("Invalid LLM response: missing 'source'")
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'source'")
            if not isinstance(parsed.get("verified"), bool):
                logger.error("Invalid LLM response: missing or invalid 'verified'")
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'verified'")

            timestamp = datetime.datetime.now().isoformat()

            conversation_table.put_item(Item={
                "user_id": user_id,
                "file_hash_timestamp": f"{payload.file_hash}#{timestamp}",
                "file_hash": payload.file_hash,
                "question": parsed["question"],
                "answer": parsed["answer"],
                "confidence": Decimal(str(parsed["confidence"])),
                "reasoning": parsed["reasoning"],
                "source": json.dumps(parsed["source"]),
                "verified": parsed["verified"]
            })

            logger.info(f"Question processed successfully")
            # Return as validated Pydantic model
            return AskResponse(**parsed)
    except Exception as e:
        logger.exception("Unexpected error in process_question")
        raise HTTPException(status_code=500, detail=str(e))


async def extract_metadata(file_bytes: bytes, file_name: str):
    """
    Calls Mistral LLM to extract metadata + common questions from a document.
    """
    try:
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""
        You are an intelligent assistant. Analyze the uploaded document '{file_name}'.
        Extract the key metadata (title, type, number of pages, created date) and return
        5 likely questions a user might ask about this document. Respond in JSON:
        {{
          "metadata": {{
            "title": string,
            "type": string,
            "pages": int,
            "created_date": string
          }},
          "questions": [string, ...]
        }}
        """

        data = {
            "model": MISTRAL_LLM_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(MISTRAL_API_URL, headers=headers, json=data)

            if resp.status_code != 200:
                logger.error(f"LLM API error (metadata): {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail=resp.text)

            import re
            import json

            result_text = resp.json()["choices"][0]["message"]["content"]

            match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if match:
                logger.info(f"Metadata extracted successfully for file_name={file_name}")
                return json.loads(match.group(1).strip())
            else:
                logger.error("No valid JSON block found in LLM metadata response.")
                raise HTTPException(status_code=500, detail="No valid JSON block found in LLM metadata response.")
    except Exception as e:
        logger.exception("Error in extract_metadata")
        raise HTTPException(status_code=500, detail=str(e))

async def get_conversations(user_id: str, file_hash: str):
    import boto3
    from boto3.dynamodb.conditions import Key

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("IDPConversation")

    response = table.query(
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(file_hash)
    )

    items = response.get("Items", [])
    return items