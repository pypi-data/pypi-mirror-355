#######################
sphinxcontrib-asciiart
#######################

http://packages.python.org/sphinxcontrib-asciiart

A Sphinx_ extension, which turns ascii art color sequences in Sphinx documents
into colored HTML or .png or other output.

.. _`Sphinx`: http://sphinx.pocoo.org/latest

Installation
============

This extension can be installed from the Python Package Index::

   pip install sphinxcontrib-asciiart

Usage
=====

Just add ``sphinxcontrib.asciiart`` to the list of extensions in the
``conf.py`` file. For example::

    extensions = ['sphinxcontrib.asciiart']

And then use the asciiart block to include your ascii art code::

    .. asciiart::
        :line-height: 1.0em
        :spacing: 0

        [31m                                              :. ,..[0m
        [31m                                            .' :~.':_.,[0m
        [31m                                          .'   ::.::'.'[0m
        [31m                                         :     ::'  .:[0m
        [31m                                       `.:    .:  .:/[0m
        [31m                                        `::--.:'.::'[0m
        [31m                                          |. _:===-'[0m
        [32m                                        / /[0m
        [32m                       ,---.---.    __,','[0m
        [32m                      (~`.  \   )   )','.,---..[0m
        [32m                       `v`\ | ,' .-'.:,'_____   `.[0m
        [32m                           )|/.-~.--~~--.   ~~~-. \[0m
        [32m                         _/-'_.-~        ""---.._`.|[0m
        [32m                    _.-~~_.-~                    ""'[0m
        [32m             _..--~~_.(~~[0m
        [32m  __...---~~~_..--~~[0m
        [32m'___...---~~~[0m


Then it would be rendered as a colorful literal block or image. To show the
content of the pypi webpage, I remove the colors::

                                                  :. ,..
                                                .' :~.':_.,
                                              .'   ::.::'.'
                                             :     ::'  .:
                                           `.:    .:  .:/
                                            `::--.:'.::'
                                              |. _:===-'
                                             / /
                            ,---.---.    __,','
                           (~`.  \   )   )','.,---..
                            `v`\ | ,' .-'.:,'_____   `.
                                )|/.-~.--~~--.   ~~~-. \
                              _/-'_.-~        ""---.._`.|
                         _.-~~_.-~                    ""'
                  _..--~~_.(~~
       __...---~~~_..--~~
    ,'___...---~~~

Options
=======

sphinxcontrib-asciiart provide rich options to custimize the output. You can
configure the global setting, you also can change the behavior for only one
ascii art literal block.

When the global setting and literal block based setting are change, or if the
content of the literal block is changed, it would re-build the target image
even there is target image cache already.

global setting
--------------

First of all, you should configure the sphinxcontrib-asciiart in the conf.py
to enable the sphinxcontrib-asciiart::

    extensions = ['sphinxcontrib-asciiart']

* ascii_art_output_format: We use the suffix to control the build output format
  for different target. The default value is as below and you can change it in
  your conf.py in the following format::

    ascii_art_output_format = dict(html='.html', latex='.png', text='.txt')

Besides the .png, we support many other kinds of image output format::

    bmp dib eps gif icns ico im jpg jpeg msp pcx png ppm sgi spider tga tiff
    webp xbm palm pdf xv bufr fits grib hdf5 mpeg

* ascii_art_image_font: When we render the image instead of ".html" and ".txt",
  which font name we use, It's a list of font name that we want to use to
  render the ascii art. The front one have high priority to be used. the
  default is::

    ascii_art_image_font = 'NSimSun, simsun, monospace'

* ascii_art_image_fontsize: When we render the image instead of ".html" and
  ".txt", the font size we want to use, it's an integer, the default value is::

    ascii_art_image_fontsize = 14

block specific setting
----------------------

* 'spacing': int, The space between each lines. The default value is -1.
* 'font': str, A list of font name that we want to use to render the ascii art. The front one have high priority to be used.
* 'fontsize': int, The font size we want to use to render the ascii art.
* 'include': Use the content of the file given in include as ascii content.
* 'textwidth': The maxmium seen character number in each lines. Lines longer than that would case line break. Default is 0 and 0 means never line break.
* 'leadingspace': When textwidth option is given, then the wrapped text would start at leadingspace.

For example::

    .. asciiart::
        :font: simsun, monospace, "Times new roman"
        :fontsize: 14
        :spacing: 0

        .· .·.   [1;35m/╲     /|[0m
                ·[1;35m│  \  ╱ |[0m
           [1;35m\-.___ / \  \/ / /[0m
            [1;35m\ __ ╲  [1;33m.,.[1;35m| ╱__[0m
            [1;35m╱  乁  [1;33m'\|)[1;35m╱￣  ╲[0m
        [1;35m-＜`︶╲__╱ [1;33m︶[1;35m╲    ╲ \[0m
            [35m￣￣ /   /  ╱﹀乀 \│[0m
                 [1;35m╲  ' /[1;30m╲  ·╲/[0m
                   [1;35m\| /   [1;30m\  ; ｀[0m
                    [1;35m\/     [1;30m\  ·,[0m
        .----/[1;35m      ′      [1;30m︳  ·__,[0m


Changelog
============

#. 1.0.0 Initial upload.
#. 1.1.2 Support new options: textwidth, include
