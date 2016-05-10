#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from colorama import Fore, Back, Style


def copy_db(source_uri, sink_uri):

	source_engine = create_engine(source_uri, convert_unicode=True)
	source_session = scoped_session(sessionmaker(autocommit=False,
											 autoflush=False,
											 bind=source_engine))

	sink_engine = create_engine(sink_uri, convert_unicode=True)
	sink_session = scoped_session(sessionmaker(autocommit=False,
											 autoflush=False,
											 bind=sink_engine))
	# import all modules here that might define models so that
	# they will be registered properly on the metadata.  Otherwise
	# you will have to import them first before calling init_db()
	import models
	
	models.Base.metadata.create_all(bind=sink_engine)

#	import inspect
#	classes = [m for m in inspect.getmembers(models, inspect.isclass) if m[1].__module__ == 'models']

	for cls in [models.User, models.Post, models.Project]:
		print(Fore.RED + cls.__name__ + Fore.RESET)
		objs = source_session.query(cls).all()
		for obj in objs:
			print(obj)
			source_session.expunge(obj)
		sink_session.add_all(objs)
	sink_session.commit()
	sink_session.flush()

if __name__ == "__main__":

	import argparse

	parser = argparse.ArgumentParser(description='')
	parser.add_argument('-f', '--source', '--from', dest='source', type=str, action='store',
			            help='source db uri')
	parser.add_argument('-t', '--sink', '--to', dest='sink', type=str, action='store',
			            help='sink db uri')

	args = parser.parse_args()

	copy_db(args.source, args.sink)
