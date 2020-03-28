#!/usr/bin/env python
# coding=UTF-8
'''
@Author: LogicJake, Jacob
@Date: 2019-03-24 16:35:24
@LastEditTime: 2020-03-01 15:02:28
'''
from datetime import datetime

from sqlalchemy import event

from config import logger

from .. import db


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    url = db.Column(db.String(128), nullable=False)
    selector_type = db.Column(db.String(32), nullable=False, default='xpath')
    selector = db.Column(db.String(128), nullable=False)
    is_chrome = db.Column(db.String(32), nullable=False, default='no')
    frequency = db.Column(db.Integer, nullable=False, default='5')
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    # 通知方式
    mail = db.Column(db.String(32), nullable=False, default='no')
    wechat = db.Column(db.String(32), nullable=False, default='no')
    pushover = db.Column(db.String(32), nullable=False, default='no')
    # 高级设置
    regular_expression = db.Column(db.String(128))
    rule = db.Column(db.String(128))
    headers = db.Column(db.String(1024))


def after_insert_listener(mapper, connection, target):
    from app.main.scheduler import add_job

    add_job(target.id, target.frequency)

    from app.models.task_status import TaskStatus
    task_status = TaskStatus.__table__
    connection.execute(task_status.insert().values(task_id=target.id,
                                                   task_name=target.name))


def after_update_listener(mapper, connection, target):
    from app.main.scheduler import add_job, remove_job

    remove_job(target.id)
    from app.models.task_status import TaskStatus
    task_status = TaskStatus.__table__
    connection.execute(task_status.update().values(
        task_name=target.name, last_status='更新任务成功', last_run=datetime.now(),
        task_status='run').where(TaskStatus.task_id == target.id
                                 and TaskStatus.task_type == 'html'))

    add_job(target.id, target.frequency)
    logger.info('task_{}更新'.format(target.id))


def after_delete_listener(mapper, connection, target):
    from app.main.scheduler import remove_job

    remove_job(target.id)

    from app.models.task_status import TaskStatus
    task_status = TaskStatus.__table__
    connection.execute(task_status.delete().where(
        TaskStatus.task_id == target.id and TaskStatus.task_type == 'html'))

    from app.models.content import Content
    content = Content.__table__
    connection.execute(content.delete().where(Content.task_id == target.id
                                              and Content.task_type == 'html'))

    logger.info('task_{}删除'.format(target.id))


event.listen(Task, 'after_insert', after_insert_listener)
event.listen(Task, 'after_update', after_update_listener)
event.listen(Task, 'after_delete', after_delete_listener)
