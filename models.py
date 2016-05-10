from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
	__tablename__ = "user"
	id = Column(Integer, primary_key=True)
	username = Column(String(80), unique=True)
	email = Column(String(120), unique=True)
	secret = Column(String(64)) #byte array

	def __init__(self, username, email, passwd):
		self.username = username
		self.email = email
		self.secret = self.digest(passwd)

	def __repr__(self):
		return '<User %r>' % self.username

	def digest(self,passwd):
		whirl = Whirlpool.new()
		whirl.update(app.config['BOTTLESHIP_SALT'])
		whirl.update(passwd.encode())
		whirl.update(app.config['BOTTLESHIP_SALT'])
		return whirl.digest()


	def check_passwd(self,passwd):
		return self.digest(passwd) == self.secret


#class Category(Base):
#	__tablename__ = "Category"
#	id = Column(Integer, primary_key=True)
#	name = Column(String(50))

#	def __init__(self, name):
#		self.name = name

#	def __repr__(self):
#		return '<Category %r>' % self.name


class Post(Base):
	__tablename__ = "post"
	id = Column(Integer, primary_key=True)
	title = Column(String(80))
	body = Column(Text)
	date = Column(DateTime)
	slug = Column(String(30), unique=True)

	author_id = Column(Integer, ForeignKey('user.id'))
	author = relationship('User',
		backref=backref('posts', lazy='joined'))

#	category_id = Column(Integer, ForeignKey('category.id'))
#	category = relationship('Category',
#		backref=backref('posts', lazy='joined'))

	def __init__(self, slug, title, body, author=None, category=None, date=None):
		self.title = title
		self.body = body
		if date is None:
			date = datetime.utcnow()
		self.date = date
		self.category = category
		self.author = author
		self.slug = slug

	def __repr__(self):
		return '<Post %r>' % self.title



class Project(Base):
	__tablename__ = "project"
	id = Column(Integer, primary_key=True)
	name = Column(String(80))
	readme = Column(Text)
	editdate = Column(DateTime)
	slug = Column(String(30))

	author_id = Column(Integer, ForeignKey('user.id'))
	author = relationship('User',
		backref=backref('projects', lazy='joined'))

#	category_id = Column(Integer, ForeignKey('category.id'))
#	category = relationship('Category',
#		backref=backref('projects', lazy='joined'))

	def __init__(self, slug, name, readme, author, team=None, category=None, date=None):
		self.name = name
		self.readme = readme
		if date is None:
			date = datetime.utcnow()
		self.editdate = date
		self.category = category
		self.author = author
		self.slug = slug

	def __repr__(self):
		return '<Project %r>' % self.name

