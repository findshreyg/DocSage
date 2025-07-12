import os
from dotenv import load_dotenv
from schemas import AskRequest, AskResponse
import logging

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
    Process a user question by securely calling the Mistral LLM.

    This function performs the following:
    - Uses the authenticated user's ID to locate their file record in DynamoDB.
    - Handles format conversion if the uploaded file is not already a PDF.
    - Generates a secure S3 presigned URL for the LLM to access the file.
    - Checks for duplicate or similar questions using cosine similarity.
    - Calls the Mistral LLM with a structured prompt including the document.
    - Parses, validates, and saves the LLM's response to the conversation table.
    - Returns a validated structured answer.

    Args:
        payload (AskRequest): The input containing the file hash and question.
        user (dict): Authenticated user info, containing Cognito ID.

    Returns:
        AskResponse: The structured response containing the answer, confidence, source, and verification flag.

    Raises:
        HTTPException: For DynamoDB lookups, S3 issues, conversion failures,
                       LLM errors, JSON parse failures, or validation issues.
    """
    import boto3
    import os
    import httpx
    import json
    import re
    from fastapi import HTTPException
    from boto3.dynamodb.conditions import Key
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import datetime
    from decimal import Decimal

    try:
        AWS_REGION = os.getenv("AWS_REGION")
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        METADATA_TABLE_NAME = os.getenv("DDB_TABLE")
        S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

        # Use user information directly, don't call internal get-user endpoint
        user_id = user["sub"] if "sub" in user else user["Username"]

        table = dynamodb.Table(METADATA_TABLE_NAME)
        file_record = table.get_item(Key={"user_id": user_id, "hash": payload.file_hash})
        if "Item" not in file_record:
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
                s3_key_to_use = converted_key

            except s3_client.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "404":

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
                raise HTTPException(status_code=resp.status_code, detail=resp.text)

            result_text = resp.json()["choices"][0]["message"]["content"]

            match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if not match:
                raise HTTPException(status_code=500, detail="No valid JSON block found.")

            parsed = json.loads(match.group(1).strip())

            # Type checks for parsed fields
            if not isinstance(parsed.get("question"), str):
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'question'")
            if not isinstance(parsed.get("answer"), str):
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'answer'")
            if not isinstance(parsed.get("confidence"), (float, int)):
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'confidence'")
            if not isinstance(parsed.get("reasoning"), str):
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'reasoning'")
            if "source" not in parsed:
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing 'source'")
            if not isinstance(parsed.get("verified"), bool):
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

            # Return as validated Pydantic model
            return AskResponse(**parsed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
