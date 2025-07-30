from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
from rubricgenerator_mcp_server.rubric_app import RubricApp
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()


# 1) FastAPI 앱 인스턴스 생성
app = FastAPI()

# 2) MCP 인스턴스 생성 (FastAPI 앱에 붙임)
mcp = FastMCP(server_name="rubric-mcp-server", app=app)


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

    app = RubricApp(**data)

    return {
        "rubric_standards": app.get_rubric_standards(),
        "grading_feedback": app.get_grading_feedback(),
    }


@app.get("/", tags=["health"])
def read_root():
    return {"status": "ok", "message": "Rubric MCP Server is running"}


def main():
    """STDIO 모드로 MCP 서버 실행"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
