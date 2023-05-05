import json

from playwright.sync_api import Playwright, sync_playwright, expect
import base64
import requests


def path2base64(path):
    with open(path, "rb") as f:
        byte_data = f.read()
    base64_str = base64.b64encode(byte_data).decode("ascii")  # 二进制转base64
    return base64_str


def run(playwright: Playwright, name, ID):
    man_info = [[name, ID, 3]]
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://cx.mem.gov.cn/")
    page.frame_locator("internal:text=\"</html>\"i").locator("#certtype_code").select_option("720")
    page.frame_locator("internal:text=\"</html>\"i").locator("#certnum").click()
    page.frame_locator("internal:text=\"</html>\"i").locator("#certnum").fill(ID)
    page.frame_locator("internal:text=\"</html>\"i").locator("#name").click()
    page.frame_locator("internal:text=\"</html>\"i").locator("#name").fill(name)
    page.frame_locator("internal:text=\"</html>\"i").locator("#passcode").click()
    page.frame_locator("internal:text=\"</html>\"i").get_by_role("img", name="点我刷新").screenshot(
        path="screenshot.png")
    img_base64 = path2base64("screenshot.png")
    print(img_base64)
    api_url = "http://43.207.206.87:6688/api.Common_VerificationCode"
    data = {"ImageBase64": img_base64}
    data_json = json.dumps(data)
    response = requests.post(api_url, data=data_json)
    if response.status_code != 200:
        raise ConnectionError(f'{api_url} status code is {response.status_code}.')
    response_load = json.loads(response.content)
    if 'result' not in response_load.keys():
        raise ValueError(f'{api_url} miss key msg.')
    if len(response_load['result']) != 4:
        print('识别验证码位数错误')
    else:
        print('识别认证码为：' + response_load['result'])
    page.frame_locator("internal:text=\"</html>\"i").locator("#passcode").fill(response_load['result'])
    with page.expect_popup() as page1_info:
        page.frame_locator("internal:text=\"</html>\"i").get_by_role("button", name="查询").click()
        page1 = page1_info.value
        page1.wait_for_selector("text='以上信息仅供参考，如有疑问请与发证机关联系！'")
        test = page1.locator("'没有查询到相关证件信息，请核实后重新查询或联系发证机关补登信息！'").count()
        if test == 0:
            newest_content = page1.query_selector_all('.content')[0]
            all_trs = newest_content.query_selector_all('tr')
            for tr in all_trs:
                if tr.query_selector_all('th')[0].text_content() == "操作项目":
                    # print(tr.query_selector_all('td')[0].text_content().strip(), tr.query_selector_all('td')[
                    # 1].text_content().strip())
                    man_info.append([tr.query_selector_all('td')[0].text_content().strip()+'证书', 'T' +
                                     ID, '未到期，有效至'+tr.query_selector_all('td')[1].text_content().strip()])
        else:
            print("没有查询到相关证件信息")
        print(man_info)
    # ---------------------
    context.close()
    browser.close()
    return man_info


def start(name, ID):
    with sync_playwright() as playwright:
        query = run(playwright, name, ID)
        return query
