from distutils.core import setup
setup(
  name = 'Pyhoot',         # How you named your package folder (MyLib)
  packages = ['Pyhoot'],   # Chose the same as "name"
  version = '1.0',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'A library for the Kahoot! Api interface',   # Give a short description about your library
  author = 'Maxgamertyper1',                   # Type in your name
  author_email = 'Maxa5302@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/maxgamertyper/Pyhoot/',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',    # I explain this later on
  keywords = ['Kahoot!', 'Kahoot', 'kahoot',"library","interface","api","python","Py 3.x"],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'websocket-client',
          'fake_useragent',
          'requests',
          'beautifulsoup4',
      ],
  classifiers=[
    "Development Status :: 5 - Production/Stable",      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which python versions that you want to support
    'Programming Language :: Python :: 3.12'
  ],
)
