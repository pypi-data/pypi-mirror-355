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
    ## delete the database folder
    path = os.path.join(os.path.dirname(__file__), "database")
    if os.path.exists(path):
        shutil.rmtree(path)
    

    await init_db()
    scheduler.start()
    imo_list = [9721932,
9729489,
9729477,
9722015,
9490624,
9490636,
9557123,
9490662,
9490698,
9758129,
9714678,
9707699,
9368871,
9923334,
9490686,
9705976,
9707364,
9923205,
9714680,
9301720]
    
    # for imo in imo_list:
#         await add_job_to_scheduler(f""" For the imo {imo}, Begin by accessing the following tools to gather comprehensive information about the vessel’s current voyage:
# “get_vessel_eta_cargo_activity”
# “position_book_report_from_shippalm”
# “get_voyage_details_from_shippalm”
# “get_vessel_live_position_and_eta”
# Review the vessel’s schedule, cargo details, weather updates, and other relevant voyage information from these sources.
# Next, assess the vessel’s fuel and lube oil status by using:
# “Get_vessel_fuel_consumption/ROB” – for fuel consumption trends and remaining onboard (ROB) quantities
# “get_me_cylinder_oil_consumption_and_rob” – for Main Engine cylinder oil usage and ROB
# “get_mecc_aecc_consumption_and_rob” – for Main Engine Control and Auxiliary Engine Control oil consumption and ROB
# Then, access “get_fresh_water_production_consumption_and_rob” to analyze fresh water production, usage, and onboard reserves.
# Finally, use “get_charter_party_compliance_status” to evaluate the vessel’s compliance with Charter Party voyage instructions.
# After reviewing all the above data, prepare a comprehensive summary of key findings, discrepancies, and any actions required. Clearly document everything in the casefile.
#  """,
# {
#     "minute": "*",
#     "hour": "1,12",
#     "day": "*",
#     "month": "*",
#     "day_of_week": "*"
# })


    print("Scheduler is running. Waiting for jobs...")
    await asyncio.Event().wait()     