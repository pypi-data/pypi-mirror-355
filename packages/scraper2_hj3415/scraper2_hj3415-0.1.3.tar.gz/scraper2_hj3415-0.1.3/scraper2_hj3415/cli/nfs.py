import argparse
import asyncio
from scraper2_hj3415.db import mongo
from scraper2_hj3415.db.nfs import c101, c10346, c108
from playwright.async_api import async_playwright
from scraper2_hj3415.async_ import nfs
from scraper2_hj3415.krx300 import krx300
from utils_hj3415 import tools

# 공통 맵
PARSER_MAP = {
    'c101': nfs.parse_c101,
    'c103': nfs.parse_c103,
    'c104': nfs.parse_c104,
    'c106': nfs.parse_c106,
    'c108': nfs.parse_c108,
}

COL_FUNC_MAP = {
    'c101': c101.save,
    'c103': c10346.save,
    'c104': c10346.save,
    'c106': c10346.save,
    'c108': c108.save,
}

COL_FUNC_MANY_MAP = {
    'c101': c101.save_many,
    'c103': c10346.save_many,
    'c104': c10346.save_many,
    'c106': c10346.save_many,
    'c108': c108.save_many,
}

async def parse_data(col: str, targets: list[str] | str):
    parser = PARSER_MAP.get(col)
    if not parser:
        raise ValueError(f"지원하지 않는 컬렉션: {col}")

    if isinstance(targets, str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            data = await parser(targets, page)
            await browser.close()
            return data
    else:
        return await nfs.parse_many(targets, parser)

async def save_data(col: str, data, many: bool = False):
    client = mongo.get_client()
    try:
        func_map = COL_FUNC_MANY_MAP if many else COL_FUNC_MAP
        func = func_map.get(col)
        if not func:
            raise ValueError(f"저장 함수 없음: {col}")
        result = await func(data, client)
        print(result)
    finally:
        client.close()

def handle_save_many_command(col: str, targets: list[str]):
    valid_targets = [code for code in targets if tools.is_6digit(code)]

    if not valid_targets:
        print("유효한 종목 코드가 없습니다.")
        return

    async def main():
        data = await parse_data(col, valid_targets)
        await save_data(col, data, many=True)

    asyncio.run(main())

def handle_save_command(col: str, target: str):
    if not tools.is_6digit(target):
        print(f"잘못된 코드: {target}")
        return

    async def main():
        data = await parse_data(col, target)
        await save_data(col, data, many=False)

    asyncio.run(main())

def main():
    parser = argparse.ArgumentParser(description="Naver Financial Scraper CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # save 명령
    save_parser = subparsers.add_parser('save', help='데이터 저장 실행')
    save_parser.add_argument('col', type=str, help="컬렉션 이름 (예: c101, c103, c104, c016, c108)")
    save_parser.add_argument('targets', nargs='*', help="종목코드 (예: 005930, 000660... and all)")

    args = parser.parse_args()
    col = args.col.lower()

    if args.command == 'save':
        if len(args.targets) == 1 and args.targets[0].lower() == "all":
            handle_save_many_command(col, krx300.get_codes())
        elif len(args.targets) == 1:
            handle_save_command(col, args.targets[0])
        else:
            handle_save_many_command(col, args.targets)

