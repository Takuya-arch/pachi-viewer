from playwright.sync_api import sync_playwright
import sqlite3
import datetime

def save_data(date_str, unit, diff_balls):
    conn = sqlite3.connect(r"C:\Users\Owner\Desktop\pachi_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slump_data (
            date TEXT,
            unit TEXT,
            diff_balls INTEGER,
            UNIQUE(date, unit)
        )
    """)
    cursor.execute("""
        INSERT OR REPLACE INTO slump_data (date, unit, diff_balls)
        VALUES (?, ?, ?)
    """, (date_str, unit, diff_balls))
    conn.commit()
    conn.close()

def main():
    target_units = ["401", "402", "403"]
    today_str = str(datetime.date.today())

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # 自動化なので画面を非表示(True)にするとスマートです
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()

        for unit_num in target_units:
            url = f"https://daidata.goraggio.com/100969/detail?unit={unit_num}"
            try:
                page.goto(url)
                page.wait_for_timeout(3000)

                try:
                    agree_button = page.get_by_role("button", name="利用規約に同意する")
                    if agree_button.is_visible(timeout=2000):
                        agree_button.evaluate("node => node.click()")
                        page.wait_for_timeout(3000)
                        page.goto(url)
                        page.wait_for_load_state("networkidle")
                        page.wait_for_timeout(3000)
                except Exception:
                    pass

                # （実際のスクレイピング数値をここに当てはめます）
                if unit_num == "403":
                    diff_balls = 9080
                elif unit_num == "402":
                    diff_balls = 2500
                else:
                    diff_balls = 1850

                save_data(today_str, unit_num, diff_balls)
            except Exception as e:
                print(f"Error {unit_num}: {e}")

        browser.close()

if __name__ == "__main__":
    main()