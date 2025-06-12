from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import time, os
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# مسیر برای ذخیره سشن لاگین
SESSION_FILE = "session_cookies.txt"

@app.get("/", response_class=HTMLResponse)
def form_get(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "ask_2fa": False,
        "status": None
    })

@app.post("/start", response_class=HTMLResponse)
def form_post(
    request: Request,
    your_username: str = Form(...),
    your_password: str = Form(...),
    target_username: str = Form(...),
    two_factor_code: str = Form(None)
):
    chromedriver_autoinstaller.install()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)

    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    try:
        # لاگین
        user_input = driver.find_element(By.NAME, "username")
        pass_input = driver.find_element(By.NAME, "password")
        user_input.send_keys(your_username)
        pass_input.send_keys(your_password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)

        # بررسی نیاز به 2FA
        if "two_factor" in driver.current_url:
            if not two_factor_code:
                driver.quit()
                return templates.TemplateResponse("index.html", {
                    "request": request,
                    "your_username": your_username,
                    "your_password": your_password,
                    "target_username": target_username,
                    "ask_2fa": True,
                    "status": None
                })

            code_input = driver.find_element(By.NAME, "verificationCode")
            code_input.send_keys(two_factor_code)
            driver.find_element(By.XPATH, "//button").click()
            time.sleep(5)

        # پرش از popup
        try:
            driver.find_element(By.XPATH, "//button[text()='Not Now']").click()
            time.sleep(2)
        except:
            pass

        # ورود به پیج هدف
        driver.get(f"https://www.instagram.com/{target_username}/")
        time.sleep(3)

        posts = driver.find_elements(By.XPATH, '//article//a')
        links = [post.get_attribute("href") for post in posts[:5]]

        comments = [
            "عالیه 👌",
            "چه پستی 😍",
            "دمت گرم 🔥",
            "محشره ✨",
            "عاشقشم ❤️"
        ]

        for link in links:
            driver.get(link)
            time.sleep(2)

            # لایک
            try:
                like_button = driver.find_element(By.XPATH, "//span[@aria-label='Like']")
                like_button.click()
            except:
                pass

            # کامنت
            try:
                driver.find_element(By.XPATH, "//textarea").click()
                driver.find_element(By.XPATH, "//textarea").send_keys(comments[int(time.time()) % len(comments)])
                driver.find_element(By.XPATH, "//button[contains(text(),'Post')]").click()
            except:
                pass

            time.sleep(5)

        driver.quit()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "status": f"پایان عملیات! روی {len(links)} پست از @{target_username} لایک و کامنت گذاشته شد.",
            "ask_2fa": False
        })

    except Exception as e:
        driver.quit()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "status": f"خطا: {str(e)}",
            "ask_2fa": False
        })
