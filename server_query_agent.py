from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
from feishu_api import lark_writing, lark_read_and_group

app = FastAPI()


class AssignQueryRequest(BaseModel):
    query_brief: str
    staff_member: list[str]
    query_details: str
    priority_level: int
    estimated_resolution_time: int


@app.post("/items/assign_query/")
async def assign_query(result: AssignQueryRequest):
    print(f"Received result:\n{result}")
    lark_writing(
        query=result.query_brief,
        est_time=f"{result.estimated_resolution_time}",
        priority=result.priority_level,
        person=result.staff_member[0]
    )
    return {"message": "Query assigned successfully"}


@app.get("/items/fetch_weekly_queries/")
async def fetch_weekly_queries():
    print("Fetching weekly queries...")
    weekly_queries = lark_read_and_group()
    print(f"Weekly queries fetched: {weekly_queries}")
    
    return {"weekly_queries": weekly_queries}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

