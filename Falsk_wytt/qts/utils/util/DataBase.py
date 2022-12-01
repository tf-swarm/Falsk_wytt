# -*- coding: UTF-8 -*-
"""
data table

author  : keyouzhi
created : 2020-07-01
"""

from sqlalchemy.orm import sessionmaker, Session

class DaoBase(object):
	"""docstring for DaoBase"""
	def __init__(self,sm: sessionmaker):
		super(DaoBase, self).__init__()
		self.SessionMaker = sm 

	def _get_session(self) -> Session:
		return self.SessionMaker()


	def add_record(self, obj):
		s = self._get_session()
		if s:
			s.add(obj)
			s.commit()
		return obj if s else None
		


	