"""
Scheduler Module
Runs automated daily research and outreach tasks
Owner: Md Jamil Islam
"""
import logging
import schedule
import time
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)


class AgencyScheduler:
    """
    Schedules and runs automated tasks for the agency research system.
    """

    def __init__(self):
        self.jobs = []
        self.running = False

    def add_daily_research(self, research_fn: Callable, hour: int = 9, minute: int = 0):
        """Schedule daily research at specified time."""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
            self._run_with_logging, "Daily Research", research_fn
        )
        logger.info(f"Scheduled daily research at {hour:02d}:{minute:02d}")

    def add_daily_outreach(self, outreach_fn: Callable, hour: int = 10, minute: int = 0):
        """Schedule daily outreach emails."""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
            self._run_with_logging, "Daily Outreach", outreach_fn
        )
        logger.info(f"Scheduled daily outreach at {hour:02d}:{minute:02d}")

    def add_weekly_report(self, report_fn: Callable, day: str = "monday", hour: int = 8):
        """Schedule weekly report generation."""
        getattr(schedule.every(), day).at(f"{hour:02d}:00").do(
            self._run_with_logging, "Weekly Report", report_fn
        )
        logger.info(f"Scheduled weekly report on {day} at {hour:02d}:00")

    def add_follow_up_check(self, follow_up_fn: Callable, interval_hours: int = 4):
        """Check for pending follow-ups every N hours."""
        schedule.every(interval_hours).hours.do(
            self._run_with_logging, "Follow-Up Check", follow_up_fn
        )
        logger.info(f"Scheduled follow-up check every {interval_hours} hours")

    def _run_with_logging(self, task_name: str, fn: Callable):
        """Run a task with logging and error handling."""
        logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Starting: {task_name}")
        try:
            fn()
            logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Completed: {task_name}")
        except Exception as e:
            logger.error(f"Task '{task_name}' failed: {e}")

    def run(self):
        """Start the scheduler loop."""
        self.running = True
        logger.info("Agency scheduler started. Press Ctrl+C to stop.")

        while self.running:
            schedule.run_pending()
            time.sleep(10)

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("Agency scheduler stopped.")
