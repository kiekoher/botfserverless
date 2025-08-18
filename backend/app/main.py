from fastapi import FastAPI, Depends, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.core.use_cases.process_chat_message import ProcessChatMessage
from app.dependencies import get_process_chat_message_use_case

app = FastAPI(
    title="Crezgo AI Backend",
    description="Backend for Crezgo AI services using Clean Architecture.",
    version="1.0.0",
)


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    process_message_use_case: ProcessChatMessage = Depends(
        get_process_chat_message_use_case
    ),
):
    """
    Main chat endpoint. Receives a user query and returns a bot response.
    """
    try:
        bot_response_text = await process_message_use_case.execute(
            user_id=request.user_id,
            user_query=request.query,
            history=request.conversation_history or [],
        )
        return ChatResponse(response=bot_response_text, user_id=request.user_id)
    except Exception as e:
        # In a real app, you'd have more specific error handling
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"status": "ok"}
