Fancy Tasklists for Markdown-IT-Py
==================================

This is a plugin for the Python implementation of
`Markdown-IT <https://github.com/executablebooks/markdown-it-py>`_ (a CommonMark
parser) that provides "fancy" tasklists (or checkboxes).

In particular, it allows you to use (almost) any character to "check" the
checkbox, and then, through the use of CSS, change the displayed checkbox.
Sample CSS is included. (If the character you want to use doesn't currently
work, please submit a Pull Request to add it!)

This is inspired by my use of Obsidian, where many fancy checkboxes are
provided by many themes. This seems to have come through implementing things
like *Bullet Journal* in Obsidian. What brought me to create this was a desire
to create a Pelican site out of my Markdown Obsidian notes.

This doesn't include the CSS to change the display of the checkboxes to
"fancy"; if you need example code, there is some in my Pelican theme, `seafoam`
(see `custom-checkboxes.less
<https://github.com/MinchinWeb/seafoam/blob/master/css_src/less/custom-checkboxes.less>`_).

.. image:: https://github.com/MinchinWeb/seafoam/raw/master/docs/screenshots/2.10.0/fancy-checkboxes.png
    :align: center
    :alt: Fancy Checkboxes, using Seafoam theme
