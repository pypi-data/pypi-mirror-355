from typing import AsyncGenerator, Dict, List, Optional, Union
import logging

from pydantic import BaseModel


class StepsUpdateEvent(BaseModel):
    """
    for step in steps:
        print("Description:", step.get("description", ""))
        print("Status:", step.get("status", ""))
        print("Updates:", step.get("updates", ""))
    """

    steps: List = []


class OnNodeStreamEvent(BaseModel):
    chunk: str


class ChatModelEndEvent(BaseModel):
    """
    Chat Model End Event 資料模型
    儲存從 on_chat_model_end 事件擷取的資料
    """
    ai_message_outputs: str = ""
    usage_metadata: Dict = {}
    model_name: str = ""
    inputs: list[str] = []
    langgraph_node: str = ""


MAX_RECURSION_LIMIT = 25


# graph 是 CompiledStateGraph，不傳入型別的原因是，loading import 需要 0.5秒
async def langgraph_runner(
    thread_id: str,
    init_state: dict,
    graph,
    need_resume: bool = False,
    extra_config: Optional[Dict] = None,
) -> AsyncGenerator:
    invoke_state = init_state
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_RECURSION_LIMIT,
    }
    if extra_config:
        config["configurable"].update(extra_config)
    if need_resume:
        state_history = []
        async for state in graph.aget_state_history(config):
            state_history.append(state)

        # 如果 state_history 的長度超過 MAX_RECURSION_LIMIT，動態調整 recursion_limit
        if len(state_history) > MAX_RECURSION_LIMIT:
            # 計算超出的倍數
            multiplier = (len(state_history) - 1) // MAX_RECURSION_LIMIT
            # 設定新的 recursion_limit 為 (multiplier + 1) * MAX_RECURSION_LIMIT
            config["recursion_limit"] = (multiplier + 1) * MAX_RECURSION_LIMIT

    async for event in graph.astream_events(
        invoke_state,
        config,
        version="v2",
    ):
        # state = await graph.aget_state(config)
        # print(state.config)

        yield event


# graph 是 CompiledStateGraph，不傳入型別的原因是，loading import 需要 0.5秒
async def agent_runner(
    thread_id: str,
    init_state: dict,
    graph,
    need_resume: bool = False,
    extra_config: Optional[Dict] = None,
) -> AsyncGenerator[Union[StepsUpdateEvent, OnNodeStreamEvent, ChatModelEndEvent], None]:
    invoke_state = init_state
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_RECURSION_LIMIT,
    }
    if extra_config:
        config["configurable"].update(extra_config)
    if need_resume:
        state_history = []
        async for state in graph.aget_state_history(config):
            state_history.append(state)

        # 如果 state_history 的長度超過 MAX_RECURSION_LIMIT，動態調整 recursion_limit
        if len(state_history) > MAX_RECURSION_LIMIT:
            # 計算超出的倍數
            multiplier = (len(state_history) - 1) // MAX_RECURSION_LIMIT
            # 設定新的 recursion_limit 為 (multiplier + 1) * MAX_RECURSION_LIMIT
            config["recursion_limit"] = (multiplier + 1) * MAX_RECURSION_LIMIT

    async for event in graph.astream_events(
        invoke_state,
        config,
        version="v2",
    ):
        if event["event"] == "on_chain_end":
            pass
        if event["event"] == "on_chat_model_end":
            data = event.get("data", {})
            logging.info(f"[Agent Runner] on_chat_model_end data: {data}")
            metadata = event.get("metadata", {})
            langgraph_node = metadata.get("langgraph_node", {})

            # 擷取 output 資料
            output = data.get("output", {})
            ai_message_outputs = ""
            usage_metadata = {}
            model_name = ""
            
            # 根據 langgraph_node 決定如何處理 output
            if langgraph_node == 'extract':
                # extract：從 tool_calls 中提取 has_requirement
                try:
                    for tool_call in output.tool_calls:
                        if tool_call.get('name') == 'RequirementPromptInstructions':
                            args = tool_call.get('args', {})
                            ai_message_outputs = str(args)
                            break
                except Exception as e:
                    logging.error(f"[collect log info {langgraph_node}] Failed to extract args: {e}")
                        
            elif langgraph_node in ['search_node', 'normal_chat_node']:
                # search_node 或 normal_chat_node：從content取得AI回覆
                if hasattr(output, 'content'):
                    ai_message_outputs = str(output.content)
                    
            elif langgraph_node == 'related_node':
                # related_node：從 tool_calls 中提取 related_questions
                try:
                    if hasattr(output, 'additional_kwargs') and 'tool_calls' in output.additional_kwargs:
                        tool_calls = output.additional_kwargs['tool_calls']
                        for tool_call in tool_calls:
                            if tool_call.get('function', {}).get('name') == 'RelatedQuestionsInstructions':
                                import json
                                arguments = json.loads(tool_call['function']['arguments'])
                                related_questions = arguments.get('related_questions', [])
                                ai_message_outputs = '; '.join(related_questions)
                                break
                except Exception as e:
                    logging.error(f"[collect log info {langgraph_node}] Failed to extract related_questions: {e}")
                
            if hasattr(output, 'usage_metadata'):
                usage_metadata = output.usage_metadata if output.usage_metadata else {}

            if hasattr(output, 'response_metadata'):
                model_name = output.response_metadata.get('model_name', '')
            
            # 擷取 input 資料
            input_data = data.get("input", {})
            inputs = []
            
            if 'messages' in input_data:
                messages = input_data['messages']
                
                # 收集所有訊息並分類
                ai_messages = []
                human_messages = []
                system_messages = []
                
                for msg in messages:
                    for nested_msg in msg:
                        if hasattr(nested_msg, '__class__'):
                            msg_type = nested_msg.__class__.__name__
                            msg_content = str(getattr(nested_msg, 'content', ''))
                            
                            if msg_type == 'AIMessage':
                                ai_messages.append(msg_content)
                            elif msg_type == 'HumanMessage':
                                human_messages.append(msg_content)
                            elif msg_type == 'SystemMessage':
                                system_messages.append(msg_content)
                
                inputs.extend(ai_messages)
                inputs.extend(human_messages) 
                inputs.extend(system_messages)

            chat_model_end_event = ChatModelEndEvent(
                ai_message_outputs=ai_message_outputs,
                usage_metadata=usage_metadata,
                model_name=model_name,
                inputs=inputs,
                langgraph_node=langgraph_node,
            )
            yield chat_model_end_event
        if event["event"] == "on_chat_model_stream":
            data = event["data"]
            if (
                data["chunk"].content
                and isinstance(data["chunk"].content[0], dict)
                and data["chunk"].content[0].get("text", "")
            ):
                yield OnNodeStreamEvent(chunk=data["chunk"].content[0].get("text", ""))
            elif data["chunk"].content and isinstance(data["chunk"].content, str):
                yield OnNodeStreamEvent(chunk=data["chunk"].content)


# def handle_copilotkit_intermediate_state(event: dict):
#     print("Handling copilotkit intermediate state")
#     copilotkit_intermediate_state = event["metadata"].get(
#         "copilotkit:emit-intermediate-state"
#     )
#     print(f"Intermediate state: {copilotkit_intermediate_state}")
#     if copilotkit_intermediate_state:
#         for intermediate_state in copilotkit_intermediate_state:
#             if intermediate_state.get("state_key", "") == "steps":
#                 for tool_call in event["data"]["output"].tool_calls:
#                     if tool_call.get("name", "") == intermediate_state.get("tool", ""):
#                         steps = tool_call["args"].get(
#                             intermediate_state.get("tool_argument")
#                         )
#                         print(f"Yielding steps: {steps}")
#                         yield StepsUpdateEvent(steps=steps)
#     print("--------------------------------")
