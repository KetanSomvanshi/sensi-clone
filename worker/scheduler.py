from config.settings import CELERY
from worker.celery import celery_app

from worker.task_worker import trigger_underlyings_sync, trigger_derivatives_sync


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """This scheduler would periodically trigger the assigned task
    command to run scheduler - 'celery -A worker.scheduler beat' """
    sender.add_periodic_task(CELERY.trigger_freqn_for_underlying, trigger_underlyings_sync,
                             name='trigger_underlyings_sync')
    sender.add_periodic_task(CELERY.trigger_freqn_for_derivative, trigger_derivatives_sync,
                             name='trigger_derivatives_sync')
