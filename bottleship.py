#!/usr/bin/env python3

from flask import Flask, g, current_app, render_template, request, flash, session, abort, url_for, redirect, send_from_directory

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.whooshee import Whooshee
import whoosh.index
#from flask.ext.cache import Cache

from sqlalchemy import desc
from datetime import datetime

import whirlpool as Whirlpool
import markdown2
import os

from functools import wraps

#import backend
#User,Post,Category

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

import os

app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{user}:{passwd}@{host}/{db}'.format(user=os.environ['BOTTLESHIP_DB_USER'],passwd=os.environ['BOTTLESHIP_DB_PASSWORD'],host=os.environ['BOTTLESHIP_DB_HOST'],db=os.environ['BOTTLESHIP_DB_NAME'])
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['BOTTLESHIP_SALT'] = 'b4fa258d43dece6aeb4f4f3ae2814874'.encode()
app.config['BOTTLESHIP_POSTS_PER_PAGE'] = 5
app.config['BOTTLESHIP_PROJECTS_PER_PAGE'] = 4
app.config['WHOOSHEE_DIR'] = 'storage/whoosh'

app.secret_key = bytearray(os.environ['BOTTLESHIP_DB_USER'])

db = SQLAlchemy(app)
whooshee = Whooshee(app)


import argparse

parser = argparse.ArgumentParser(description='Make the bottleship float')
parser.add_argument('-d', '--debug', dest='debug', action='store_true', default="false",
	                help='enable debug')
parser.add_argument('-p', '--port', dest='port', type=int, action='store', default=8080,
	                help='which port to serve on (default: 8080)')


################################################################################


#@auth.get_password
#def get_password(username):
#	user = User.query.filter(User.username==username).first()
#	x = (user!=None)
#	print ("xxx %s  -- b==%s" % (username, x))
#	if not user:
#		return False
#	print ("yyy %s  -- %s" % (username,user.secret.encode('utf-8')))
#	return user.secret


#@auth.error_handler
#def auth_err():
#	return "<body><p>Too much Wodka. *Ürps*.</p></body>"





###############################################################################
def render_md(content):
	   if not isinstance(content,str):
			   return None
	   return markdown2.markdown(content,extras=['footnotes','fenced-code-blocks'])


###############################################################################




# pygments for code
#@app.template_filter()
def code_highlight(code, lang, style='default', lineos=True):
	lexer = get_lexer_by_name(lang, stripall=False)
	formatter = HtmlFormatter(linenos=lineos, cssclass="source")
	code = highlight(code, lexer, formatter)
	return code


import models


#cache = Cache(app,config={'CACHE_TYPE': 'simple'})

### jinja2 custom filters

@app.template_filter("datetimeformat")
def datetimeformat(value, format='%b %d, %Y'):
	return value.strftime(format)







@app.route("/login", methods=["POST","GET"])
def login():
	if request.method == "POST":
		username = request.form['username']
		password = request.form['password']
		user = User.query.filter(User.username==username).first()
		if user and user.check_passwd(password):
			session['active'] = True
			session['who'] = user.username
			flash("That was correct.")
			return redirect(url_for('index'))
		else:
			flash("That username or passwd was wrong.")
	return render_template('login.html')

def login_session_test():
	"""Test if user is logged in."""
	return session.get('active') and session.get('who')



def login_required(func):
	"""Decorator for views that require login."""
	@wraps(func)
	def decorator(*args, **kwargs):
		if not login_session_test():
			print ("Not logged in - redirect to /login")
			flash ("Well that was wrong. Chicken winner. No more dinner.")
			return redirect(url_for('login'))
		print ("Logged in, do what needs to be done.")
		return func(*args, **kwargs)
	return decorator


@app.route("/logout", methods=["GET"])
@login_required
def logout():
	session.pop('active',None)
	session.pop('who',None)
	flash ('Bye!')
	return redirect(url_for('index'))


@app.route("/write/<string:context>", methods=['GET'])
@login_required
def write_entry(context):
	if context == "project":
		return render_template('writeproject.html')
	elif context == "blog":
		return render_template('writepost.html')

	flash ("GET: Unknown context %s" % str(context))
	return redirect(url_for('index'))



@app.route('/add/<string:context>', methods=['POST'])
@login_required
def write_entry_add(context):

	author = User.query.filter(User.username==session.get('who')).first()
	if context == "blog":
		try:
			entry = Post(slug=request.form['slug'],\
						 body=request.form['body'],\
						 title=request.form['title'],\
						 author=author,\
						 date=None)
			db.session.add(entry)
			db.session.commit()
			flash('New entry/post was successfully posted')
		except:
			flash('Some constraint may not be met.')

	elif context == "project":
		try:
			entry = Project(slug=request.form['slug'],\
							readme=request.form['readme'],\
							name=request.form['name'],\
							author=author,\
							date=None)
			db.session.add(entry)
			db.session.commit()
			flash('New entry/project was successfully posted')
		except:
			flash('Some constraint may not be met.')

	else:
		flash ("POST: Unknown context %s" % str(context))

	return redirect(url_for('index'))



@app.route('/update/<string:context>/<string:slug>', methods=['POST'])
@login_required
def edit_entry_update(context,slug):

	entryid = session['entry_id']
	if not entryid or entryid==0:
		flash('No valid '+context+' id specified, seems something went wrong. Very wrong.')
		return redirect(url_for('index'))

	if context == 'blog':
		entry = Post.query.get(entryid)
		entry.slug=request.form['slug']
		entry.title=request.form['title']
		entry.body=request.form['body']
		entry.html=None
	elif context == 'project':
		entry = Project.query.get(entryid)
		entry.slug=request.form['slug']
		entry.name=request.form['name']
		entry.readme=request.form['readme']
		entry.html=None
	else:
		flash('No valid '+context+' with that id, seems something went wrong. Very wrong.')
		return redirect(url_for('index'))
	db.session.commit()
	flash('Record got updated')
	return redirect('/'+context+'/'+slug)


@app.route("/edit/<string:context>/<string:slug>", methods=['GET'])
@login_required
def edit_entry(context,slug):
	entry = None
	if context == "blog":
		entry = Post.query.filter(Post.slug==slug).first()
	elif context == 'project':
		entry = Project.query.filter(Project.slug==slug).first()
	if not entry:
		flash ("No such slug known. Typo?")
		return redirect(url_for('index'))

	session['entry_id'] = entry.id

	return render_template ('edit'+context+'.html', entry=entry, authorized=login_session_test())

@app.route("/del/blog", methods=['POST'])
@app.route("/del/blog/", methods=['POST'])
@app.route("/del/blog/<int:id>", methods=['POST'])
@login_required
def delete_for_real(id):
	post = Post.query.filter(Post.id==id).first()
	if not post:
		flash ("No such Post id. Something is wrong.")
		return redirect(url_for('index'))
	try:
		db.session.delete(post)
		db.session.commit()
		flash ("Post successfully deleted.")
	except:
		flash ("Post could not be deleted. Something went wrong.")


	return redirect(url_for('index'))


@app.route("/del/blog/<string:slug>", methods=['GET'])
@login_required
def delete_confirm_page(slug):
	post = Post.query.filter(Post.slug==slug).first()
	if not post:
		flash ("No such slug known. Typo?")
		return redirect(url_for('index'))
	return render_template ('reconfirmdelete.html', slug=slug, post=post)


# simple what's my ip service
@app.route("/whatsmyip", methods=["GET","POST"])
@app.route("/whatismyip", methods=["GET","POST"])
@app.route("/getmyip", methods=["GET","POST"])
def whatsmyip():
	x = str(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
	if request.method=="POST":
		return x
	return render_template('whatsmyip.html',ipaddr=x)


##@cache.cached(timeout=600)
@app.route("/about", methods=["GET"])
def about():
	return render_template ('about.html')




##@cache.cached(timeout=120)
@app.route("/search", methods=["POST"])
@app.route("/search/<int:page>", methods=["POST"])
def search(page=1):
	searchwords = request.form['searchwords']
	if len(searchwords)<3:
		flash ("Search items need to be at least 3 characters long.")
		return redirect(url_for('index'))


	posts = Post.query.whooshee_search(searchwords).order_by(desc(Post.date)).paginate(page,app.config['BOTTLESHIP_POSTS_PER_PAGE'],False)
	print ("posts" + str(posts.items))
#	posts.items = Post.query.filter(Post.slug=="test").all()

	for post in posts.items:
		print ("Post found with title = '%s' " % (post.title))
		post.html = render_md(post.body)

	return render_template ('search.html', searchwords=searchwords, posts=posts, page=page)


##@cache.cached(timeout=600)
@app.route("/archive", methods=["GET"])
@app.route("/archive/<int:year>", methods=["GET"])
def archive(year=2014):
	posts = Post.query.order_by(desc(Post.date)).all()
	pmap = {}
	for post in posts:
		if post.date.year in pmap:
			pmap[post.date.year].extend([post])
		else:
			pmap[post.date.year] = [post]
	return render_template('archive.html', postmap=pmap, year=year)


# serve the post
##@cache.cached(timeout=120)
@app.route("/<int:year>/<int:month>/<int:day>/<string:slug>/")
@app.route("/<int:year>/<int:month>/<int:day>/<string:slug>")
@app.route("/blog/<string:slug>", methods=["GET"])
@app.route("/blog/<path:slug>", methods=["GET"])
@app.route("/tag/<path:slug>", methods=["GET"])
def blog(year=None,month=None,day=None,slug=None):
	obj = Post.query.filter(Post.slug == slug)
#	if year and month and day:
#		obj = obj.filter(Post.date == datetime(year,month,day))
	post = obj.first()
	if post:
		post.html = render_md(post.body)
		return render_template ('post.html', post=post)
	return render_template ('err.html', message="I'm sorry dave, I'm afraid I can't do that.")


@login_required
@app.route("/upload", methods=["GET","POST"])
def upload():
	if request.method == "POST":
		print ("content:" + str(request.files))
		flash ("uploading/uploaded foo?")
	return render_template ('upload.html')

@app.route("/<path:nowhere>", methods=["GET"])
def fallback(nowhere):
	return render_template ('err.html', message="I think you just got lost. Go back. There is nothing at \"/%s\"" % (nowhere))


def blogroll():
	with open ('blogroll.md', "r") as blogroll:
		data = blogroll.readline()








@app.route("/projects", methods=["GET"])
@app.route("/project", methods=["GET"])
@app.route("/projects/<int:page>", methods=["GET"])
@app.route("/project/<int:page>", methods=["GET"])
def projects(page = 1):
	projects = Project.query.paginate(page,app.config['BOTTLESHIP_PROJECTS_PER_PAGE'],False)
	for project in projects.items:
		project.html = render_md(project.readme)

	return render_template ('projects.html', projects=projects, page=page)

@app.route("/", methods=["GET"])
@app.route("/blog", methods=["GET"])
@app.route("/blog/<int:page>", methods=["GET"])
def index(page = 1):
	posts = Post.query.order_by(desc(Post.date)).\
			       paginate(page,app.config['BOTTLESHIP_POSTS_PER_PAGE'],False)
	if posts:
		for post in posts.items:
			post.html = render_md(post.body)

	return render_template ('index.html', posts=posts, page=page, authorized=login_session_test())



# serve the project
@app.route("/project/<string:slug>", methods=["GET"])
@app.route("/project/<path:slug>", methods=["GET"])
def project(slug):
	proj = Project.query.filter(Project.slug == slug).first()
	if proj:
		proj.html = render_md(proj.readme)
		return render_template ('project.html', project=proj)
	return render_template ('err.html', message="I'm sorry dave, I'm afraid I can't do that.")


#static fun
@app.route("/robots.txt", methods=["GET"])
def static_from_root():
	return send_from_directory(app.static_folder, request.path[1:])

#@app.route("/favicon.png", methods=["GET"])
@app.route("/favicon.ico", methods=["GET"])
def staticfun():
	return send_from_directory(app.static_folder, request.path[1:], mimetype='image/vnd.microsoft.icon')


####################################################################################################

def import_posts():
	for item in os.listdir('./import'):
		if os.path.isdir(item):
			continue

		with open('./import/'+item, 'r') as f:
			content = f.readlines()
		withmeta = ''.join(content)
		content = content[5:]
		content = ''.join(content)

		if not content:
			continue;
		x = markdown2.markdown(withmeta,extras=['footnotes','fenced-code-blocks','metadata'])

		print ("meta: " + str(x.metadata))
		print ("slug: "+str(x.metadata["slug"]))
		print ("title: "+str(x.metadata["title"]))
		print ("date: "+str(x.metadata["date"]))

		date=datetime.strptime(x.metadata["date"], "%Y-%m-%d %H:%M:%S")

		post = Post.query.filter(Post.slug==x.metadata["slug"]).first()
		if post:
			post.date = date
			post.title = x.metadata["title"]
			post.body = content
		else:
			post = Post(slug=x.metadata["slug"], title=x.metadata["title"], body=content, date=date)
			db.session.add(post)
		db.session.commit()


####################################################################################################

def float(port, debug):
	app.dabug = debug
	def refresh_index():
		try:
			ix = whoosh.index.open_dir(os.path.join(app.config['WHOOSHEE_DIR'],'post'))
			with ix.writer() as w:
				posts = Post.query.all()
				for post in posts:
					w.update_document(id=post.id, title=post.title, slug=post.slug, body=post.body)
				projects = Project.query.all()

			ix = whoosh.index.open_dir(os.path.join(app.config['WHOOSHEE_DIR'],'project'))
			with ix.writer() as w:
				posts = Project.query.all()
				for project in projects:
					w.update_document(id=project.id, name=project.name, slug=project.slug, readme=project.readme)

		except Exception as e:
			print ("Something when wrong when updating index" + str(e))

	def init():
		try:
			db.create_all()
		except:
			print ("DB Creation failed. Maybe DB is already present.")

		try:
			u = User(username=os.environ['BOTTLESHIP_ADMIN_NAME'],email=os.environ['BOTTLESHIP_ADMIN_EMAIL'], passwd=os.environ['BOTTLESHIP_ADMIN_PASSWORD'])
			db.session.add(u)
			db.session.commit()
		except Exception as e:
			pass

		refresh_index()

	def dummypost():
		try:
			u = User.query.filter(User.username==os.environ['BOTTLESHIP_ADMIN_NAME']).first()
			p = Post(slug="test",
					title="A demonstration post",
					body="with not thaaaaaaat much content, featuring *no more swearwords* and some inline `def pypy(code):\nprint(\"fun\")`",
					author=u,
					category=None,
					date=None)

			db.session.add(p)
			db.session.commit()
		except Exception as e:
			print("Failed to add demo post " + str(e))



	init()

	if debug:
		dummypost()
		app.run(host='127.0.0.1', port=port, debug=True)
		return

	from tornado.wsgi import WSGIContainer
	from tornado.httpserver import HTTPServer
	from tornado.ioloop import IOLoop

	self.server = HTTPServer(WSGIContainer(app))
	self.server.listen(port)
	IOLoop.instance().start()


if __name__ == "__main__":
	args = parser.parse_args()
	float(args.port, args.debug)
