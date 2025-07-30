import argparse
import asyncio
from scraper2_hj3415.db import mongo
from scraper2_hj3415.db.nfs import c101, c10346, c108
from playwright.async_api import async_playwright
from scraper2_hj3415.scraper import nfs
from scraper2_hj3415.krx300 import krx300
from utils_hj3415 import tools
import pandas as pd

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

async def parse_data(col: str, target: str) -> dict | pd.DataFrame | None:
    parser = PARSER_MAP.get(col)
    if not parser:
        raise ValueError(f"지원하지 않는 컬렉션: {col}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        data = await parser(target, page)
        await browser.close()
        return data

async def save_data(col: str, target: str, data: dict | pd.DataFrame | None):
    client = mongo.get_client()
    try:
        func = COL_FUNC_MAP.get(col)
        if not func:
            raise ValueError(f"저장 함수 없음: {col}")

        match col:
            case "c101":
                result = await func(data, client)
            case "c103" | "c104" | "c106":
                result = await func(col, target, data, client)
            case "c108":
                result = await func(target, data, client)
            case _:
                raise ValueError(f"알 수 없는 컬렉션: {col}")
        print(result)
    finally:
        client.close()


async def parse_many_data(col: str, targets: list[str] | str) ->  dict[str, dict | dict[str, pd.DataFrame] | pd.DataFrame | None]:
    parser = PARSER_MAP.get(col)
    if not parser:
        raise ValueError(f"지원하지 않는 컬렉션: {col}")

    return await nfs.parse_many(targets, parser)


async def save_many_data(col: str, many_data: dict[str, dict | dict[str, pd.DataFrame] | pd.DataFrame | None]):
    client = mongo.get_client()
    try:
        func = COL_FUNC_MANY_MAP.get(col)
        if not func:
            raise ValueError(f"저장 함수 없음: {col}")

        match col:
            case "c101" | 'c108':
                result = await func(many_data, client)
            case "c103" | "c104" | "c106":
                result = await func(col, many_data, client)
            case _:
                raise ValueError(f"알 수 없는 컬렉션: {col}")
        print(result)
    finally:
        client.close()


def handle_save_many_command(col: str, targets: list[str]):
    valid_targets = [code for code in targets if tools.is_6digit(code)]

    if not valid_targets:
        print("유효한 종목 코드가 없습니다.")
        return

    async def main():
        many_data = await parse_many_data(col, valid_targets)
        await save_many_data(col, many_data)

    asyncio.run(main())

def handle_save_command(col: str, target: str):
    if not tools.is_6digit(target):
        print(f"잘못된 코드: {target}")
        return

    async def main():
        data = await parse_data(col, target)
        await save_data(col, target, data)

    asyncio.run(main())

def main():
    parser = argparse.ArgumentParser(description="Naver Financial Scraper CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # save 명령
    save_parser = subparsers.add_parser('save', help='데이터 저장 실행')
    save_parser.add_argument('col', type=str, help="컬렉션 이름 (예: c101, c103, c104, c106, c108)")
    save_parser.add_argument('targets', nargs='*', help="종목코드 (예: 005930, 000660... and all)")

    args = parser.parse_args()
    col = args.col.lower()

    from scraper2_hj3415.scraper.helper import ensure_playwright_installed
    ensure_playwright_installed()

    if args.command == 'save':
        if len(args.targets) == 1 and args.targets[0].lower() == "all":
            handle_save_many_command(col, krx300.get_codes())
        elif len(args.targets) == 1:
            handle_save_command(col, args.targets[0])
        else:
            handle_save_many_command(col, args.targets)

