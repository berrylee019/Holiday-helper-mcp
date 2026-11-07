"""공휴일·연휴 도우미 테스트 (특일 정보는 모의값. 기대값은 달력을 손으로 세어 정함: python -m unittest test_main -v)"""
import os
import unittest
from datetime import date

import main

H2026 = {date(2026, 1, 1): "1월1일", date(2026, 2, 16): "설날", date(2026, 2, 17): "설날", date(2026, 2, 18): "설날",
         date(2026, 3, 2): "대체공휴일", date(2026, 5, 5): "어린이날", date(2026, 5, 25): "대체공휴일",
         date(2026, 6, 3): "전국동시지방선거", date(2026, 8, 17): "대체공휴일",
         date(2026, 9, 24): "추석", date(2026, 9, 25): "추석", date(2026, 9, 26): "추석", date(2026, 9, 28): "대체공휴일",
         date(2026, 10, 3): "개천절", date(2026, 10, 5): "대체공휴일", date(2026, 10, 9): "한글날", date(2026, 12, 25): "기독탄신일"}
H2026[date(2026, 3, 1)] = "3·1절"   # 일요일 + 월요일 대체공휴일 조합


class Base(unittest.TestCase):
    def setUp(self):
        self._o = main.fetch_year
        main.fetch_year = lambda y: dict(H2026) if y == 2026 else {}

    def tearDown(self):
        main.fetch_year = self._o


class Blocks(unittest.TestCase):
    def test_blocks_and_bridges(self):
        b = main.off_blocks(date(2026, 2, 10), date(2026, 2, 28), H2026)
        self.assertEqual(b[0], (date(2026, 2, 14), date(2026, 2, 18)))   # 토 일 월화수(설날)
        self.assertEqual(main.block_len(b[0]), 5)
        self.assertEqual(b[1], (date(2026, 2, 21), date(2026, 2, 22)))
        br = main.bridges(b, H2026, 2)
        self.assertEqual(len(br), 1)
        self.assertEqual((br[0]["start"], br[0]["end"], br[0]["leave"], br[0]["total"]),
                         (date(2026, 2, 14), date(2026, 2, 22), 2, 9))

    def test_bridge_requires_holiday(self):
        blocks = main.off_blocks(date(2026, 7, 1), date(2026, 7, 31), H2026)   # 주말만 있는 달
        self.assertEqual(main.bridges(blocks, H2026, 3), [])


class Holidays(Base):
    def test_month_and_year(self):
        r = main.get_holidays(2026, 10)
        self.assertIn("2026-10-03(토) 개천절", r)
        self.assertIn("2026-10-05(월) 대체공휴일", r)
        self.assertIn("2026-10-09(금) 한글날", r)
        self.assertNotIn("설날", r)
        self.assertIn("출처: 한국천문연구원", r)
        self.assertIn("2026년 10월 공휴일 (3일)", r)
        self.assertIn("해당 월에는 공휴일이 없습니다", main.get_holidays(2026, 7))

    def test_unpublished(self):
        self.assertTrue(main.get_holidays(2027).startswith("[입력 확인]"))


class Next(Base):
    def test_next(self):
        r = main.get_next_holiday("2026-11-06")
        self.assertIn("2026-12-25(금) 기독탄신일 — D-49", r)
        r2 = main.get_next_holiday("2026-12-25")
        self.assertIn("오늘", r2)
        self.assertTrue(main.get_next_holiday("2026-12-26").startswith("[입력 확인]"))
        self.assertTrue(main.get_next_holiday("내일").startswith("[입력 확인]"))


class Check(Base):
    def test_check(self):
        self.assertIn("대체공휴일입니다", main.check_holiday("2026-03-02"))
        self.assertIn("공휴일입니다: 설날", main.check_holiday("2026-02-17"))
        self.assertIn("주말(토요일)", main.check_holiday("2026-07-04"))
        self.assertIn("평일입니다", main.check_holiday("2026-07-06"))
        self.assertTrue(main.check_holiday("2040-01-01").startswith("[입력 확인]"))
        self.assertTrue(main.check_holiday("x").startswith("[입력 확인]"))


class Long(Base):
    def test_long_weekends(self):
        r = main.get_long_weekends(2026, 2)
        self.assertIn("2026-02-14(토) ~ 2026-02-18(수) — 5일 (설날)", r)
        self.assertIn("2026-09-24(목) ~ 2026-09-28(월) — 5일", r)
        self.assertIn("2026-10-09(금) ~ 2026-10-11(일) — 3일 (한글날)", r)
        self.assertIn("연차 2일(2026-02-19(목), 2026-02-20(금)) 사용 → 2026-02-14(토) ~ 2026-02-22(일) 총 9일 휴무", r)

    def test_leave_limit(self):
        r1 = main.get_long_weekends(2026, 1)
        self.assertIn("연차 1일(2026-05-04(월)) 사용 → 2026-05-02(토) ~ 2026-05-05(화) 총 4일 휴무", r1)
        self.assertNotIn("2026-02-19", r1)
        r3 = main.get_long_weekends(2026, 3)
        self.assertIn("연차 3일(2026-09-21(월), 2026-09-22(화), 2026-09-23(수)) 사용 → 2026-09-19(토) ~ 2026-09-28(월) 총 10일 휴무", r3)

    def test_bridges_stay_in_year(self):
        r = main.get_long_weekends(2026, 3)
        self.assertNotIn("2025-12-29", r)
        self.assertIn("연차 1일(2026-01-02(금)) 사용 → 2026-01-01(목) ~ 2026-01-04(일) 총 4일 휴무", r)

    def test_unpublished(self):
        self.assertTrue(main.get_long_weekends(2027).startswith("[입력 확인]"))


class Errors(unittest.TestCase):
    def setUp(self):
        self._o = main.fetch_year

    def tearDown(self):
        main.fetch_year = self._o

    def test_errors(self):
        for exc, word in ((main.HolidayUnavailable(), "정상 응답"), (main.HolidayConfigError(), "설정"), (main.HolidayLimit(), "횟수")):
            def boom(y, e=exc):
                raise e
            main.fetch_year = boom
            for call in (lambda: main.get_holidays(2026), lambda: main.get_next_holiday("2026-11-06"),
                         lambda: main.get_long_weekends(2026), lambda: main.check_holiday("2026-03-02")):
                r = call()
                self.assertTrue(r.startswith("[조회 실패]"), r)
                self.assertIn(word, r)
                self.assertNotIn("HOLIDAY_KEY", r)

    def test_no_key(self):
        main.fetch_year = self._o
        os.environ.pop("HOLIDAY_KEY", None)
        with self.assertRaises(main.HolidayConfigError):
            main.fetch_year(2026)

    def test_adjacent_year_failure_ignored(self):
        def f(y):
            if y == 2026:
                return dict(H2026)
            raise main.HolidayUnavailable()
        main.fetch_year = f
        self.assertIn("연휴", main.get_long_weekends(2026))


class Reference(unittest.TestCase):
    def test_ref(self):
        r = main.get_holiday_reference()
        for s in ("공휴일로 표시된 날", "1~3일", "24시간"):
            self.assertIn(s, r)


class Registry(unittest.TestCase):
    def test_tools(self):
        import fastmcp
        reg = getattr(fastmcp, "REG", None)
        if reg is None:
            self.skipTest("스텁 fastmcp에서만 실행")
        self.assertEqual(set(reg), {"get_holidays", "get_next_holiday", "get_long_weekends", "check_holiday", "get_holiday_reference"})
        for n, (kw, fn) in reg.items():
            self.assertEqual(set(kw["annotations"]), {"title", "readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"})
            self.assertLessEqual(len(kw["description"]), 1024, n)
            self.assertIn("공휴일·연휴 도우미 - Holiday Helper", kw["description"])
            self.assertNotIn("kakao", n.lower())
        self.assertLessEqual(len(main.SERVICE), 30)


if __name__ == "__main__":
    unittest.main()
