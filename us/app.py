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

# "07:30,15:40" 형식의 환경 변수 지원
SCHEDULE_TIMES_STR = os.getenv('SCHEDULE_TIMES', '08:00')
SCHEDULE_TIMES = []
for t in SCHEDULE_TIMES_STR.split(','):
    try:
        h, m = map(int, t.strip().split(':'))
        SCHEDULE_TIMES.append((h, m))
    except ValueError:
        logger.error(f"Invalid schedule format: {t}")

job_lock = asyncio.Lock()
# 날짜와 시간대(slot)를 조합하여 성공 여부 관리
last_success_slots = set()

async def job(slot_id=None):
    global last_success_slots
    today = date.today()
    # slot_id는 "07:30" 같은 형식
    success_key = f"{today}-{slot_id}" if slot_id else None

    if success_key and success_key in last_success_slots:
        logger.info(f"US stock analysis job for slot {slot_id} already completed today. Skipping.")
        return

    if job_lock.locked():
        logger.warning("Job is already running. Skipping this trigger.")
        return

    async with job_lock:
        if success_key and success_key in last_success_slots:
            return

        logger.info(f"Starting US stock analysis job{' for slot ' + slot_id if slot_id else ''}...")
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
            
            if success_key:
                last_success_slots.add(success_key)
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
    
    for h, m in SCHEDULE_TIMES:
        slot_id = f"{h:02d}:{m:02d}"
        # 각 스케줄별로 기본 시간 및 5분, 10분 뒤 재시도 스케줄 추가
        for offset in [0, 5, 10]:
            curr_m = (m + offset) % 60
            curr_h = (h + (m + offset) // 60) % 24
            scheduler.add_job(job, 'cron', hour=curr_h, minute=curr_m, args=[slot_id])
    
    scheduler.start()
    logger.info(f"US Scheduler started. Registered slots: {SCHEDULE_TIMES_STR} (with retries).")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
