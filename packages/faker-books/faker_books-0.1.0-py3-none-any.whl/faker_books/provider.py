from random import choice

from faker.providers import BaseProvider

from ._genres import genre_list
from ._titles import title_list
from ._authors import author_list
from ._publishers import publisher_list


class BookProvider(BaseProvider):
    """
    A provider for book-related data.

    example usage:
    >>> from faker import faker
    >>> from faker_books import BookProvider
    >>> fake = Faker()
    >>> fake.add_provider(BookProvider)
    >>> fake.book_genre()
    >>> fake.book_title()
    >>> fake.book_author()
    >>> fake.book_publisher()
    """

    def book_genre(self):
        """Returns a randomly-chosen book genre."""
        return choice(genre_list)

    def book_title(self):
        """Returns a randomly-chosen book title."""
        return choice(title_list)

    def book_author(self):
        """Returns a randomly-chosen book author."""
        return choice(author_list)

    def book_publisher(self):
        """Returns a randomly-chosen book publisher."""
        return choice(publisher_list)
