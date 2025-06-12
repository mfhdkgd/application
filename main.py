from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")

COMMENTS = [
    "خیلی خوبه 👏",
    "عالیه 🔥",
    "چه پست خفنی 😍",
    "دمت گرم 💯",
    "واقعاً زیباست 🌟"
]

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def login(driver, username, password, two_factor_code=None):
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(7)

    if "two_factor" in driver.current_url:
        if two_factor_code:
            try:
                driver.find_element(By.NAME, "verificationCode").send_keys(two_factor_code)
                driver.find_element(By.XPATH, "//button[@type='button']").click()
                time.sleep(5)
                return True
            except:
                return "خطا در وارد کردن کد ۲FA."
        else:
            return "۲FA مورد نیاز است."
    elif "login" in driver.current_url:
        return "ورود ناموفق بود."
    return True

def interact_with_target(driver, target_username):
    driver.get(f"https://www.instagram.com/{target_username}/")
    time.sleep(5)

    # کلیک روی اولین پست
    posts = driver.find_elements(By.XPATH, "//article//a")
    links = [p.get_attribute("href") for p in posts[:5]]

    for link in links:
        driver.get(link)
        time.sleep(random.randint(4, 8))

        try:
            # لایک کردن
            like_btn = driver.find_element(By.XPATH, '//span[contains(@aria-label, "Like") or @aria-label="پسندیدن"]/..')
            like_btn.click()
            time.sleep(2)

            # کامنت گذاشتن
            comment_area = driver.find_element(By.XPATH, '//textarea[@aria-label="افزودن نظر…"]')
            comment_area.click()
            comment = random.choice(COMMENTS)
            comment_area.send_keys(comment)
            post_btn = driver.find_element(By.XPATH, "//button[text()='ارسال' or text()='Post']")
            post_btn.click()
            time.sleep(2)

        except Exception as e:
            print(f"خطا در تعامل با پست: {e}")
        time.sleep(random.randint(3, 7))

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "status": "", "ask_2fa": False})

@app.post("/start", response_class=HTMLResponse)
async def form_post(
    request: Request,
    your_username: str = Form(...),
    your_password: str = Form(...),
    target_username: str = Form(...),
    two_factor_code: str = Form(None)
):
    driver = create_driver()
    login_status = login(driver, your_username, your_password, two_factor_code)

    if login_status == "۲FA مورد نیاز است.":
        driver.quit()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "status": "کد تأیید دو مرحله‌ای را وارد کنید",
            "ask_2fa": True,
            "your_username": your_username,
            "your_password": your_password,
            "target_username": target_username
        })

    if login_status is True:
        try:
            interact_with_target(driver, target_username)
            status_msg = "عملیات با موفقیت انجام شد."
        except Exception as e:
            status_msg = f"خطا در تعامل با پیج هدف: {e}"
    else:
        status_msg = login_status

    driver.quit()
    return templates.TemplateResponse("index.html", {"request": request, "status": status_msg, "ask_2fa": False})