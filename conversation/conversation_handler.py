import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
conversation_table = dynamodb.Table("IDPConversation")


def find_conversation(user_id: str, file_hash: str, question: str) -> dict | None:
    """
    Find the conversation record matching the question for this user and file.
    """
    try:
        response = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(file_hash),
            FilterExpression=Attr("question").eq(question)
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        raise RuntimeError(f"DynamoDB query failed: {e}")


def delete_conversation(user_id: str, file_hash: str, question: str) -> tuple[bool, str]:
    """
    Find and delete a specific conversation.
    """
    match = find_conversation(user_id, file_hash, question)
    if not match:
        return False, "Conversation not found."

    try:
        conversation_table.delete_item(
            Key={
                "user_id": user_id,
                "file_hash_timestamp": match["file_hash_timestamp"]
            }
        )
        return True, "Conversation deleted successfully."
    except ClientError as e:
        return False, f"Failed to delete conversation: {e}"


def delete_all_conversations(user_id: str, file_hash: str) -> tuple[bool, str]:
    """
    Delete all conversations for a user and file_hash.
    """
    try:
        response = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("file_hash_timestamp").begins_with(file_hash)
        )
    except ClientError as e:
        return False, f"Query failed: {e}"

    items = response.get("Items", [])
    if not items:
        return False, "No conversations found for this file."

    errors = []
    for item in items:
        try:
            conversation_table.delete_item(
                Key={
                    "user_id": user_id,
                    "file_hash_timestamp": item["file_hash_timestamp"]
                }
            )
        except ClientError as e:
            errors.append(str(e))

    if errors:
        return False, f"Some deletes failed: {'; '.join(errors)}"

    return True, f"Deleted {len(items)} conversations for file."


def get_all_conversations(user_id: str) -> list[dict]:
    """
    Return all conversations for this user.
    """
    try:
        response = conversation_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        return response.get("Items", [])
    except ClientError as e:
        raise RuntimeError(f"Failed to fetch conversations: {e}")