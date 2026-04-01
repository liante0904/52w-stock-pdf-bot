import os
import asyncio
import logging
import argparse
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from nikkei_52wk import analyze_nikkei225
from topix_52wk import analyze_topix
from utils.telegram_util import sendMarkDownText

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN_REPORT_ALARM')
chat_id = os.getenv('TELEGRAM_CHANNEL_ID_STOCK_INDICATOR')
SCHEDULE_HOUR = int(os.getenv('SCHEDULE_HOUR', 8))
SCHEDULE_MINUTE = int(os.getenv('SCHEDULE_MINUTE', 0))

job_lock = asyncio.Lock()
last_success_date = None

async def job():
    global last_success_date
    today = date.today()

    if last_success_date == today:
        logger.info("JP stock analysis job already completed successfully today. Skipping.")
        return

    if job_lock.locked():
        logger.warning("Job is already running. Skipping this trigger.")
        return

    async with job_lock:
        # Re-check inside lock
        if last_success_date == today:
            return

        logger.info("Starting JP stock analysis job...")
        try:
            # Analyze nikkei225
            high_52_week_stocks, nikkei225_pdf_file_name = await analyze_nikkei225()
            if high_52_week_stocks:
                await sendMarkDownText(token=token, chat_id=chat_id, sendMessageText=high_52_week_stocks, title="Nikkei225 52주 신고가 종목", is_markdown=True)
            else:
                await sendMarkDownText(token=token, chat_id=chat_id, sendMessageText='Nikkei225 52주 신고가 종목이 없습니다.', is_markdown=True)
            
            # Analyze topix
            high_52_week_stocks, topix_pdf_file_name = await analyze_topix()
            if high_52_week_stocks:
                await sendMarkDownText(token=token, chat_id=chat_id, sendMessageText=high_52_week_stocks, title="TOPIX 52주 신고가 종목", is_markdown=True)
            else:
                await sendMarkDownText(token=token, chat_id=chat_id, sendMessageText='TOPIX 52주 신고가 종목이 없습니다.', is_markdown=True)

            # PDF 파일 전송
            if nikkei225_pdf_file_name:
                try: await sendMarkDownText(token=token, chat_id=chat_id, file=nikkei225_pdf_file_name, title="Nikkei225 52주 신고가 PDF")
                except Exception as e: logger.error(f"Nikkei225 PDF 전송 오류: {e}", exc_info=True)
            if topix_pdf_file_name:
                try: await sendMarkDownText(token=token, chat_id=chat_id, file=topix_pdf_file_name, title="TOPIX 52주 신고가 PDF")
                except Exception as e: logger.error(f"TOPIX PDF 전송 오류: {e}", exc_info=True)
            
            last_success_date = today
            logger.info("JP stock analysis job finished successfully.")
        except Exception as e:
            logger.error(f"JP job execution failed: {e}", exc_info=True)
            logger.info("Job failed. It will be retried if there are more triggers scheduled.")


async def main():
    parser = argparse.ArgumentParser(description="JP Stock Analysis Bot")
    parser.add_argument('--now', action='store_true', help='Run the job immediately and exit')
    args = parser.parse_args()

    if args.now:
        logger.info("Immediate execution requested via --now flag.")
        await job()
        return

    scheduler = AsyncIOScheduler()
    # 기본 스케줄 및 5분 뒤, 10분 뒤 재시도 스케줄 추가
    for offset in [0, 5, 10]:
        minute = (SCHEDULE_MINUTE + offset) % 60
        hour = (SCHEDULE_HOUR + (SCHEDULE_MINUTE + offset) // 60) % 24
        scheduler.add_job(job, 'cron', hour=hour, minute=minute)
    
    scheduler.start()
    logger.info(f"JP Scheduler started. Jobs scheduled for {SCHEDULE_HOUR}:{SCHEDULE_MINUTE} (with retries at +5, +10 min).")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
