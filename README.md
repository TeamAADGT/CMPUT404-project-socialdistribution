CMPUT404-project-socialdistribution
===================================

CMPUT404-project-socialdistribution

See project.org (plain-text/org-mode) for a description of the project.

Make a distributed social network!

Contributors / Licensing
========================

Generally everything is LICENSE'D under the Apache 2 license by Abram Hindle.

All text is licensed under the CC-BY-SA 4.0 http://creativecommons.org/licenses/by-sa/4.0/deed.en_US


Contributors:

    Karim Baaba
    Ali Sajedi
    Kyle Richelhoff
    Chris Pavlicek
    Derek Dowling
    Olexiy Berjanskii
    Erin Torbiak
    Abram Hindle
    Braedy Kuzma
    Adam Ford
    Alanna McLafferty
    David Yee
    Gaylord Mbuyi
    Tiegan Bonowicz

Team Members
============

* Adam Ford (ajford@ualberta.ca)
* Alanna McLafferty (mclaffer@ualberta.ca)
* David Yee (dvyee@ualberta.ca
* Gaylord Mbuyi (gaylord@ualberta.ca)
* Tiegan Bonowicz (tiegan@ualberta.ca)

Video
=====

https://archive.org/details/cmput404video

Project API
===========

* Service Address: `https://aadgt-404-master.herokuapp.com/service/`
* Port: 443
* Hostname: `aadgt-404-master.herokuapp.com`
* Prefix: `service/`

Basic Authentication: Credentials are generated on a node-by-node basis. Please contact one 
of the team members listed above to add your node.

API Documentation
=================

View API documentation at: https://aadgt-404-master.herokuapp.com/service/docs/

To view non-public endpoints, click on the "Authorize" button on the top-right, and enter the following credentials:

* username: api        
* password: api

AJAX
====

AJAX was used to implement the Follow, Unfollow, and Send Friend Request buttons on the Author Detail page.

The endpoints used internally are documented (and notes where specifically they are used) in the API documentation referenced above, in the "internal" section.

Unimplemented User Stories
==========================

* As an author, I want to un-befriend local and remote authors

Project Management
==================

* [User Story Ranking and Project Milestone Planning (Google Sheets)](https://docs.google.com/spreadsheets/d/1cJCfzLqsmpnJd4xiAdVyMDdLkoQ1MP6Rk7lP-_9abBI/edit?usp=sharing)

* [Project Management and Sprint Planning (Pivotal Tracker)](https://www.pivotaltracker.com/n/projects/1975357)

Sources
=======

* heroku-django-template (MIT): https://github.com/heroku/heroku-django-template

* Django Login

  * Django Login System ideas by Vitor Freitas:
    https://simpleisbetterthancomplex.com/tutorial/2016/06/27/how-to-use-djangos-built-in-login-system.html

  * Django AuthRequiredMiddleware (http://stackoverflow.com/a/21123660/2557554; 
    http://stackoverflow.com/a/40873794/2557554) by 
    Dimit3y (http://stackoverflow.com/users/1234326/dmit3y) and 
    conner.xyz (http://stackoverflow.com/users/2836259/conner-xyz) and licensed 
    under CC-BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/deed.en)

  * Django Registration by James Bennet (BSD):
    https://github.com/ubernostrum/django-registration

  * Django registration form template inspired from 
    https://github.com/macdhuibh/django-registration-templates/blob/master/registration/registration_form.html

  * UserProfile ideas by Alon Swartz (https://www.turnkeylinux.org/users/alon)
    from https://www.turnkeylinux.org/blog/django-profile

* Bootstrap framework is licensed under the MIT license 
  http://getbootstrap.com/

* django-widget-tweaks for front-end UI styling with Bootstrap 
  https://pypi.python.org/pypi/django-widget-tweaks and licensed under the MIT 
  license

* Form styling code based on code written by Vitor Freitas from 
  https://simpleisbetterthancomplex.com/2015/12/04/package-of-the-week-django-widget-tweaks.html
  
* Form success message code based on code written by 
  damio (http://stackoverflow.com/users/1075195/damio) from http://stackoverflow.com/a/38897952/2557554 and licensed under the MIT license

* Admin dashboard styling idea from 
  Reto Aebersold (http://stackoverflow.com/users/286432/reto-aebersold) from
  http://stackoverflow.com/a/24983231/2557554 and licensed under 
  CC-BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/deed.en)

* Django REST Framework (BSD-2-Clause)
  http://www.django-rest-framework.org/

* Django adding comments to a post is based on tutorial by Django Girls from
  https://djangogirls.gitbooks.io/django-girls-tutorial-extensions/homework_create_more_models/
  visited on Thursday March 9th, License: Creative Commons Attribution-ShareAlike 4.0

* Django adding images to a post is based on code by thenewbosten,
  url:https://www.youtube.com/watch?v=v5FWAxi5QqQ&index=33, license: Standard YouTube License,
  visited on Thursday March 8th

* Django adding images to a post is also based on code by CodingEnterpreters,
  url: https://www.youtube.com/watch?v=Rr1-UTFCuH4, license: Standard YouTube License,
  visited on Thursday March 8th

* Djanjo adding attribute value from options, usage found in Django Docs,
  url: https://docs.djangoproject.com/en/dev/ref/models/fields/#choices, License: not listed

* jQuery Shorten is licensed under the MIT license  
  https://github.com/viralpatel/jquery.shorten

* Masonry is licensed under the MIT license  
  http://masonry.desandro.com/

* The JavaScript Cookie library (js.cookie.js) is licensed under the MIT license
  https://github.com/js-cookie/js-cookie/

* CommonMark-py (https://github.com/rtfd/CommonMark-py) licensed under BSD-3-Clause

* Authorship test idea from http://stackoverflow.com/a/28801123/2557554
  Code from mishbah (http://stackoverflow.com/users/1682844/mishbah)
  Licensed under CC-BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/deed.en)

* Testing with RequestFactory (https://docs.djangoproject.com/en/1.10/topics/testing/advanced/)

* Pre-save code based on idea by 
  Bernhard Vallant (http://stackoverflow.com/users/183910/bernhard-vallant)
  from http://stackoverflow.com/a/6462188/2557554 and licensed under 
  CC-BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/deed.en)

* Python Requests library (http://docs.python-requests.org/) is licensed under 
  the Apache 2.0 license.

* Environment variable idea by 
  Danilo Bergen (http://stackoverflow.com/users/284318/danilo-bargen) 
  From http://stackoverflow.com/a/11189383/2557554 and licensed under 
  CC-BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/deed.en)

* How to pass argument to reverse
  By igor(https://stackoverflow.com/users/978434/igor)
  On StackOverflow url: https://stackoverflow.com/questions/15703475/how-to-make-reverse-lazy-lazy-for-arguments-too
  License: CC-BY-SA 3.0
