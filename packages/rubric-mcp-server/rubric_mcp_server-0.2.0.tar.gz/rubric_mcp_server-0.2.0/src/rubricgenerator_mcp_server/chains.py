from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Literal
from pydantic import BaseModel, Field


def create_rubric_chain(model_name, model_type="openai"):
    """Create a chain that generates rubrics.

    Parameters
    ----------
    model_name : str
        Identifier of the language model to use.
    model_type : str, optional
        Provider of the model, either ``"openai"`` or ``"gemini"``. Defaults to
        ``"openai"``.

    Returns
    -------
    Runnable
        LangChain runnable that produces a rubric in markdown format.
    """

    # LLM 준비
    if model_type == "gemini":
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
    else:
        llm = ChatOpenAI(model=model_name, temperature=0)

    # PromptTemplate
    system = "You are an expert in educational assessment and rubric design in Korean."

    rubric_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Generate a detailed rubric in markdown format for the following assessment:\n"
                "topic: {topic}\n"
                "objective: {objective}\n"
                "grade Level: {grade_level}\n"
                "Provide criteria, levels, and sample answers.",
            ),
        ]
    )

    # define Rubric chain
    rubric_generator = rubric_prompt | llm | StrOutputParser()
    return rubric_generator




class SubmissionChecker(BaseModel):
    binary_score: Literal["yes", "no"] = Field(
        ...,
        description="Given a user question, if there is student's submission, return 'yes', otherwise return 'no'",
    )


def create_submission_checker(model_name, model_type="openai") -> str:
    # initialize the LLM
    llm = ChatOpenAI(model=model_name, temperature=0)
    # LLM 준비
    if model_type == "gemini":
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
    else:
        llm = ChatOpenAI(model=model_name, temperature=0)

    sub_checker = llm.with_structured_output(SubmissionChecker)

    system = (
        """Your task is to check if there is student's submission in user's input"""
    )

    checker_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "student submission: \n\n {student_submission}",
            ),
        ]
    )

    # Build submission checker
    submission_checker = checker_prompt | sub_checker

    return submission_checker
