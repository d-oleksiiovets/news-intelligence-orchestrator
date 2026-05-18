from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from src.config.logger import StatusLog
from src.ml.llm_factory import stop_llm_server

def start_scheduler(pipeline_runner, config: dict):
    scheduler = BlockingScheduler(
        executors={"default": ThreadPoolExecutor(max_workers=1)},
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 300,
        },
    )

    for task in config["tasks"]:
        trigger_type = task["trigger"]
        job_params = task["params"]
        job_id = task["id"]
        
        scheduler.add_job(
            pipeline_runner,
            trigger=trigger_type,
            args=[job_id],
            id=job_id,
            replace_existing=True,
            **job_params
        )
        
        StatusLog.info(f"Scheduler started. ID: {job_id}")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        StatusLog.info("Scheduler stopped")
    finally:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass
        stop_llm_server()
    

    