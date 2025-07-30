from mcp.server.fastmcp import FastMCP
from .rubric_app import RubricApp
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

MODEL_TYPE = os.getenv("MODEL_TYPE", "openai")  # 기본값 openai # "gemini"  # openai
MODEL_NAME = os.getenv(
    "MODEL_NAME", "gpt-4o-mini"
)  # 기본값 "gpt-4o-mini" # "gemini-2.0-flash"


mcp = FastMCP("rubric-mcp-server")


# @mcp.tool()
# def generate_rubric_feedback(
#     topic: str,
#     objective: str,
#     grade_level: str,
#     name: Optional[str],
#     student_submission: Optional[str],
# ) -> dict:


@mcp.tool()
def generate_rubric_feedback(**data) -> Dict[str, str]:
    """
    Generate rubric standards and grading feedback for a student's assignment in Korean.

    If `student_submission` and 'name' is not provided or is empty, only the rubric standards
    will be generated; no grading feedback will be returned.

    Parameters:
        topic (str): The subject or topic of the assignment.
        objective (str): The learning objective or goal.
        grade_level (str): The student's grade level.
        name (Optional[str]): The student's name.
        student_submission (Optional[str]): The student's submitted work. If None or an empty string,
            only rubric standards will be produced.

    Returns:
        dict:
            {
                "rubric_standards": str,   # Generated rubric standards
                "grading_feedback": str    # Generated feedback (empty if no submission)
            }
    """

    # real_data = data.get("data", data)

    app = RubricApp(**data)

    # app = RubricApp(
    #     topic=topic,
    #     objective=objective,
    #     grade_level=grade_level,
    #     name=name,
    #     student_submission=student_submission,
    #     )
    return {
        "rubric_standards": app.get_rubric_standards(),
        "grading_feedback": app.get_grading_feedback(),
    }


def main():
    """MCP 서버를 stdio 모드로 실행합니다."""
    print("Starting MCP server for RubricApp…")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
