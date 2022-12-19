import schedule
import time

from functions import main


if __name__ == "__main__":
    schedule.every().hour.do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)
