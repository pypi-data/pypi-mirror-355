Bitbucket Pipes Toolkit
=======================

![Coverage](https://bitbucket.org/bitbucketpipelines/bitbucket-pipes-toolkit/downloads/coverage.svg)

This package contains various tools and helpers to make it more fun and easy for people to develop pipes. This includes improved colorized logging, shared data interface, array variables helpers and more.

Installation
============

`pip install bitbucket-pipes-toolkit`


Examples
========

Simple pipe example
```python3
import os

from bitbucket_pipes_toolkit import Pipe


class MyPipe(Pipe):
    def run(self):
        super().run()
        print("I'm a simple little pipe")


# below is a simple schema for pipe variables.
schema = {'USERNAME': {'required': True, 'type': 'string'},
          'PASSWORD': {'required': True, 'type': 'string'}}

pipe_metadata = {
    'name': 'My Pipe',
    'image': 'my-docker-image:latest'
}

# Set environment variables required in schema.
os.environ['USERNAME'] = 'user'
os.environ['PASSWORD'] = 'pwd'

my_pipe = MyPipe(pipe_metadata=pipe_metadata, schema=schema)
my_pipe.run()
```

Documentation
=============

For more details have a look at the [official documentation](https://bitbucket-pipes-toolkit.readthedocs.io).


Support
=======
If you’d like help with the toolkit, or you have an issue or feature request, let us know on [Community](https://community.atlassian.com/t5/forums/postpage/board-id/bitbucket-pipelines-questions?add-tags=pipes,toolkit).

If you’re reporting an issue, please include:

* the version of the toolkit
* relevant logs and error messages
* steps to reproduce
