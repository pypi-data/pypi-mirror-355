from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.cron import CronTrigger
import aiosqlite
import asyncio
import os
from .executor import tasker  # tasker(query, job_id) is expected
import shutil


app_db_path = os.path.join(os.path.dirname(__file__),"database", "app_data.db")
jobstore_path = f"sqlite:///{os.path.join(os.path.dirname(__file__),"database" ,'jobs.db')}"

# APScheduler setup
scheduler = AsyncIOScheduler(
    jobstores={'default': SQLAlchemyJobStore(url=jobstore_path)},
    executors={'default': AsyncIOExecutor()}
)

# Global DB connection for aiosqlite
conn = None

# -----------------------------
# SQLite initialization
# -----------------------------
async def initialize_sqlite_db():
    os.makedirs(os.path.dirname(app_db_path), exist_ok=True)
    new_file = not os.path.exists(app_db_path)

    conn = await aiosqlite.connect(app_db_path)
    await conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = aiosqlite.Row

    if new_file:
        await conn.execute("""
            CREATE VIRTUAL TABLE docs USING fts5(
                query,
                cron,
                next_run UNINDEXED
            );
        """)
        await conn.commit()
    return conn

async def init_db():
    global conn
    conn = await initialize_sqlite_db()

# -----------------------------
# Job Store Functions
# -----------------------------
async def add_job(conn, query, cron, next_run):
    cursor = await conn.execute(
        "INSERT INTO docs (query, cron, next_run) VALUES (?, ?, ?)",
        (query, cron, next_run)
    )
    await conn.commit()
    return cursor.lastrowid

async def get_all_jobs():
    local_conn = await initialize_sqlite_db()
    cursor = await local_conn.execute("SELECT rowid, * FROM docs")
    return await cursor.fetchall()

async def delete_job(rowid):
    await conn.execute("DELETE FROM docs WHERE rowid = ?", (rowid,))
    await conn.commit()
    print(f"Deleted job {rowid} from docs")

async def update_job(arguments: dict):
    rowid = arguments.get("rowid")
    fields = []
    values = []

    for field in ["query", "cron", "next_run"]:
        if arguments.get(field) is not None:
            fields.append(f"{field} = ?")
            values.append(arguments[field])

    if not fields:
        raise ValueError("Nothing to update")
    
    values.append(rowid)
    query = f"UPDATE docs SET {', '.join(fields)} WHERE rowid = ?"
    await conn.execute(query, values)
    await conn.commit()
    print(f"Updated job {rowid}")

# -----------------------------
# Job Scheduling Logic
# -----------------------------
def is_valid_cron_expression(cron_expr):
    try:
        CronTrigger(**cron_expr)
        return True
    except Exception as e:
        print(f"Invalid cron expression: {e}")
        return False

async def start_scheduler(task_func):
    jobs = await get_all_jobs()
    for job in jobs:
        try:
            cron = eval(job["cron"]) if isinstance(job["cron"], str) else job["cron"]
            if not is_valid_cron_expression(cron):
                print(f"Skipping job {job['rowid']} due to invalid cron")
                continue

            scheduler.add_job(
                func=task_func,
                trigger="cron",
                id=str(job["rowid"]),
                start_date=job["next_run"],
                kwargs={
                    "query": job["query"],
                    "job_id": job["rowid"]
                },
                **cron
            )
            print(f"Scheduled job {job['rowid']}")
        except Exception as e:
            print(f"Failed to add job {job['rowid']}: {e}")

async def add_job_to_scheduler(query, cron_dict):
    if not is_valid_cron_expression(cron_dict):
        raise ValueError("Invalid cron expression")

    rowid = await add_job(conn, query, str(cron_dict), None)

    try:
        job = scheduler.add_job(
            func=tasker,
            trigger="cron",
            id=str(rowid),
            kwargs={
                "query": query,
                "job_id": rowid
            },
            **cron_dict
        )
        next_run = job.next_run_time
        if next_run:
            await update_job({
                "rowid": rowid,
                "next_run": str(next_run)
            })
        print(f"Added and scheduled job {rowid}")
    except Exception as e:
        await delete_job(rowid)
        raise RuntimeError(f"Failed to add job to scheduler: {e}")

async def get_all_schedules():
    jobs = scheduler.get_jobs()
    return {
        "message": "All scheduled jobs retrieved",
        "jobs": [
            {
                "id": job.id,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]
    }

# -----------------------------
# Main Entrypoint
# -----------------------------
imo_list = [9735062,9832925,

9832913,

9792058,

9677313,

9433860,

9278662,

9525194,

9629421,

9810032,

9765550,

9944974,

9796585,

9929871,

9737503,

9700146,

9928188,

9877561,

9617959,

9697909,

9916604,

9483451]
 
async def scheduler_main():
    ## delete the database folder
    path = os.path.join(os.path.dirname(__file__), "database")
    if os.path.exists(path):
        shutil.rmtree(path)
    

    await init_db()
    scheduler.start()

    

    for imo in imo_list:
        await add_job_to_scheduler(f""" For the imo {imo}, Access the “get_internal_audit_summary” tool to retrieve the latest Internal Audit (IA) overview.
Carefully review all available information, focusing on:
Key findings from the inspection
Identified issues or non-conformities
Recommended or pending actions
Past inspection details and plan for next one.
Based on your review, prepare a comprehensive summary highlighting important points, concerns, and any follow-up steps required.
Ensure all observations and conclusions are clearly documented in the casefile. 
Category is : internalAudit
 """,
{
    "minute": "30",
    "hour": "2,6",
    "day": "*",
    "month": "*",
    "day_of_week": "*"
})
        
        await add_job_to_scheduler(f""" For the imo {imo}, Access the “get_sire_reports_from_ocimf” tool to retrieve the latest SIRE inspection reports from OCIMF.
Thoroughly review all the available information, focusing on:
Key observations and findings from the inspections
Any noted deficiencies or areas of concern
Corrective actions suggested or taken
Last Inspection details and plan for next one
Based on your assessment, prepare a comprehensive summary outlining significant insights, unresolved issues, and any required follow-up actions.
Ensure all findings and recommendations are clearly documented in the casefile.
Category is : sire
 """,
 {
    "minute": "35",
    "hour": "2,6",
    "day": "*",
    "month": "*",
    "day_of_week": "*"
})
        await add_job_to_scheduler(f""" For the imo {imo}, Access the “get_vir_status_overview” tool to retrieve the latest Vessel Inspection Report (VIR) overview.
Carefully review all available information, focusing on:
Key findings from the inspection
Identified issues or non-conformities
Recommended or pending actions
Based on your review, prepare a comprehensive summary highlighting important points, concerns, and any follow-up steps required.
Ensure all observations and conclusions are clearly documented in the casefile.
Category is : vir
""",
{
    "minute": "40",
    "hour": "2,6",
    "day": "*",
    "month": "*",
    "day_of_week": "*"
})


    print("Scheduler is running. Waiting for jobs...")
    await asyncio.Event().wait() 

    
