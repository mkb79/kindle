# Kindle

In development

Please take a look at https://audible.readthedocs.io/en/latest/ for information about Locale, auth files and so on. More will be coming soon.

# Installation

```shell
git clone https://github.com/mkb79/kindle
cd kindle
pip install .
```

# Example Get Library

```python
import kindle
import kindle.api

auth = kindle.Authenticator.from_login(
    AUDIBLE_MAIL,
    AUDIBLE_PASSWORD,
    LOCALE_CODE)
auth.register_device()
auth.to_file(AUTH_FILENAME)  # Optionally

library = kindle.api.get_library(auth)
print(library)

book_manifest = kindle.api.get_manifest(auth, ASIN_OF_BOOK)
print(book_manifesr)

# Optionally unregister
auth.refresh_access_token()
auth.deregister_device()
```