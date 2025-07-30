# djangoldp_blog

## Installation

How to install the project locally

1- create virtual environement
`python -m venv venv`

2- activate venv
`venv\Scripts\activate.bat`

3- update pip & wheel
`python -m pip install -U pip wheel`

4- install djangoldp V2
`pip install djangoldp`

5- init server 
`djangoldp initserver [SERVER NAME]`

7- update settings.yml
dependencies: 
  - django-tinymce

ldppackages: 
  - djangoldp_blog

8- create a virtual link in sibserver : 
ln -s ../djangoldp-blog/djangoldp_blog djangoldp_blog

9- install the server in sibserver:
`djangoldp install`

10- install all packages
`djangoldp configure`

11- create rsa key
`python manage.py creatersakey`

12- launch the server
`djangoldp runserver`

## congrats ! You've made it. :)

It should be ok.