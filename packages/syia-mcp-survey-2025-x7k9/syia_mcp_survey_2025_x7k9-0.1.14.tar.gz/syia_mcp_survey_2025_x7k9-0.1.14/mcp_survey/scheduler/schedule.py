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
async def scheduler_main():
    await init_db()
    scheduler.start()

#     await add_job_to_scheduler("""For the vessel with imo 9930923, Access the “get_class_survey_report” tool to find the latest Class Survey Status Report along with the link to access the document. 
# Then proceed to:
# Use “get_class_certificate_status” to review the status of all statutory certificates.
# Use “get_class_survey_status” to check the current status of statutory class surveys.
# Use “get_coc_notes_memo_status” to verify if the vessel has any active Conditions of Class (CoC) or Notes/Memos.
# Use “get_cms_items_status” to assess the condition and due status of Continuous Survey of Machinery (CMS) items.
# Use “get_next_periodical_survey_details” to assess the details of next periodical survey.
# Once the above data points have been reviewed, access the “certificate_table_search” tool for more details on each of above.
# Conduct a comprehensive review of all gathered information and clearly document your findings and observations in the casefile.""",
# {
#         "minute": "*/1",
#         "hour": "*",
#         "day": "*",
#         "month": "*",
#         "day_of_week": "*"
#     })
    

    print("Scheduler is running. Waiting for jobs...")
    await asyncio.Event().wait()


async def scheduler_main():
    ## delete the database folder
    path = os.path.join(os.path.dirname(__file__), "database")
    if os.path.exists(path):
        shutil.rmtree(path)
    

    await init_db()
    scheduler.start()
    imo_list = [9832925,

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
 
    
    for imo in imo_list:
        await add_job_to_scheduler(f"""For the vessel with imo {imo}, Survey And Certificates:
Access the “get_class_survey_report” tool to find the latest Class Survey Status Report along with the link to access the document.
 Then proceed to:
Use “get_class_certificate_status” to review the status of all statutory certificates.
Use “get_class_survey_status” to check the current status of statutory class surveys.
Use “get_coc_notes_memo_status” to verify if the vessel has any active Conditions of Class (CoC) or Notes/Memos.
Use “get_cms_items_status” to assess the condition and due status of Continuous Survey of Machinery (CMS) items.
Use “get_next_periodical_survey_details” to assess the details of the next periodical survey.
Once the above data points have been reviewed, access the “certificate_table_search” tool for more details on each of the above. 
Conduct a comprehensive review of all gathered information and clearly document your findings and observations in the casefile daily at 0900 Hrs.
Once the casefile is created, the next day add information in the casefile only if there is any change. If all information is the same as the previous day, there is no need to update anything, but the link for Class survey status report should be renewed with the latest one.
Category is : classSurveyAndCertificateStatus
 """,
{
    "minute": "30",
    "hour": "2,6",
    "day": "*",
    "month": "*",
    "day_of_week": "*"
})

    print("Scheduler is running. Waiting for jobs...")
    await asyncio.Event().wait()      