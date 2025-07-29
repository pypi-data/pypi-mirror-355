from celery import Celery
from datetime import datetime
import traceback

from app.utils.email import send_email
from app.utils.logger import logger

# 初始化 Celery
celery = Celery(
    "celery_task",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/1"
)

# 持久化任务记录（内存示例，建议使用数据库）
email_log_db = []


@celery.task(name="send_email_task", bind=True, max_retries=2, default_retry_delay=10)  # 最多重试2次，间隔10秒
def send_email_task(self, to_email, subject, plain_body="", html_body="", attachments=None):
    task_info = {
        "to": to_email,
        "subject": subject,
        "status": "PENDING",
        "attempt": self.request.retries + 1,
        "created_at": datetime.utcnow().isoformat()
    }
    email_log_db.append(task_info)

    try:
        send_email(
            to_email=to_email,
            subject=subject,
            plain_body=plain_body,
            html_body=html_body,
            attachments=attachments
        )
        task_info["status"] = "SUCCESS"
        logger.info(f"Email sent successfully to {to_email}")

    except Exception as e:
        task_info["status"] = "RETRYING" if self.request.retries < self.max_retries else "FAILED"
        task_info["error"] = str(e)
        logger.error(f"Failed to send email to {to_email}: {e}")
        logger.debug(traceback.format_exc())

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        else:
            logger.warning(f"Email to {to_email} failed after max retries")
