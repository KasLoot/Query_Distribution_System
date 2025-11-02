from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
from feishu_api import lark_writing, lark_read_and_group
from gemini_sched.lark_reader import lark_read_and_group as lark_read_and_group_sched
from gemini_sched.planning import plan

app = FastAPI()


class AssignQueryRequest(BaseModel):
    query_brief: str
    staff_member: list[str]
    query_details: str
    priority_level: int
    estimated_resolution_time: int
    source: str


@app.post("/items/assign_query/")
async def assign_query(result: AssignQueryRequest):
    print(f"Received result:\n{result}")
    lark_writing(
        query=result.query_brief,
        query_details=result.query_details,
        est_time=f"{result.estimated_resolution_time}",
        priority=result.priority_level,
        person=str.join(",", result.staff_member),
        source=result.source
    )
    print("Starting scheduling process...")
    print("Reading and grouping scheduled tasks...")
    lark_read_and_group_sched()
    print("Planning schedule...")
    plan()
    return {"message": "Query assigned successfully"}


@app.get("/items/fetch_weekly_queries/")
async def fetch_weekly_queries():
    print("Fetching weekly queries...")
    weekly_queries = lark_read_and_group()
    print(f"Weekly queries fetched: {weekly_queries}")
    
    return {"weekly_queries": weekly_queries}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

