from playwright.sync_api import Playwright, sync_playwright, expect
from datetime import datetime
# ok check status
ok = True


def handle_dialog(dialog):
    global ok
    """监听后处理"""
    print(dialog.message)
    ok = False
    dialog.dismiss()


def browse(page, page_destination):
    page.goto(page_destination)


def put_into(page, name, ID):
    page.get_by_placeholder("请输入姓名").click()
    page.get_by_placeholder("请输入姓名").fill(name)
    page.get_by_placeholder("请输入身份证号").click()
    page.get_by_placeholder("请输入身份证号").fill(ID)


def run(playwright: Playwright, name, ID):
    global ok
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    website_1 = "https://txjs.miit.gov.cn/ggfw/search.jsp"
    browse(page, website_1)
    page.on("dialog", handle_dialog)
    ok = True
    while True:
        put_into(page, name, ID)
        page.get_by_role("button", name="立即查询").click()
        page.wait_for_selector(".detail")
        page.get_by_role("button", name="查看详情").click()
        page.wait_for_selector("#CERTIFICATE_NUMBER")
        if ok:
            break
        else:
            page.goto(website_1)

    # page.wait_for_event("li:#CERTIFICATE_NUMBER")
    man_info = [[name, ID, 1]]
    # print("证书号：" + page.query_selector("#CERTIFICATE_NUMBER").text_content())
    # print("有效期：" + page.query_selector("#END_DATE").text_content())
    date_string = page.query_selector("#END_DATE").text_content()
    date = datetime.strptime(date_string, "%Y-%m-%d")
    now_time = datetime.now()
    check = ""
    if date > now_time:
        check = "未过期，有效至" + date_string
    else:
        check = "已到期，有效至" + date_string
    man_info.append(['安全员证书', page.query_selector("#CERTIFICATE_NUMBER").text_content(), check])
    print(man_info)
    # ---------------------
    context.close()
    browser.close()
    return man_info


def start(name, ID):
    with sync_playwright() as playwright:
        query = run(playwright, name, ID)
        return query

