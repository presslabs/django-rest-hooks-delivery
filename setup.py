from distutils.core import setup  # setuptools breaks

version = __import__('rest_hooks_delivery').VERSION

setup(
    name='django-rest-hooks-delivery',
    description=('Various webhook deliverers for django-rest-hooks and '
                 'django-rest-hooks-ng.'),
    version=version,
    author='PressLabs',
    author_email='ping@presslabs.com',
    url='http://github.com/PressLabs/django-rest-hooks-delivery',
    install_requires=['Django>=1.4', 'requests', 'django-jsonfield'],
    packages=['rest_hooks_delivery'],
    package_data={
        'rest_hooks': [
            'migrations/*.py'
        ]
    },
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],
)
