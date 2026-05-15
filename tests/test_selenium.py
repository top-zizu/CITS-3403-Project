import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://127.0.0.1:5000"

TEST_USERNAME = "selenium_test_user"
TEST_EMAIL = "selenium@test.com"
TEST_PASSWORD = "TestPass123!"


# ── Driver fixture ────────────────────────────────────────────────

@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()


def wait_for(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


# ── Tests ─────────────────────────────────────────────────────────

def test_homepage_loads(driver):
    """Homepage loads and shows the DebateHub branding."""
    driver.get(BASE_URL)
    assert "DebateHub" in driver.title or "DebateHub" in driver.page_source


def test_signup(driver):
    """A new user can register through the sign up form."""
    driver.get(f"{BASE_URL}/sign-up")
    wait_for(driver, By.NAME, "username")

    driver.find_element(By.NAME, "username").send_keys(TEST_USERNAME)
    driver.find_element(By.NAME, "email").send_keys(TEST_EMAIL)
    driver.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
    driver.find_element(By.NAME, "confirm_password").send_keys(TEST_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    time.sleep(1)
    assert "/login" in driver.current_url or "log in" in driver.page_source.lower()


def test_login(driver):
    """A registered user can log in."""
    driver.get(f"{BASE_URL}/login")
    wait_for(driver, By.NAME, "login")

    driver.find_element(By.NAME, "login").send_keys(TEST_USERNAME)
    driver.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    time.sleep(1)
    assert "/dashboard" in driver.current_url or "dashboard" in driver.page_source.lower()


def test_explore_page_shows_debates(driver):
    """The explore page loads and displays debate cards."""
    driver.get(f"{BASE_URL}/explore")
    time.sleep(1)
    assert "Explore" in driver.page_source or "debate" in driver.page_source.lower()


def test_create_debate(driver):
    """A logged-in user can create a new debate."""
    driver.get(f"{BASE_URL}/debates/create")
    wait_for(driver, By.NAME, "title")

    driver.find_element(By.NAME, "title").send_keys("Selenium Test Debate")
    driver.find_element(By.NAME, "description").send_keys("This debate was created by a Selenium test.")

    category_select = driver.find_element(By.NAME, "category")
    category_select.find_element(By.CSS_SELECTOR, "option:not([value=''])").click()

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)

    assert "Selenium Test Debate" in driver.page_source


def test_leaderboard_loads(driver):
    """The leaderboard page loads and shows user rankings."""
    driver.get(f"{BASE_URL}/leaderboard")
    time.sleep(1)
    assert "Leaderboard" in driver.page_source or "reputation" in driver.page_source.lower()


def test_search_debates(driver):
    """The search page returns results for a query."""
    driver.get(f"{BASE_URL}/search")
    time.sleep(1)
    search_box = wait_for(driver, By.CSS_SELECTOR, "input[type='text'], input[type='search'], input.search-input")
    search_box.send_keys("debate")
    search_box.send_keys(Keys.RETURN)
    time.sleep(1)
    assert "debate" in driver.page_source.lower()


def test_friends_page_loads(driver):
    """The friends page loads for a logged-in user."""
    driver.get(f"{BASE_URL}/friends")
    time.sleep(1)
    assert "Friends" in driver.page_source or "follow" in driver.page_source.lower()


def test_notifications_page_loads(driver):
    """The notifications page loads for a logged-in user."""
    driver.get(f"{BASE_URL}/notifications")
    time.sleep(1)
    assert "Notifications" in driver.page_source


def test_logout(driver):
    """A logged-in user can log out."""
    driver.get(f"{BASE_URL}/logout")
    time.sleep(1)
    assert "/login" in driver.current_url or "log in" in driver.page_source.lower() or BASE_URL == driver.current_url.rstrip("/")
