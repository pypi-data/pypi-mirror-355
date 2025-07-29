from asyncio import run, sleep
from x_model import init_db
from xync_schema import models
from xync_client.loader import TORM
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


def login(driver, agent) -> None:
    driver.get("https://finance.ozon.ru")
    for cookie in agent.state:
        driver.add_cookie(cookie)
    driver.get("https://finance.ozon.ru/lk")
    if 1:  # todo: только если просит ввести пин-код
        pin = agent.auth.get("code")
        actions = ActionChains(driver)
        for char in pin:
            actions.send_keys(char)
        actions.perform()


async def send_cred(driver, amount, payment, cred):
    pass


async def main():
    _ = await init_db(TORM, True)
    agent = await models.PmAgent.filter(pm__norm="ozon", auth__isnull=False).first()
    driver = uc.Chrome(no_sandbox=True)
    driver.implicitly_wait(15)

    try:
        if not agent.state:
            driver.get("https://ozon.ru/ozonid-lite")
            driver.find_element(By.NAME, "autocomplete").send_keys(agent.auth.get("phone"))
            driver.find_element(By.CLASS_NAME, "b201-a").click()
            # todo: здесь не всегда просит код, иногда вход по QR или подтверждению из почты
            sms_code = input("Введите 6-ти значный код: ")
            driver.find_element(By.CLASS_NAME, "d01-a.d01-a5").send_keys(sms_code)
        # elif 0:  # todo: проверка на залогиненность
        login(driver, agent)
        # todo: здесь дальше отправка исходящего платежа и проверка входящего
        await sleep(5)

    finally:
        agent.state = driver.get_cookies()  # Получаем все куки
        await agent.save()
        driver.quit()


if __name__ == "__main__":
    run(main())
