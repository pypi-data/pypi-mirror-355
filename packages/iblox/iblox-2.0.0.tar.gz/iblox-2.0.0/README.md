![Logo](docs/source/_static/iblox.png "iblox")

A Python module for interacting with [Infoblox's WAPI](https://www.infoblox.com/).
It uses Python's request module to handle session caching and is very flexible.
We currently maintian compatibility with the [latest supported versions of Python!](https://devguide.python.org/versions/)

## License

[iblox][] is released under the [GNU Lesser General Public License v3.0][],
see the file LICENSE and LICENSE.lesser for the license text.

## Installation

The most straightforward way to get the iblox module working for you is:
```commandline
pip install iblox
```

This will ensure that all the requirements are met.

## Documentation

Documentation for the iblox module can be found at http://iblox.readthedocs.io/

You can build the documentation locally by running:
```commandline
make docs;
```

Then simply open `docs/build/html/index.html` in your browser.

## Contributing

Comments and enhancements are very welcome.

Report any issues or feature requests on the [BitBucket bug
tracker](https://bitbucket.org/isaiah1112/infoblox/issues?status=new&status=open). Please include a minimal
(not-) working example which reproduces the bug and, if appropriate, the
 traceback information.  Please do not request features already being worked
towards.

Code contributions are encouraged: please feel free to [fork the
project](https://bitbucket.org/isaiah1112/infoblox/fork) and submit pull requests to the **develop** branch.

## More information

- [Infoblox DDI](https://www.infoblox.com/)

[GNU Lesser General Public License v3.0]: http://choosealicense.com/licenses/lgpl-3.0/ "LGPL v3"

[iblox]: https://bitbucket.org/isaiah1112/infoblox "iblox Module"
