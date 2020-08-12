from setuptools import setup

version = __import__('rest_hooks_delivery').VERSION

setup(
    name='django-rest-hooks-delivery',
    description=('Various webhook deliverers for django-rest-hooks and '
                 'django-rest-hooks-ng.'),
    version=version,
    author='PressLabs',
    author_email='ping@presslabs.com',
    url='http://github.com/PressLabs/django-rest-hooks-delivery',
    install_requires=['Django>=2.2', 'requests', 'django-jsonfield'],
    packages=['rest_hooks_delivery'],
    include_package_data=True,
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],
)
