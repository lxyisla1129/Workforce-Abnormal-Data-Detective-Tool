# Scrapying AMS system
# import requests
# import pandas as pd

# session = requests.Session()

# session.headers.update({
#     "Accept": "application/json, text/plain, */*",
#     "Content-Type": "application/json;charset=UTF-8",
#     "Origin": "http://iams-us.jd.com",
#     "Referer": "http://iams-us.jd.com/workHourCorrect",
#     "User-Agent": "Mozilla/5.0",
#     "X-Requested-With": "XMLHttpRequest",
#     "Cookie": "jd.erp.lang=zh_CN; jdd69fo72b8lfeoe=PWC2UVDNDIEOUAOOR75K7BCEL34AERZ7ET7LMWQK5Z5AKGIKNTYFTHZVIYUVZJ4FQUQ5EE2WOLF2DHAWGD37WSKIEY; focus-login-switch=saas; ssa.global.ticket=C3D1FA42A599078B28E10DB9055AC288; __jdu=17737693397381901549022; focus-token-type=15; __jdc=177913917; sso.jd.com=BJ.26D1D749867AFFB90724CFB8D148373C.6620260905012919; ejdst_essa=goJCEEFYoreQCBu2oub1oTJfdUYNGoGpZGl-TCw_hDrLERaXcyq9GVFOG7ZcJIZXC3KtkwMkwrogzv9Na4RBoRWEMBSIyvFrjme-VuEkP8l-ECxc5DptCxOVXIbXlogqsKAwSmJwKXNn_FgAPiW2wbxL1pcmokHJuIQuWz5g6QW-wBeIQBVRMpQ1n7QhaDNWZ2V8TshGvoRJDgPcN2N3ccqeakSC6FncJlhAeZH77UhQ-KWeHxRLNuznfKLUkURn557ovk2L0XrR4LP90HHUGfEEn6Lr3zh7zHjp4atWF6qkIMNreDR_jD9FBA; __jda=177913917.17737693397381901549022.1773769340.1788369959.1789404397.15; __jdv=177913917|direct|-|none|-|1789404397084; ssa.jdlhr-kq=e056a3c2941f5320704f64bc19ee4c36ef4f5148cd5c236c57febdfe6d8355c4550a49014f63cee1dab1ca901de3f81f856744e299556153d9bf11d25a41bfc03ec5ab224fb59c5e886dbc2d9389bbad361d8839ca97988a7718e1fa48a14d4739debe2a69f0f133e129c8e50ff1d0de984bd731e1c497d709249b8448f820d2; jdd69fo72b8lfeoeTK=jdd03PWC2UVDNDIEOUAOOR75K7BCEL34AERZ7ET7LMWQK5Z5AKGIKNTYFTHZVIYUVZJ4FQUQ5EE2WOLF2DHAWGD37WSKIEYAAAANAUG2KE2IAAAAAD7646Y3PE6E6XQX"
# })

# url = "http://api-iams-us.jd.com/kqAttDailySummaryCheck/findPage"

# base_payload = {
#     "deptFullCode": "/00000000/00029430/00076304",
#     "exTypeCodeList": [],
#     "kqAttGroupId": None,
#     "language": "zh_CN",
#     "nature": None,
#     "natureList": [],
#     "statusList": [],
#     "timeRange": ["2026-09-08", "2026-09-14"],
#     "userCode": None,
#     "userErp": None,
#     "userName": None,
#     "pageSize": 1000,
# }

# all_rows = []

# for page in range(1, 100):
#     payload = base_payload.copy()
#     payload["pageIndex"] = page

#     r = session.post(url, json=payload, timeout=30)
#     r.raise_for_status()

#     result = r.json()

#     print(f"Page {page}")
#     print(result.keys())

#     # 这里需要根据真实 response 调整
#     rows = result.get("data", {}).get("list", [])

#     if not rows:
#         break

#     all_rows.extend(rows)

# df = pd.DataFrame(all_rows)

# print(df.head())
# print(df.shape)

# df.to_excel("attendance.xlsx", index=False)
import requests
import pandas as pd
import math
import time
from datetime import datetime, timedelta

url = "http://api-iams-us.jd.com/kqAttDailySummaryCheck/findPage"

params = {
    "oidc.code": "sfaVhaUz2Nne7Cf9E2m3qZRmNZuXzNDjyYs_mgewKMA",
    "oidc.state": "hHanIzEfsXpojLsO7VFZkKEC8jiEK0ya0uJCXgff4vI",
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "http://iams-us.jd.com",
    "Referer": "http://iams-us.jd.com/workHourCorrect",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": "jd.erp.lang=zh_CN; jdd69fo72b8lfeoe=PWC2UVDNDIEOUAOOR75K7BCEL34AERZ7ET7LMWQK5Z5AKGIKNTYFTHZVIYUVZJ4FQUQ5EE2WOLF2DHAWGD37WSKIEY; focus-login-switch=saas; ssa.global.ticket=C3D1FA42A599078B28E10DB9055AC288; __jdu=17737693397381901549022; focus-token-type=15; __jdc=177913917; sso.jd.com=BJ.26D1D749867AFFB90724CFB8D148373C.6620260905012919; ejdst_essa=goJCEEFYoreQCBu2oub1oTJfdUYNGoGpZGl-TCw_hDrLERaXcyq9GVFOG7ZcJIZXC3KtkwMkwrogzv9Na4RBoRWEMBSIyvFrjme-VuEkP8l-ECxc5DptCxOVXIbXlogqsKAwSmJwKXNn_FgAPiW2wbxL1pcmokHJuIQuWz5g6QW-wBeIQBVRMpQ1n7QhaDNWZ2V8TshGvoRJDgPcN2N3ccqeakSC6FncJlhAeZH77UhQ-KWeHxRLNuznfKLUkURn557ovk2L0XrR4LP90HHUGfEEn6Lr3zh7zHjp4atWF6qkIMNreDR_jD9FBA; __jdv=177913917|direct|-|none|-|1789404397084; jdd69fo72b8lfeoeTK=jdd03PWC2UVDNDIEOUAOOR75K7BCEL34AERZ7ET7LMWQK5Z5AKGIKNTYFTHZVIYUVZJ4FQUQ5EE2WOLF2DHAWGD37WSKIEYAAAANAYZKLH5QAAAAADLFRF4D7ROHMSUX; __jda=177913917.17737693397381901549022.1773769340.1790354891.1790613577.19; ssa.jdlhr-kq=e056a3c2941f5320704f64bc19ee4c3641cc1010bd228c06b2d518976e4edbc32c4b053c77f51c166729d8a4e6014b143a30f044408d75a74c3a9728b7aece46dc18e78f5e3ef8d2333dd2b6d9bff9c3f37a67505158533ce53a5c4589bdac3e2845d613785936d3b3f9112728a516dd558692963921eb7f2ceeeb187aad97cb"
}

def get_attendance_data(start_date, end_date):

    payload = {
        "deptFullCode": "/00000000/00029430/00076304",
        "kqAttGroupId": None,
        "timeRange": [start_date, end_date],
        "userCode": None,
        "userErp": None,
        "userName": None,
        "nature": None,
        "natureList": [],
        "statusList": [],
        "exTypeCodeList": [],
        "pageIndex": 1,
        "pageSize": 1000,
        "language": "zh_CN"
    }

    all_data = []

    # First page
    r = requests.post(
        url,
        params=params,
        headers=headers,
        json=payload,
        timeout=30,
        allow_redirects=False
    )

    # Detect expired JD login
    if r.status_code in (301, 302, 303, 307, 308):
        raise RuntimeError(
            "JD login expired. Please refresh your OIDC/cookie."
        )

    content_type = r.headers.get("Content-Type", "")

    if "text/html" in content_type:
        raise RuntimeError(
            "JD login expired. Received HTML instead of API data."
        )

    r.raise_for_status()

    result = r.json()

    if not result.get("success"):
        raise RuntimeError(result)

    total = result["totalCount"]

    all_data.extend(result["data"])

    pages = math.ceil(
        total / payload["pageSize"]
    )

    print(f"Total records: {total:,}")
    print(f"Total pages: {pages}")

    # Remaining pages
    for page in range(2, pages + 1):

        payload["pageIndex"] = page

        r = requests.post(
            url,
            params=params,
            headers=headers,
            json=payload,
            timeout=30,
            allow_redirects=False
        )

        if r.status_code in (301, 302, 303, 307, 308):
            raise RuntimeError(
                "JD login expired."
            )

        r.raise_for_status()

        result = r.json()

        if not result.get("success"):
            raise RuntimeError(
                f"Page {page} failed: {result}"
            )

        all_data.extend(result["data"])

        print(
            f"Page {page}/{pages} | "
            f"{len(all_data):,}/{total:,}"
        )

        time.sleep(0.2)

    df = pd.DataFrame(all_data)

    print(
        f"Scraping completed: {len(df):,} rows"
    )

    return df