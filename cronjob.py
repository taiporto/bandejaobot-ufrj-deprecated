# Package Scheduler.
from apscheduler.schedulers.blocking import BlockingScheduler

# Main cronjob function.
from main import cronjob

# Create an instance of scheduler and add function.
scheduler = BlockingScheduler({
  'apscheduler.timezone': 'America/Sao_Paulo'
})

scheduler.add_job(cronjob, "cron", hour=9, day_of_week='mon-sun')

scheduler.start()