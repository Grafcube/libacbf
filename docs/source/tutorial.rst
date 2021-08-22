Quick Tutorial
==============

Read a book
-----------
Use it with a context manager:

.. code-block:: python

    from libacbf import ACBFBook

    with ACBFBook("path/to/book.cbz") as book:
        # Read English title of book
        title = book.book_info.book_titles["en"]

Alternatively just open and close it:

.. code-block:: python

    from libacbf import ACBFBook

    book = ACBFBook("path/to/book.cbz")
    # Read English title of book
    title = book.book_info.book_titles["en"]
    book.close()

You can read plain ``.acbf`` XML formatted files, Zip archives, 7Zip archives, Tar archives or RAR
archives.

Metadata
~~~~~~~~
It is recommended that you skim through the API Reference at least once. Specifically ACBFBook,
Book Info, Publisher Info and Document Info to see all the metadata you can read.

.. code-block:: python

    book.book_info  # Read metadata from the book info section
    book.publish_info  # Read metadata from the publisher info section
    book.document_info  # Read metadata from the document info section

Body
~~~~
(Read ACBFBody in the API Reference)

It contains a list of pages that you can read info from.

.. code-block:: python

    for page in book.body.pages:
        page  # A page object with information
        page.image  # Get the image data from its source.

Data
~~~~
(Read ACBFData in the API Reference)

Files can be embedded within the plain XML book. You can use
this to list and read the embedded data.

.. code-block:: python

    book.data.list_files()

Styles
~~~~~~
(Read Styles in the API Reference)

Stylesheets can be used with an ACBF formatted book. Styles can
be embedded in a style tag, in the data section or be a reference to another file either in an archive
or a path on disk.

.. code-block:: python

    book.styles.list_styles()

Edit/Create Books
-----------------
(See ACBFBook for detailed information)

You can use different modes to open books.

.. code-block:: python

    from libacbf import ACBFBook

    # Edit an existing file.
    with ACBFBook("path/to/book.cbz", 'a') as book:
        # Edit the English title of the book
        book.book_info_book_titles["en"] = "New title"

You can create new files with other modes. ``'w'`` will create a new file at the given path. If a file
already exists it will be overwritten so be careful. ``'x'`` will also create a new file but raises
``FileExistsError`` if a file already exists.

.. code-block:: python

    from libacbf import ACBFBook

    # Creates a new book. Overwrites if a file already exists.
    with ACBFBook("path/to/file.cbz", 'w') as book:
        # Set the English title of the new book
        book.book_info.book_titles["en"] = "Newly created book"

    # Creates a new book. Raises an exception if a file already exists.
    with ACBFBook("path/to/file.cbz", 'x') as book:
        # Set the English title of the new book
        book.book_info.book_titles["en"] = "Newly created book"

By default, the book will be a Zip archive. You can override this with the nullable ``archive_type``
parameter. Accepted values can be found in the API Reference. This parameter is ignored when using
``'r'`` or ``'a'`` mode.

Passing ``None`` creates a plain text XML formatted book. You can convert it to an archive
later if you want using ``ACBFBook.make_archive(...)``. You cannot create Rar archived books.

.. warning::
    You will lose information like compression level etc. when you edit and/or create a book as
    it re-archives the book using the default values for each archive type. Information on how to
    avoid this is available further below.

.. code-block:: python

    from libacbf import ACBFBook

    # Creates a Zip archived book
    with ACBFBook("path/to/file.cbz", 'w', archive_type="Zip") as book:
        book.book_info.book_titles["en"] = "CBZ book"

    # Creates a 7Zip archived book
    with ACBFBook("path/to/file.cb7", 'w', archive_type="SevenZip") as book:
        book.book_info.book_titles["en"] = "CB7 book"

    # Creates a Tar archived book
    with ACBFBook("path/to/file.cbt", 'w', archive_type="Tar") as book:
        book.book_info.book_titles["en"] = "CBT book"

    # Creates a plain XML book
    with ACBFBook("path/to/file.acbf", 'w', archive_type=None) as book:
        book.book_info.book_titles["en"] = "ACBF book"

        # This can be converted to an archive later
        # An exception is raised if the book is already an archive

        # Convert to CBZ
        book.make_archive()
        -- OR --
        book.make_archive("Zip")

        # Convert to CB7
        book.make_archive("SevenZip")

        # Convert to CBT
        book.make_archive("Tar")

Edit Book Data
--------------
``ACBFBook.book_info.genres`` is a dictionary with keys being enum values. You can edit it by doing
this:

.. code-block:: python

    from libacbf import ACBFBook
    from libacbf.constants import Genres

    with ACBFBook("path/to/file.cbz", 'a') as book:
        # Get the match value of the genre if it exists
        match = book.book_info.genres[Genres.other]

        # Add a new genre if it doesn't already exist and set no match value
        book.book_info.genres[Genres.humor] = None

        # Add a genre and set its match value to 90%
        book.book_info.genres[Genres.manga] = 90

Or you could do this:

.. code-block:: python

    from libacbf import ACBFBook

    with ACBFBook("path/to/file.cbz", 'w') as book:
        # Get the match value of the genre if it exists
        match = book.book_info.get_genre_match("other")

        # Add a new genre if it doesn't already exist and set no match value
        book.book_info.edit_genre("humor")

        # Add a genre and set its match value to 90%
        book.book_info.edit_genre("manga", 90)

Similarly you can add an author object to ``ACBFBook.document_info.authors``.

Importing Author:

.. code-block:: python

    from libacbf import ACBFBook
    from libacbf.metadata import Author

    with ACBFBook("path/to/file.cbz", 'w') as book:
        book.document_info.authors.append( Author("Nickname") )

Directly:

.. code-block:: python

    from libacbf import ACBFBook

    with ACBFBook("path/to/file.cbz", 'w') as book:
        book.document_info.add_author("Nickname")

There are many functions available that simplify editing, allowing you to edit information without
having to import additional classes.

Adding Pages
------------
Adding pages may take one or two steps.

First let's append a page to the book.

.. code-block:: python

    from libacbf import ACBFBook

    with ACBFBook("path/to/file.cbz", 'w') as book:
        book.body.append_page("page1.png")

The page is now referencing an image relative to the root of the Zip archive. If the archive already
has this image then you're done. If it doesn't, you have to write it to the archive.

.. code-block:: python

        # ... continued
        book.data.add_data("path/to/image/page1.png")

This will write the image stored on disk into the archive with the path ``"page1.png"`` relative to
the root of the archive. There is more information on what you can do with this function in the API
reference.

How to avoid losing the original compression of an archive
----------------------------------------------------------
Regardless of whether you open a book in ``'w'``, ``'a'`` or ``'x'`` mode, it is saved with the
default options of its archive type. So for example, if your CBZ book uses ``ZIP_DEFLATE`` compression,
opening it will extract and re-archive it as ``ZIP_STORED`` because that is the default. Books opened
with ``'r'`` do not affect the original file in any way.

To get around this, you can manage the archive manually. Image references in pages are relative to
the root of the archive and the ``.acbf`` file must also be at the root of the archive. If you extract
the contents of the archive to a directory, the image references will be relative to the ACBF file
and it will still retrieve the correct image. You can then edit the book as usual. The only difference
would be that writing a file to the archive means copying the file into the extracted directory.

After you're done you can archive the contents of the directory with the settings you want and read
the archived book normally.
