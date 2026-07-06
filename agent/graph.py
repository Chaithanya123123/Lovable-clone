from dotenv import load_dotenv
from langchain_core.globals import set_verbose, set_debug
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent

from agent.prompts import planner_prompt, architect_prompt, coder_system_prompt
from agent.states import Plan, TaskPlan, CoderState
from agent.tools import write_file, read_file, get_current_directory, list_files
from agent.status import update_status, add_log, reset_status

_ = load_dotenv()

set_debug(True)
set_verbose(True)

# Using the Groq model
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.0)


def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    update_status("planner", f"Analyzing request: '{user_prompt}' and generating plan...")
    try:
        resp = llm.with_structured_output(Plan).invoke(
            planner_prompt(user_prompt)
        )
        if resp is None:
            raise ValueError("Planner did not return a valid response.")
        update_status("planner", "Project plan created successfully.", plan=resp)
        return {"plan": resp}
    except Exception as e:
        update_status("planner", f"Error in planner: {str(e)}", error=str(e), done=True)
        raise e


def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    update_status("architect", "Breaking plan down into individual implementation tasks...")
    try:
        resp = llm.with_structured_output(TaskPlan).invoke(
            architect_prompt(plan=plan.model_dump_json())
        )
        if resp is None:
            raise ValueError("Architect did not return a valid response.")

        resp.plan = plan
        update_status("architect", "Implementation steps ready.", task_plan=resp)
        return {"task_plan": resp}
    except Exception as e:
        update_status("architect", f"Error in architect: {str(e)}", error=str(e), done=True)
        raise e


def coder_agent(state: dict) -> dict:
    """LangGraph tool-using coder agent."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    total_steps = len(steps)
    
    if coder_state.current_step_idx >= total_steps:
        update_status("coder", "All implementation steps completed!", current_step=total_steps, total_steps=total_steps, done=True)
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    update_status(
        "coder", 
        f"Implementing step {coder_state.current_step_idx + 1}/{total_steps}: {current_task.task_description} ({current_task.filepath})",
        current_step=coder_state.current_step_idx,
        total_steps=total_steps
    )
    
    try:
        existing_content = read_file.invoke({"path": current_task.filepath})
    except Exception:
        existing_content = ""

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n"
        "Use write_file(path, content) to save your changes."
    )

    coder_tools = [read_file, write_file, list_files, get_current_directory]
    react_agent = create_react_agent(llm, coder_tools)

    try:
        res = react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                         {"role": "user", "content": user_prompt}]})
        
        # Log assistant messages
        for msg in res.get("messages", []):
            if msg.content:
                add_log(f"[CODER:{coder_state.current_step_idx+1}] {msg.content}")
    except Exception as e:
        update_status("coder", f"Error in coder during step {coder_state.current_step_idx + 1}: {str(e)}", error=str(e), done=True)
        raise e

    coder_state.current_step_idx += 1
    
    if coder_state.current_step_idx >= total_steps:
        update_status("coder", "All implementation steps completed successfully!", current_step=total_steps, total_steps=total_steps, done=True)
        return {"coder_state": coder_state, "status": "DONE"}
    else:
        return {"coder_state": coder_state}


graph = StateGraph(dict)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"}
)

graph.set_entry_point("planner")
agent = graph.compile()


def run_agent(user_prompt: str):
    reset_status()
    add_log(f"Starting agent run with prompt: '{user_prompt}'")
    try:
        result = agent.invoke({"user_prompt": user_prompt}, {"recursion_limit": 100})
        add_log("Agent run finished successfully!")
        return result
    except Exception as e:
        add_log(f"Agent run failed: {str(e)}")
        update_status("failed", f"Failed: {str(e)}", error=str(e), done=True)
        raise e


if __name__ == "__main__":
    import sys
    prompt = "Build a colourful modern todo app in html css and js"
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    run_agent(prompt)
