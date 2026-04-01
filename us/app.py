import os
import asyncio
import logging
import argparse
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from nasdaq_52wk import analyze_nasdaq100
from snp_52wk import analyze_sp500
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
        logger.info("US stock analysis job already completed successfully today. Skipping.")
        return

    if job_lock.locked():
        logger.warning("Job is already running. Skipping this trigger.")
        return

    async with job_lock:
        # Re-check inside lock
        if last_success_date == today:
            return

        logger.info("Starting US stock analysis job...")
        try:
            high_52_week_stocks, nsd100_pdf_file_name = await analyze_nasdaq100()
            if high_52_week_stocks:
                await sendMarkDownText(token=token, chat_id=chat_id, sendMessageText=high_52_week_stocks, title="NASDAQ 100 52주 신고가 종목", is_markdown=True)
            else:
                await sendMarkDownText(token=token, chat_id=chat_id, sendMessageText='NASDAQ 100 52주 신고가 종목이 없습니다.', is_markdown=True)

            high_52_week_stocks, snp500_pdf_file_name = await analyze_sp500()
            if high_52_week_stocks:
                await sendMarkDownText(token=token, chat_id=chat_id, sendMessageText=high_52_week_stocks, title="S&P 500 52주 신고가 종목", is_markdown=True)
            else:
                await sendMarkDownText(token=token, chat_id=chat_id, sendMessageText='S&P 500 52주 신고가 종목이 없습니다.', is_markdown=True)

            if nsd100_pdf_file_name:
                try: await sendMarkDownText(token=token, chat_id=chat_id, file=nsd100_pdf_file_name, title="NASDAQ 100 52주 신고가 PDF")
                except Exception as e: logger.error(f"NASDAQ PDF 전송 오류: {e}", exc_info=True)

            if snp500_pdf_file_name:
                try: await sendMarkDownText(token=token, chat_id=chat_id, file=snp500_pdf_file_name, title="S&P 500 52주 신고가 PDF")
                except Exception as e: logger.error(f"S&P 500 PDF 전송 오류: {e}", exc_info=True)
            
            last_success_date = today
            logger.info("US stock analysis job finished successfully.")
        except Exception as e:
            logger.error(f"US job execution failed: {e}", exc_info=True)
            logger.info("Job failed. It will be retried if there are more triggers scheduled.")

async def main():
    parser = argparse.ArgumentParser(description="US Stock Analysis Bot")
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
    logger.info(f"US Scheduler started. Jobs scheduled for {SCHEDULE_HOUR}:{SCHEDULE_MINUTE} (with retries at +5, +10 min).")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
