# faker_books
Books Faker Community Provider

## Installation
```
> pip install faker_books
```
## Usage
```py
from faker import Faker
from faker_books import BookProvider

fake = Faker()
fake.add_provider(BookProvider)

fake.book_genre()
fake.book_author()
fake.book_title()
fake.book_publisher()
```

## Acknowledgements
The layout for this repository was mainly inspired by https://github.com/jeffwright13/faker_music

