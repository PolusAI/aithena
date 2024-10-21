from aithena_services.llms.types.response import ChatResponse

def call_llm_stream(llm, messages):
    """Send chat history to the llm and update chat history with the response."""     
    
    response = llm.stream_chat(messages=messages)
    for chunk in response:
        yield chunk.delta

def call_llm(llm, messages) -> ChatResponse :
    """Send chat history to the llm and update chat history with the response."""     
    response = llm.chat(messages=messages)
    return response
