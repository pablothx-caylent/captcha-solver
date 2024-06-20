import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium_recaptcha_solver import RecaptchaSolver


class ValidationFailed(Exception):
    pass


class RecaptchaFailed(Exception):
    pass


def configure_driver(user_agent):
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    # Uncomment the following line to run the browser in headless mode no UI
    # options.add_argument('--headless')

    timestamp = str(int(round(time.time_ns())))
    service_log_path = f'/tmp/{timestamp}.log'

    driver = webdriver.Chrome(
        options=options, service_log_path=service_log_path)
    return driver


def fill_and_submit_form(form_data, driver):
    selectors = {
        "full_name_input": "body > div.main-block > form > div.info > input.fname",
        "submit_button": '//*[@id="submit"]',
        "email_input": "body > div.main-block > form > div.info > input[type=text]:nth-child(2)",
        "phone_number_input": "body > div.main-block > form > div.info > input[type=text]:nth-child(3)",
        "title_text": "body > div > h1"
    }

    solver = RecaptchaSolver(driver=driver)
    driver.get('http://localhost/index.html')

    print("Waiting for reCAPTCHA to be solved")
    try:
        recaptcha_iframe = driver.find_element(
            By.XPATH, '//iframe[@title="reCAPTCHA"]')
        solver.click_recaptcha_v2(iframe=recaptcha_iframe)
    except Exception as e:
        print(f"Error solving reCAPTCHA: {e}")
        raise RecaptchaFailed("Failed to solve reCAPTCHA") from e

    print("reCAPTCHA solved")

    driver.maximize_window()
    time.sleep(2)

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, selectors["full_name_input"])))
    driver.find_element(By.CSS_SELECTOR, selectors["full_name_input"]).send_keys(
        form_data["full_name"])

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, selectors["email_input"])))
    driver.find_element(By.CSS_SELECTOR, selectors["email_input"]).send_keys(
        form_data["email"])

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, selectors["phone_number_input"])))
    driver.find_element(By.CSS_SELECTOR, selectors["phone_number_input"]).send_keys(
        form_data["phone_number"])

    time.sleep(3)

    try:
        submit_button = driver.find_element(
            By.XPATH, selectors["submit_button"])
        submit_button.click()
        print("Form submitted and navigation successful")
        time.sleep(2)
    except Exception as e:
        print(f"Error during form submission: {e}")
        raise ValidationFailed("Form submission failed") from e


def lambda_handler(event, context):
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'

    driver = configure_driver(user_agent)

    try:
        fill_and_submit_form(event, driver)
    finally:
        driver.quit()


if __name__ == "__main__":
    test_event_data = {
        "phone_number": "123454321",
        "email": "john.doe@domain.com",
        "full_name": "John Doe"
    }
    lambda_handler(test_event_data, None)
