from fastapi import APIRouter, HTTPException
import logging
from app.agents.providers.geminichat import GeminiChatStateless
from app.services.milvus_multilingual_service import MilvusMultilingualService
from app.utils.langue import detect_dominant_lang, detect_lang_distribution,should_translate_to_fr,translate_to_fr_if_malagasy
from app.models.chat import ChatRequest, ChatResponse, TrainingResponse
from app.utils import group_training_metadata


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
router = APIRouter()
provider = GeminiChatStateless(model="gemini-2.5-flash")


@router.post("/search", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        translated_q = translate_to_fr_if_malagasy(req.question)
        search_results = MilvusMultilingualService().search(translated_q, req.user, req.partitions)
        reply = await provider.chat_with_rag_search(
            messages=[m.model_dump() for m in req.messages],
            user_question=req.question,
            search_results=search_results,  
            temperature=req.temperature,
            max_input_tokens=req.max_input_tokens,
            max_output_tokens=req.max_output_tokens,
            max_history_messages=req.max_messages,
        )
        return ChatResponse(reply=reply)
    except HTTPException as he:
        raise he 
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise Exception(str(e))



@router.post("/training", response_model=TrainingResponse)
async def chat(req: ChatRequest):
    try:
        translated_q = translate_to_fr_if_malagasy(req.question)
        search_results = MilvusMultilingualService().formation(translated_q)
        reply = await provider.chat_with_rag_training(
            messages=[m.model_dump() for m in req.messages],
            user_question=req.question,
            search_results=search_results,  
            temperature=req.temperature,
            max_input_tokens=req.max_input_tokens,
            max_output_tokens=req.max_output_tokens,
            max_history_messages=req.max_messages,
        )
        metas = group_training_metadata(search_results, limit_per_media=6)
        return TrainingResponse(
        reply=reply,
        sources=metas
    )
    except HTTPException as he:
        raise he 
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))
