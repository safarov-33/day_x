# Interface translations

New interface strings in Python and templates use English source text.
English is also the default language for first-time visitors.

- RU: `ru/LC_MESSAGES/django.po`
- TJ (Cyrillic Tajik, ISO code `tg`): `tg/LC_MESSAGES/django.po`
- `en/LC_MESSAGES/django.po` retains Russian-to-English mappings solely for
  historical activity records created before the source-language conversion.
  Do not regenerate that compatibility catalog with `makemessages`.

Use `gettext_lazy` in form definitions and models, `gettext` for immediate
translations, and `{% translate %}` / `{% blocktranslate %}` in templates.
Do not translate customer names, shop names or user-entered descriptions.
Activity messages store their message ID and interpolation values separately.

Update and compile catalogs with GNU gettext installed:

```sh
python manage.py makemessages -l ru -l tg --ignore=.venv --ignore=backups --extension=html,txt,py
python manage.py compilemessages --ignore=.venv
python manage.py test
```

The Tajik catalog supplements Django's built-in translations of password rules
and form errors. Their extraction markers live in `main/i18n_messages.py`.
Russian standard validation messages fall back to Django's built-in catalog.

The header posts to Django's CSRF-protected `set_language` view.
The language cookie lasts one year and is used across public and private pages.
Without a valid language cookie the configured default (`en`) is used,
regardless of the browser's Accept-Language preference.
