import os
import logging
from typing import Optional, Dict, Tuple, List

import boto3
from fastapi import HTTPException
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError, BotoCoreError

load_dotenv()

DYNAMODB_CONVERSATION_TABLE = os.getenv("DYNAMODB_CONVERSATION_TABLE")
AWS_REGION = os.getenv("AWS_REGION")

if not DYNAMODB_CONVERSATION_TABLE or not AWS_REGION:
    raise RuntimeError("Server configuration error: Missing environment variable(s)")

try:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    conversation_table = dynamodb.Table(DYNAMODB_CONVERSATION_TABLE)
except Exception as e:
    logging.exception("Failed to initialize DynamoDB resources.")
    raise HTTPException(status_code=500, detail="Failed to initialize AWS resources.")

def find_conversation(user_id: str, file_hash: str, question: str) -> Optional[Dict]:
    """
    Search for a conversation in DynamoDB matching the user, file hash, and question.

    Args:
        user_id (str): Unique ID of the user.
        file_hash (str): The file hash used as a sort key prefix.
        question (str): The question text to filter conversations.

    Returns:
        dict or None: The matching conversation item if found, otherwise None.

    Raises:
        HTTPException: If DynamoDB query fails.
    """
    try:
        response = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(file_hash),
            FilterExpression=Attr("question").eq(question)
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        logging.error(f"DynamoDB query failed: {e}")
        raise HTTPException(status_code=500, detail=f"DynamoDB query failed: {e}")
    except Exception as e:
        logging.exception("Unexpected error in find_conversation.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def delete_conversation(user_id: str, file_hash: str, question: str) -> Tuple[bool, str]:
    """
    Delete a conversation that matches the user, file hash, and question.

    Args:
        user_id (str): Unique ID of the user.
        file_hash (str): The file hash prefix to match.
        question (str): The question string to find the conversation.

    Returns:
        (bool, str): Success status and message.
    """
    match = find_conversation(user_id, file_hash, question)
    if not match:
        return False, "Conversation not found."

    try:
        conversation_table.delete_item(
            Key={
                "user_id": user_id,
                "file_hash_timestamp": match["file_hash_timestamp"],
            }
        )
        return True, "Conversation deleted successfully."
    except ClientError as e:
        logging.error(f"Failed to delete conversation: {e}")
        return False, f"Failed to delete conversation: {e}"
    except Exception as e:
        logging.exception("Unexpected error deleting conversation.")
        return False, f"Unexpected error deleting conversation: {str(e)}"

def delete_all_conversations(user_id: str, file_hash: str) -> Tuple[bool, str]:
    """
    Delete all conversations for a specific file hash belonging to the user.

    Args:
        user_id (str): Unique ID of the user.
        file_hash (str): The file hash to match as prefix in sort key.

    Returns:
        (bool, str): Success status and message.
    """
    try:
        response = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(file_hash)
        )
    except ClientError as e:
        logging.error(f"Query failed: {e}")
        return False, f"Query failed: {e}"
    except Exception as e:
        logging.exception("Unexpected error during query in delete_all_conversations.")
        return False, f"Unexpected error during query: {str(e)}"

    items = response.get("Items", [])
    if not items:
        return False, "No conversations found for this file."

    errors = []
    for item in items:
        try:
            conversation_table.delete_item(
                Key={
                    "user_id": user_id,
                    "file_hash_timestamp": item["file_hash_timestamp"],
                }
            )
        except ClientError as e:
            logging.error(f"Failed to delete conversation item: {e}")
            errors.append(str(e))
        except Exception as e:
            logging.exception("Unexpected error deleting a conversation item.")
            errors.append(f"Unexpected error: {str(e)}")

    if errors:
        return False, f"Some deletes failed: {'; '.join(errors)}"
    return True, f"Deleted {len(items)} conversations for file."

def get_all_conversations_by_file(user_id: str, file_hash: str) -> List[Dict]:
    """
    Retrieve all conversations for a given user and file.

    Args:
        user_id (str): Unique ID of the user.
        file_hash (str): The file hash used as a sort key prefix.

    Returns:
        List[dict]: A list of conversation items for the specified file.

    Raises:
        HTTPException: If the DynamoDB query fails.
    """
    try:
        response = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(file_hash)
        )
        return response.get("Items", [])
    except ClientError as e:
        logging.error(f"Failed to fetch conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {e}")
    except Exception as e:
        logging.exception("Unexpected error fetching conversations.")
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching conversations: {str(e)}")

