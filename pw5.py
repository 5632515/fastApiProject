import datetime

from playwright.sync_api import Playwright, sync_playwright, expect
import urllib.parse

ok = True


def handle_dialog(dialog):
    global ok
    """监听后处理"""
    print(dialog.message)
    ok = False
    dialog.dismiss()


def run(playwright: Playwright, name, ID):
    man_info = [[name, ID, 5]]
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://dn4.gxcic.net:8100/gxkspxqy/mobile/certificate/xczyrycertificatesearch")
    page.locator("[id=\"username\\$text\"]").click()
    page.locator("[id=\"username\\$text\"]").fill(name)
    page.locator("[id=\"idcard\\$text\"]").click()
    page.locator("[id=\"idcard\\$text\"]").fill(ID)
    page.get_by_role("link", name="证书查询").click()
    # page.wait_for_function("() => document.querySelectorAll('iframe').length > 0")
    page.wait_for_timeout(1000)
    row_num = page.frame_locator("iframe").nth(0).get_by_role("row").count()
    print(row_num)
    frame_rows = page.frame_locator("iframe").nth(0).get_by_role("row")
    for i in range(5, row_num - 1):
        row = frame_rows.nth(i)
        # print(row.all_text_contents())
        print(row.get_by_role("cell").nth(3).text_content(), row.get_by_role("cell").nth(4).text_content(),
              row.get_by_role("cell").nth(6).text_content())
        check = '已过期'
        if row.get_by_role("cell").nth(6).text_content() == '有效':
            check = '未到期，到本次查询时间(' + datetime.datetime.now().strftime("%Y-%m-%d") + ')有效'
        man_info.append(
            [row.get_by_role("cell").nth(4).text_content() + '证书', row.get_by_role("cell").nth(3).text_content(),
             check])
    # for tr in all_trs:
    #     if tr.query_selector_all('td')[9].text_content() == '有效':
    #         man_info.append(
    #             [tr.query_selector_all('td')[5].text_content() + '证书', tr.query_selector_all('td')[2].text_content(),
    #              '未到期，有效期至' + tr.query_selector_all('td')[9].text_content()])
    print(man_info)

    # ---------------------
    context.close()
    browser.close()
    return man_info


def start(name, ID):
    with sync_playwright() as playwright:
        query = run(playwright, name, ID)
        return query
