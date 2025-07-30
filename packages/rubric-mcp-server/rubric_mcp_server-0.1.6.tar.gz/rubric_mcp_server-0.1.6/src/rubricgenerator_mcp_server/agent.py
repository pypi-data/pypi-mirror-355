
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


def create_agent(model_name, tools, model_type="openai"):
    """Create a grading agent.

    Parameters
    ----------
    model_name : str
        Identifier of the language model to use.
    tools : Sequence
        Tools the agent can invoke during execution.
    model_type : str, optional
        Provider of the model, either ``"openai"`` or ``"gemini"``. Defaults to
        ``"openai"``.

    Returns
    -------
    AgentExecutor
        Configured agent ready to evaluate student work.
    """

    # LLM 준비
    if model_type == "gemini":
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
    else:
        llm = ChatOpenAI(model=model_name, temperature=0)

    # 프롬프트 준비
    system = """
    "You are an expert educator and resource recommender. "
    "When you need external information, use the appropriate tool.\n"
    "Given a rubric and a student submission, your task is the below:\n"
     "1. Evaluate the submission based on the rubric and assign a performance level for each criterion.\n"
     "2. Summarize strengths and areas for improvement.\n"
     "3. Using the TavilySearch tool, recommend 2-3 books that match the student's grade Level, the student's performance level and topic.\n"
     "4. Provide the title, author, and a brief description for each recommendation.\n"
     "5. Please write in KOREAN "
     "6. Once you have provided all required sections, STOP reasoning and output your final answer only. Output your final answer only.\n"
     
     "Respond in the following format and show in MARKDOWNFORMAT:\n\n"
     "- Grading Table(please mention the reason of given score as well):\n\n"
     "- Feedback Summary\n\n"
     "- Book/Resource Recommendations: [title] [author] [brief description] \n\n"
     
     "Begin!\n"
    """
    eval_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Rubric:\n{rubric}\n\n"
                "Topic: {topic}\n"
                "Objective: {objective}\n"
                "Grade Level: {grade_level}\n"
                "Name: {name}\n"
                "Student Submission:\n{student_submission}\n",
            ),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, tools, eval_prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3,
    )

    return agent_executor
