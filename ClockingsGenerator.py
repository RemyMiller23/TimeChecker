import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def getClockingReport():
    # Launch Chrome browser in headless mode
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(30)
    driver.get("http://srvhodtrac-prod/webregister/eViewClockings.aspx")

    # Find and click the clockings button
    clockings_button = driver.find_element(By.ID, "btnClockings")
    clockings_button.click()
    time.sleep(2)

    # Prepare date range for filtering
    today = datetime.today()
    print(today)
    first_of_month = today.replace(day=1)
    yesterday = today - timedelta(days=1)

    if today.day == 1:
        # On the first day of the month, get the previous month range
        last_of_prev_month = first_of_month - timedelta(days=1)
        first_of_prev_month = last_of_prev_month.replace(day=1)
        start_date = first_of_prev_month.date()
        end_date = last_of_prev_month.date()
    else:
        # Otherwise, from the 1st of this month to yesterday
        start_date = first_of_month.date()
        end_date = yesterday.date()

    # Grab the rows of the table (skip header row)
    clockings_table = driver.find_elements(By.CSS_SELECTOR, "#DataGrid1 tr")[1:]

    def parse_datetime_from_td(td_text):
        try:
            return datetime.strptime(td_text.strip(), "%Y/%m/%d %a %H:%M:%S")
        except ValueError:
            return None

    matching_rows = []

    # Filter rows by date range
    for row in clockings_table:
        tds = row.find_elements(By.TAG_NAME, "td")
        if not tds:
            continue

        clocking_text = tds[0].text.strip()
        clocking_time = parse_datetime_from_td(clocking_text)

        if clocking_time and start_date <= clocking_time.date() <= end_date:
            matching_rows.append(row)

    print(f"Found {len(matching_rows)} matching rows.")

    # Write results to file
    filename = "ClockingsReport.txt"
    output_path = os.path.join(os.getcwd(), filename)

    with open(output_path, "w", encoding="utf-8") as file:
        for row in matching_rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            line = f"{tds[0].text}\t{tds[1].text}\n"
            file.write(line)
    time.sleep(2)
    driver.quit()

    #Reminders
    reminder_path = os.path.join(os.getcwd(), "Reminder.txt")
    with open(reminder_path, "r", encoding="utf-8") as reminder_file:
        reminder_contents = reminder_file.read()

    with open(output_path, "a", encoding="utf-8") as file:
        file.write("\nReminders\n")
        file.write("---------\n")
        file.write(reminder_contents)


    print(f"Clockings Report written to: {output_path}")