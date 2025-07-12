import os

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

DYNAMODB_CONVERSATION_TABLE=os.getenv("DYNAMODB_CONVERSATION_TABLE")
AWS_REGION=os.getenv("AWS_REGION")
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
conversation_table = dynamodb.Table(DYNAMODB_CONVERSATION_TABLE)


from typing import Optional

def find_conversation(user_id: str, file_hash: str, question: str) -> Optional[dict]:
    """
    Search for a specific conversation in DynamoDB that matches the given user, file hash, and question.

    Args:
        user_id (str): Unique ID of the user.
        file_hash (str): The file hash used as a sort key prefix.
        question (str): The question text to filter conversations.

    Returns:
        dict | None: The matching conversation item if found, otherwise None.

    Raises:
        HTTPException: If DynamoDB query fails.
    """
    try:
        # Query DynamoDB using user_id and file_hash_timestamp prefix, filter by exact question.
        response = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(file_hash),
            FilterExpression=Attr("question").eq(question)
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB query failed: {e}")


def delete_conversation(user_id: str, file_hash: str, question: str) -> tuple[bool, str]:
    """
    Delete a single conversation record that matches the given user, file hash, and question.

    Args:
        user_id (str): Unique ID of the user.
        file_hash (str): The file hash prefix to match.
        question (str): The question string to find the conversation.

    Returns:
        tuple[bool, str]: (True, success message) if deleted, (False, error message) if not found or failed.
    """
    match = find_conversation(user_id, file_hash, question)
    if not match:
        return False, "Conversation not found."

    try:
        # Use the full sort key to delete the conversation
        conversation_table.delete_item(
            Key={
                "user_id": user_id,
                "file_hash_timestamp": match["file_hash_timestamp"]
            }
        )
        return True, "Conversation deleted successfully."
    except ClientError as e:
        return False, f"Failed to delete conversation: {e}"
    except Exception as e:
        return False, f"Unexpected error deleting conversation: {str(e)}"


def delete_all_conversations(user_id: str, file_hash: str) -> tuple[bool, str]:
    """
    Delete all conversations for a specific file hash belonging to the given user.

    Args:
        user_id (str): Unique ID of the user.
        file_hash (str): The file hash to match as prefix in sort key.

    Returns:
        tuple[bool, str]: (True, message) if deleted, (False, error message) if failed.
    """
    try:
        # Query all conversations with the given file hash prefix
        response = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(file_hash)
        )
    except ClientError as e:
        return False, f"Query failed: {e}"
    except Exception as e:
        return False, f"Unexpected error during query: {str(e)}"

    items = response.get("Items", [])
    if not items:
        return False, "No conversations found for this file."

    errors = []
    for item in items:
        try:
            # Delete each conversation one by one
            conversation_table.delete_item(
                Key={
                    "user_id": user_id,
                    "file_hash_timestamp": item["file_hash_timestamp"]
                }
            )
        except ClientError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")

    if errors:
        return False, f"Some deletes failed: {'; '.join(errors)}"

    return True, f"Deleted {len(items)} conversations for file."


def get_all_conversations(user_id: str) -> list[dict]:
    """
    Retrieve all conversation records for a given user.

    Args:
        user_id (str): Unique ID of the user.

    Returns:
        list[dict]: A list of conversation items.

    Raises:
        HTTPException: If the DynamoDB query fails unexpectedly.
    """
    try:
        # Query DynamoDB for all conversations where user_id matches.
        response = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        return response.get("Items", [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching conversations: {str(e)}")
    

# @app.post("/get-all-conversations")
# def get_conversations(payload: GetAllConversationsRequest):
#     user_response = requests.get("http://localhost:8000/get-user", headers={"Authorization": f"Bearer {payload.access_token}"})
#     if user_response.status_code != 200:
#         raise HTTPException(status_code=user_response.status_code, detail="Failed to retrieve user information.")
#     user = user_response.json()
#     try:
#         results = get_all_conversations(user["sub"])
#         return {
#             "conversations": results,
#             "message": "Conversations retrieved successfully."
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# @app.delete("/delete-conversation_services")
# def delete_conversation_endpoint(payload: DeleteConversationRequest):
#     user_response = requests.get("http://localhost:8000/get-user", headers={"Authorization": f"Bearer {payload.access_token}"})
#     if user_response.status_code != 200:
#         raise HTTPException(status_code=user_response.status_code, detail="Failed to retrieve user information.")
#     user = user_response.json()
#     try:
#         success, message = delete_conversation(user["sub"], payload.file_hash, payload.question)
#         if not success:
#             raise HTTPException(status_code=404, detail=message)
#         return {"message": message}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# @app.delete("/delete-all-conversations")
# def delete_all_conversation_endpoint(payload: DeleteAllConversationsRequest):
#     user_response = requests.get("http://localhost:8000/get-user", headers={"Authorization": f"Bearer {payload.access_token}"})
#     if user_response.status_code != 200:
#         raise HTTPException(status_code=user_response.status_code, detail="Failed to retrieve user information.")
#     user = user_response.json()
#     try:
#         success, message = delete_all_conversations(user["sub"], payload.file_hash)
#         if not success:
#             raise HTTPException(status_code=404, detail=message)
#         return {"message": message}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
