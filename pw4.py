from playwright.sync_api import Playwright, sync_playwright, expect

ok = True


def handle_dialog(dialog):
    global ok
    """监听后处理"""
    print(dialog.message)
    ok = False
    dialog.dismiss()


def run(playwright: Playwright, name, ID):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    man_info = [[name, ID, 4]]
    page.goto("http://dn7.gxcic.net:8190/szjsframeqy/szjs_gxxzsp/tzbasicinfo/tzbasicinfolistforkp")
    page.on("", handle_dialog)
    page.locator("[id=\"IDCardNo\\$text\"]").click()
    page.locator("[id=\"IDCardNo\\$text\"]").fill(ID)
    page.locator("[id=\"fullname\\$text\"]").click()
    page.locator("[id=\"fullname\\$text\"]").fill(name)
    page.locator("a").filter(has_text="搜索").click()
    try:
        page.wait_for_selector('.mini-grid-row', timeout=5000)
    except:
        page.get_by_role("link", name="确定").click()
        print("无相关信息，退出")
        context.close()
        browser.close()
        print(man_info)
        return man_info

    all_trs = page.query_selector_all('.mini-grid-row')
    for tr in all_trs:
        if tr.query_selector_all('td')[9].text_content() == '有效':
            man_info.append(
                [tr.query_selector_all('td')[5].text_content() + '证书', tr.query_selector_all('td')[2].text_content(),
                 '未到期，有效期至' + tr.query_selector_all('td')[9].text_content()])
    print(man_info)
    # ---------------------
    context.close()
    browser.close()
    return man_info


def start(name, ID):
    with sync_playwright() as playwright:
        query = run(playwright, name, ID)
        return query
