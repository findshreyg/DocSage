from pydantic import BaseModel

class DeleteConversationRequest(BaseModel):
    """
    Schema for deleting a specific conversation.
    """
    file_hash: str
    question: str

class DeleteAllConversationsRequest(BaseModel):
    """
    Schema for deleting all conversations for a file.
    """
    file_hash: str

class GetAllConversationsPerUserPerFile(BaseModel):
    """
    Schema for retrieving all conversations for a user/file.
    """
    file_hash: str

class FindConversationRequest(BaseModel):
    """
    Schema for finding a conversation given a file hash and question.
    """
    file_hash: str
    question: str
