import yaml
import os
import datetime,time
import logging.config

def init_log(file):

	cfg_path = os.path.join(os.path.dirname(__file__), 'log.yml')
	with open(cfg_path, 'r') as f:
		conf = yaml.safe_load(f.read())


	if 'handlers' in conf:
		tag = datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y%m%d%H%M')

		dict_h = conf['handlers']
		for h in dict_h:
			path = dict_h[h].get('filename', None)
			if path:
				f_path = os.path.dirname(path)
			
				if not os.path.exists(f_path):
					os.mkdir(f_path)
				f_name = '{}-{}'.format(file+"_"+tag, os.path.basename(path))
				dict_h[h]['filename'] = os.path.join(f_path, f_name)
	logging.config.dictConfig(conf)

#init_log()
import logging
logging.basicConfig(level = logging.INFO,format = '%(asctime)s/%(name)s/%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('connectionpool').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

Logging = logging.getLogger()

