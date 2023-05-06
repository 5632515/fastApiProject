import datetime

from playwright.sync_api import Playwright, sync_playwright, expect

now_name = ""


def run(playwright: Playwright, name, ID):
    global now_name
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://jzsc.mohurd.gov.cn/data/person")
    page.get_by_placeholder("请输入人员姓名").click()
    page.get_by_placeholder("请输入人员姓名").fill(name)
    now_name = name
    page.get_by_placeholder("请输入身份证号").click()
    page.get_by_placeholder("请输入身份证号").fill(ID)
    page.get_by_text("查询").click()
    page.wait_for_timeout(1000)
    all_trs = page.query_selector_all(".el-table__row")
    man_info = []
    man_info.append([name, ID, 2])
    for td in all_trs:
        contents = [
            td.query_selector_all(".cell")[3].text_content(),
            td.query_selector_all(".cell")[4].text_content(),
            "未到期，到本次查询时间(" + datetime.datetime.now().strftime("%Y-%m-%d") + ")有效",
        ]
        man_info.append(contents)
    print(man_info)
    # ---------------------
    context.close()
    browser.close()
    return man_info


def start(name, ID):
    with sync_playwright() as playwright:
        query = run(playwright, name, ID)
        return query
