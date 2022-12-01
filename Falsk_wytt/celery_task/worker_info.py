from celery import Celery
from qts import create_app


def make_celery(app):
	celery = Celery(
		app.import_name,
		backend=app.config['CELERY_RESULT_BACKEND'],
		broker=app.config['CELERY_BROKER_URL']
	)
	celery.conf.update(app.config)

	# 将定时任务执行包装在app应用程序上下文中，这样就可以调用db，models
	class ContextTask(celery.Task):
		def __call__(self, *args, **kwargs):
			with app.app_context():
				return self.run(*args, **kwargs)

	celery.Task = ContextTask
	return celery


flask_app = create_app()
celery = make_celery(flask_app)

