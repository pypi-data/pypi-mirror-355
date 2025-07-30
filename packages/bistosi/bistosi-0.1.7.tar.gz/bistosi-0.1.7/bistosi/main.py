from .celery_app import app


def send_email(sender, recipients, subject, html_content, group_uuid, send_at):
    app.send_task(
        "buzzbell.tasks.create_email_object_task",
        kwargs={
            "sender": sender,
            "recipients": recipients,
            "subject": subject,
            "html_content": html_content,
            "group_uuid": group_uuid,
            "send_at": send_at
        }
    )


def cancel_notification_by_group_uuid(group_uuid):
    app.send_task(
        "buzzbell.tasks.cancel_notification_by_group_uuid_task",
        kwargs={"group_uuid": group_uuid}
    )


def send_notice(sender, recipients, subject, linked_to, html_content, group_uuid, send_at):
    app.send_task(
        "buzzbell.tasks.create_notice_object_task",
        kwargs={
            "sender": sender,
            "recipients": recipients,
            "linked_to": linked_to,
            "subject": subject,
            "html_content": html_content,
            "group_uuid": group_uuid,
            "send_at": send_at
        }
    )


def send_sms(sender, recipients, content, group_uuid, send_at):
    app.send_task(
        "buzzbell.tasks.create_sms_object_task",
        kwargs={
            "sender": sender,
            "recipients": recipients,
            "content": content,
            "group_uuid": group_uuid,
            "send_at": send_at
        }
    )


def send_push_notification(sender, recipients, title, content, target, group_uuid, send_at):
    app.send_task(
        "buzzbell.tasks.create_push_notification_object_task",
        kwargs={
            "sender": sender,
            "title": title,
            "body": content,
            "target": target,
            "recipients": recipients,
            "group_uuid": group_uuid,
            "send_at": send_at
        }
    )
