import argparse
import asyncio

from playwright.async_api import async_playwright

from scraper2_hj3415.db import mongo, mi_history as db_mi_history, mi as db_mi
from scraper2_hj3415.scraper import mi_history, mi

PARSER_MAP = {
    'sp500': mi_history.parse_sp500,
    'kospi': mi_history.parse_kospi,
    'kosdaq': mi_history.parse_kosdaq,
    'wti': mi_history.parse_wti,
    'usdkrw': mi_history.parse_usdkrw,
    'silver': mi_history.parse_silver,
    'gold': mi_history.parse_gold,
    'gbond3y': mi_history.parse_gbond3y,
    'chf': mi_history.parse_chf,
    'aud': mi_history.parse_aud
}

COL_FUNC_MAP = {
    'sp500': db_mi_history.save_sp500_history,
    'kospi': db_mi_history.save_kospi_history,
    'kosdaq': db_mi_history.save_kosdaq_history,
    'wti': db_mi_history.save_wti_history,
    'usdkrw': db_mi_history.save_usdkrw_history,
    'silver': db_mi_history.save_silver_history,
    'gold': db_mi_history.save_gold_history,
    'gbond3y': db_mi_history.save_gbond3y_history,
    'chf': db_mi_history.save_chf_history,
    'aud': db_mi_history.save_aud_history,
}

def main():
    parser = argparse.ArgumentParser(description="Market Index Scraper CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    save_parser = subparsers.add_parser('save', help='데이터 저장 실행')
    save_subparsers = save_parser.add_subparsers(dest='mode', required=True)

    save_subparsers.add_parser('today', help="오늘 데이터 저장")

    save_history = save_subparsers.add_parser('history', help="과거 데이터 저장")
    save_history.add_argument('col', type=str, help="컬렉션 이름 [sp500, kospi, kosdaq, wti, usdkrw, silver, gold, gbond3y, chf, aud]")
    save_history.add_argument('--years', type=int, default=1, help="저장할 과거 연도 수 (기본: 1년)")

    args = parser.parse_args()

    from scraper2_hj3415.scraper.helper import ensure_playwright_installed
    ensure_playwright_installed()

    match (args.command, args.mode):
        case ('save', 'today'):
            async def parsing():
                return await mi.parse_all()

            data = asyncio.run(parsing())

            async def save(data):
                client = mongo.get_client()
                try:
                    await db_mi.save(data, client)
                finally:
                    client.close()

            asyncio.run(save(data))

        case ('save', 'history'):
            col = args.col.lower()
            parser_func = PARSER_MAP.get(col)
            if not parser_func:
                print(f"지원하지 않는 컬렉션: {col}")
                return

            async def parsing():
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    data = await parser_func(page, args.years)
                await browser.close()
                return data

            data = asyncio.run(parsing())

            save_func = COL_FUNC_MAP.get(col)
            if not save_func:
                print(f"저장 함수가 등록되지 않음: {col}")
                return

            async def save(data):
                client = mongo.get_client()
                try:
                    await save_func(data, client)
                finally:
                    client.close()

            asyncio.run(save(data))

        case _:
            print("지원하지 않는 명령입니다.")