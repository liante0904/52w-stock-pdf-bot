import os
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Import utilities once they are available for KR
# from kr_52wk import analyze_kr
from utils.telegram_util import sendMarkDownText

from datetime import date

load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN_REPORT_ALARM')
chat_id = os.getenv('TELEGRAM_CHANNEL_ID_STOCK_INDICATOR')
SCHEDULE_HOUR = os.getenv('SCHEDULE_HOUR', '08')
SCHEDULE_MINUTE = os.getenv('SCHEDULE_MINUTE', '00')

job_lock = asyncio.Lock()
last_success_date = None

async def job():
    global last_success_date
    today = date.today()

    if last_success_date == today:
        print(f"Job for {today} already completed successfully. Skipping.")
        return

    if job_lock.locked():
        print("Job is already running. Skipping this trigger.")
        return

    async with job_lock:
        print("Starting KR stock analysis job...")
        try:
            # Placeholder for KR analysis logic
            print("KR analysis logic goes here.")
            
            last_success_date = today
            print(f"KR stock analysis job finished successfully for {today}.")
        except Exception as e:
            print(f"KR job execution failed: {e}")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(job, 'cron', hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE)
    scheduler.start()
    
    print(f"KR Scheduler started. Job scheduled for {SCHEDULE_HOUR}:{SCHEDULE_MINUTE} daily.")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
