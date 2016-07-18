FROM fedora:latest

MAINTAINER Bernhard Schuster <bernhard@ahoi.io>
RUN dnf update -y
RUN dnf install -y python3-tornado python3-flask-whooshee python3-flask python3-flask-sqlalchemy python3-flask-wtf python3-markdown2 python3-pygments

RUN mkdir -p /srv/bottleship
COPY bottleship.py /srv/bottleship/
COPY __init__.py /srv/bottleship/
COPY models.py /srv/bottleship/
COPY whirlpool.py /srv/bottleship/
COPY static /srv/bottleship/static
COPY templates /srv/bottleship/templates
RUN ls -al /srv/bottleship/ && chown root:root -Rf /srv/bottleship && chmod -w -Rf /srv/bottleship && chmod u+rw -Rf /srv/bottleship

EXPOSE 8080

CMD [ "/srv/bottleship/bottleship.py", "--port", "8080" ]

