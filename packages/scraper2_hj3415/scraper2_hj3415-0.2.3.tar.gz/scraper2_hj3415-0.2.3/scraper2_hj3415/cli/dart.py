import argparse
import json
from scraper2_hj3415.scraper import dart
#from db_hj3415 import mymongo, myredis

def save_today_darts(data_from_file=False) -> int:
    """
    오늘 공시 데이터를 수집해서 후처리 후 MongoDB에 저장한다.
    :param data_from_file: JSON 파일에서 데이터 불러오기 (디버깅용)
    :return: 저장된 총 공시 개수
    """
    if data_from_file:
        print(f"공시 데이터를 {dart.OverView.SAVE_FILENAME} 파일에서 가져옵니다.")
        with open(dart.OverView.SAVE_FILENAME, 'r') as file:
            raw_data = json.load(file)
    else:
        raw_data = dart.OverView().get(save_to_file=True)

    print(f"총 {len(raw_data)}개의 데이터가 수집되었습니다.")
    data = dart.PostProcess.all_in_one(raw_data)
    print("원본 데이터에서 후처리를 시행합니다...")

    # Redis에 저장
    myredis.DartToday().save(data)
    print(f"총 {len(data)}개의 공시를 redis_name : dart_today에 저장했습니다.")

    # MongoDB에 저장
    for item in data:
        code = item['stock_code']
        name = item['corp_name']
        report_name = item['report_nm']
        print(f'{code}/{name}의 dart 테이블에 {report_name} 공시를 저장합니다.')
        mymongo.Dart.save(code, item)

        print(f'\tredis_name : {code}_dart_get_recent_date를 갱신합니다.')
        try:
            myredis.Dart(code).get_recent_date(refresh=True)
        except Exception as e:
            print(f'\t❌ Redis 갱신 실패: {e}')

    print(f"총 {len(data)}개의 공시를 MongoDB에 저장했습니다.")
    return len(data)

def main():
    parser = argparse.ArgumentParser(description="Dart Commands")
    subparsers = parser.add_subparsers(dest='command', help='명령어')

    save_parser = subparsers.add_parser('save', help='공시 저장')
    save_parser.add_argument('--force', action='store_true', help='캐시 사용 없이 강제 재계산')
    save_parser.add_argument('--from-file', action='store_true', help='파일에서 JSON 데이터를 불러옴')

    args = parser.parse_args()

    match args.command:
        case 'save':
            try:
                save_today_darts(data_from_file=args.from_file)
            except Exception as e:
                print(f'실행 중 오류 발생: {e}')
        case _:
            parser.print_help()
