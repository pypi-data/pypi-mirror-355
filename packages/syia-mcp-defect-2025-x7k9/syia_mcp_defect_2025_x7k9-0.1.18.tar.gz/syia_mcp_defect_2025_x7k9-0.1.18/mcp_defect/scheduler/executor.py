import asyncio
# from mcp_mailProcessor.Agent.main import main
from ..Agent.main import main

async def tasker(query: str, job_id: int = None, agentName: str = None):
    print(f"Running job {job_id} with query: {query}")
    try:
        result = await main({"query": query})
        print(f"Job {job_id} completed with result: {result}")
    except Exception as e:
        print(f"Error in job {job_id}: {e}")

