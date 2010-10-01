# -*- coding: utf-8 -*-
"""
    tipfy.i18n
    ~~~~~~~~~~

    Internationalization extension.

    This extension provides internationalization utilities: a translations
    store, hooks to set locale for the current request, functions to manipulate
    dates according to timezones or translate and localize strings and dates.

    It uses `Babel <http://babel.edgewall.org/>`_ to manage translations of
    strings and localization of dates and times, and
    `gae-pytz <http://code.google.com/p/gae-pytz/>`_ to handle timezones.

    Several ideas and code were borrowed from
    `Flask-Babel <http://pypi.python.org/pypi/Flask-Babel/>`_ and
    `Kay <http://code.google.com/p/kay-framework/>`_.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime
import os

from babel import Locale, dates, numbers, support

try:
    from pytz.gae import pytz
except ImportError:
    try:
        import pytz
    except ImportError:
        raise RuntimeError('gaepytz or pytz are required.')

from tipfy import Tipfy

#: Default configuration values for this module. Keys are:
#:
#: locale
#:     The application default locale code. Default is ``en_US``.
#:
#: timezone
#:     The application default timezone according to the Olson
#:     database. Default is ``America/Chicago``.
#:
#: locale_session_key
#:     Session key used to save requested locale, if sessions are used.
#:
#: timezone_session_key
#:     Session key used to save requested timezone, if sessions are used.
#:
#: locale_request_lookup
#:     A list of tuples (method, key) to search
#:     for the locale to be loaded for the current request. The methods are
#:     searched in order until a locale is found. Available methods are:
#:
#:     - args: gets the locale code from ``GET`` arguments.
#:     - form: gets the locale code from ``POST`` arguments.
#:     - session: gets the locale code from the current session.
#:     - cookies: gets the locale code from a cookie.
#:     - rule_args: gets the locale code from the keywords in the current
#:       URL rule.
#:
#:     If none of the methods find a locale code, uses the default locale.
#:     Default is ``[('session', '_locale')]``: gets the locale from the
#:     session key ``_locale``.
#:
#: timezone_request_lookup
#:     Same as `locale_request_lookup`, but for the timezone.
#:
#: date_formats
#:     Default date formats for datetime, date and time.
default_config = {
    'locale':                  'en_US',
    'timezone':                'America/Chicago',
    'locale_session_key':      '_locale',
    'timezone_session_key':    '_timezone',
    'locale_request_lookup':   [('session', '_locale')],
    'timezone_request_lookup': [('session', '_timezone')],
    'date_formats': {
        'time':             'medium',
        'date':             'medium',
        'datetime':         'medium',
        'time.short':       None,
        'time.medium':      None,
        'time.full':        None,
        'time.long':        None,
        'date.short':       None,
        'date.medium':      None,
        'date.full':        None,
        'date.long':        None,
        'datetime.short':   None,
        'datetime.medium':  None,
        'datetime.full':    None,
        'datetime.long':    None,
    },
}


class I18nMiddleware(object):
    """``tipfy.RequestHandler`` middleware that saves the current locale in
    the session at the end of request, if it differs from the current value
    stored in the session.
    """
    def after_dispatch(self, handler, response):
        """Saves the current locale in the session.

        :param handler:
            A :class:`tipfy.RequestHandler` instance.
        :param response:
            A :class:`tipfy.Response` instance.
        """
        session = handler.request.session
        i18n = handler.request.i18n_store
        locale_session_key = i18n.config['locale_session_key']
        timezone_session_key = i18n.config['timezone_session_key']

        # Only save if it differs from original session value.
        if i18n.locale != session.get(locale_session_key):
            session[locale_session_key] = i18n.locale

        if i18n.timezone != session.get(timezone_session_key):
            session[timezone_session_key] = i18n.timezone

        return response


class I18nStore(object):
    #: Loaded translations.
    loaded_translations = None
    #: Current locale.
    locale = None
    #: Current translations.
    translations = None
    #: Current timezone.
    timezone = None
    #: Current tzinfo.
    tzinfo = None

    def __init__(self, app, loaded_translations=None, locale=None,
        timezone=None):
        self.app = app
        self.loaded_translations = loaded_translations or {}
        self.config = app.config[__name__]
        self.set_locale(locale or self.config['locale'])
        self.set_timezone(timezone or self.config['timezone'])

    def set_locale(self, locale):
        """Sets the current locale and translations.

        :param locale:
            A locale code, e.g., ``pt_BR``.
        """
        self.locale = locale
        if locale not in self.loaded_translations:
            locales = [locale]
            if locale != self.config['locale']:
                locales.append(self.config['locale'])

            self.loaded_translations[locale] = self.load_translations(locales)

        self.translations = self.loaded_translations[locale]

    def set_timezone(self, timezone):
        """Sets the current timezone and tzinfo.

        :param timezone:
            The timezone name from the Olson database, e.g.:
            ``America/Chicago``.
        """
        self.timezone = timezone
        self.tzinfo = pytz.timezone(timezone)

    def load_translations(self, locales, dirname='locale', domain='messages'):
        return support.Translations.load(dirname, locales, domain)

    def gettext(self, string, **variables):
        """Translates a given string according to the current locale.

        :param string:
            The string to be translated.
        :param variables:
            Variables to format the returned string.
        :returns:
            The translated string.
        """
        return self.translations.ugettext(string) % variables

    def ngettext(self, singular, plural, n, **variables):
        """Translates a possible pluralized string according to the current
        locale.

        :param singular:
            The singular for of the string to be translated.
        :param plural:
            The plural for of the string to be translated.
        :param n:
            An integer indicating if this is a singular or plural. If greater
            than 1, it is a plural.
        :param variables:
            Variables to format the returned string.
        :returns:
            The translated string.
        """
        return self.translations.ungettext(singular, plural, n) % variables

    def to_local_timezone(self, datetime):
        """Returns a datetime object converted to the local timezone.

        :param datetime:
            A ``datetime`` object.
        :returns:
            A ``datetime`` object normalized to a timezone.
        """
        if datetime.tzinfo is None:
            datetime = datetime.replace(tzinfo=pytz.UTC)

        return self.tzinfo.normalize(datetime.astimezone(self.tzinfo))

    def to_utc(self, datetime):
        """Returns a datetime object converted to UTC and without tzinfo.

        :param datetime:
            A ``datetime`` object.
        :returns:
            A naive ``datetime`` object (no timezone), converted to UTC.
        """
        if datetime.tzinfo is None:
            datetime = self.tzinfo.localize(datetime)

        return datetime.astimezone(pytz.UTC).replace(tzinfo=None)

    def _get_format(self, key, format):
        """A helper for the datetime formatting functions. Returns a format
        name or pattern to be used by Babel date format functions.

        :param key:
            A format key to be get from config. Valid values are "date",
            "datetime" or "time".
        :param format:
            The format to be returned. Valid values are "short", "medium",
            "long", "full" or a custom date/time pattern.
        :returns:
            A format name or pattern to be used by Babel date format functions.
        """
        if format is None:
            format = self.config['date_formats'].get(key)

        if format in ('short', 'medium', 'full', 'long'):
            rv = self.config['date_formats'].get('%s.%s' % (key, format))
            if rv is not None:
                format = rv

        return format

    def format_date(self, date=None, format=None, locale=None, rebase=True):
        """Returns a date formatted according to the given pattern and
        following the current locale.

        :param date:
            A ``date`` or ``datetime`` object. If None, the current date in UTC
            is used.
        :param format:
            The format to be returned. Valid values are "short", "medium",
            "long", "full" or a custom date/time pattern. Example outputs:

            - short:  11/10/09
            - medium: Nov 10, 2009
            - long:   November 10, 2009
            - full:   Tuesday, November 10, 2009

        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :param rebase:
            If True, converts the date to the current :attr:`timezone`.
        :returns:
            A formatted date in unicode.
        """
        format = self._get_format('date', format)
        locale = locale or self.locale

        if rebase and isinstance(date, datetime):
            date = self.to_local_timezone(date)

        return dates.format_date(date, format, locale=locale)

    def format_datetime(self, datetime=None, format=None, locale=None,
        timezone=None, rebase=True):
        """Returns a date and time formatted according to the given pattern and
        following the current locale and timezone.

        :param datetime:
            A ``datetime`` object. If None, the current date and time in UTC
            is used.
        :param format:
            The format to be returned. Valid values are "short", "medium",
            "long", "full" or a custom date/time pattern. Example outputs:

            - short:  11/10/09 4:36 PM
            - medium: Nov 10, 2009 4:36:05 PM
            - long:   November 10, 2009 4:36:05 PM +0000
            - full:   Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time

        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :param timezone:
            The timezone name from the Olson database, e.g.:
            'America/Chicago'. If not set, uses the current timezone.
        :param rebase:
            If True, converts the datetime to the current :attr:`timezone`.
        :returns:
            A formatted date and time in unicode.
        """
        format = self._get_format('datetime', format)
        locale = locale or self.locale

        kwargs = {}
        if rebase:
            if timezone:
                kwargs['tzinfo'] = pytz.timezone(timezone)
            else:
                kwargs['tzinfo'] = self.tzinfo

        return dates.format_datetime(datetime, format, locale=locale, **kwargs)

    def format_time(self, time=None, format=None, locale=None, timezone=None,
        rebase=True):
        """Returns a time formatted according to the given pattern and
        following the current locale and timezone.

        :param time:
            A ``time`` or ``datetime`` object. If None, the current
            time in UTC is used.
        :param format:
            The format to be returned. Valid values are "short", "medium",
            "long", "full" or a custom date/time pattern. Example outputs:

            - short:  4:36 PM
            - medium: 4:36:05 PM
            - long:   4:36:05 PM +0000
            - full:   4:36:05 PM World (GMT) Time

        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :param timezone:
            The timezone name from the Olson database, e.g.:
            ``America/Chicago``. If not set, uses the current timezone.
        :param rebase:
            If True, converts the time to the current :attr:`timezone`.
        :returns:
            A formatted time in unicode.
        """
        format = self._get_format('time', format)
        locale = locale or self.locale

        kwargs = {}
        if rebase:
            if timezone:
                kwargs['tzinfo'] = pytz.timezone(timezone)
            else:
                kwargs['tzinfo'] = self.tzinfo

        return dates.format_time(time, format, locale=locale, **kwargs)

    def format_timedelta(self, datetime_or_timedelta, granularity='second',
        threshold=.85, locale=None):
        """Formats the elapsed time from the given date to now or the given
        timedelta. This currently requires an unreleased development version
        of Babel.

        :param datetime_or_timedelta:
            A ``timedelta`` object representing the time difference to format,
            or a ``datetime`` object in UTC.
        :param granularity:
            Determines the smallest unit that should be displayed, the value
            can be one of "year", "month", "week", "day", "hour", "minute" or
            "second".
        :param threshold:
            Factor that determines at which point the presentation switches to
            the next higher unit.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            A string with the elapsed time.
        """
        locale = locale or self.locale
        if isinstance(datetime_or_timedelta, datetime):
            datetime_or_timedelta = datetime.utcnow() - datetime_or_timedelta

        return dates.format_timedelta(datetime_or_timedelta, granularity,
            threshold=threshold, locale=locale)

    def format_number(self, number, locale=None):
        """Returns the given number formatted for a specific locale.

        .. code-block:: python

           >>> format_number(1099, locale='en_US')
           u'1,099'

        :param number:
            The number to format.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The formatted number.
        """
        locale = locale or self.locale
        return numbers.format_number(number, locale=locale)

    def format_decimal(self, number, format=None, locale=None):
        """Returns the given decimal number formatted for a specific locale.

        .. code-block:: python

           >>> format_decimal(1.2345, locale='en_US')
           u'1.234'
           >>> format_decimal(1.2346, locale='en_US')
           u'1.235'
           >>> format_decimal(-1.2346, locale='en_US')
           u'-1.235'
           >>> format_decimal(1.2345, locale='sv_SE')
           u'1,234'
           >>> format_decimal(12345, locale='de')
           u'12.345'

        The appropriate thousands grouping and the decimal separator are used
        for each locale:

        .. code-block:: python

           >>> format_decimal(12345.5, locale='en_US')
           u'12,345.5'

        :param number:
            The number to format.
        :param format:
            Notation format.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The formatted decimal number.
        """
        locale = locale or self.locale
        return numbers.format_decimal(number, format=format, locale=locale)

    def format_currency(self, number, currency, format=None, locale=None):
        """Returns a formatted currency value.

        .. code-block:: python

           >>> format_currency(1099.98, 'USD', locale='en_US')
           u'$1,099.98'
           >>> format_currency(1099.98, 'USD', locale='es_CO')
           u'US$\\xa01.099,98'
           >>> format_currency(1099.98, 'EUR', locale='de_DE')
           u'1.099,98\\xa0\\u20ac'

        The pattern can also be specified explicitly:

        .. code-block:: python

           >>> format_currency(1099.98, 'EUR', u'\\xa4\\xa4 #,##0.00', locale='en_US')
           u'EUR 1,099.98'

        :param number:
            The number to format.
        :param currency:
            The currency code.
        :param format:
            Notation format.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The formatted currency value.
        """
        locale = locale or self.locale
        return numbers.format_currency(number, currency, format=format,
            locale=locale)

    def format_percent(self, number, format=None, locale=None):
        """Returns formatted percent value for a specific locale.

        .. code-block:: python

           >>> format_percent(0.34, locale='en_US')
           u'34%'
           >>> format_percent(25.1234, locale='en_US')
           u'2,512%'
           >>> format_percent(25.1234, locale='sv_SE')
           u'2\\xa0512\\xa0%'

        The format pattern can also be specified explicitly:

        .. code-block:: python

           >>> format_percent(25.1234, u'#,##0\u2030', locale='en_US')
           u'25,123\u2030'

        :param number:
            The percent number to format
        :param format:
            Notation format.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The formatted percent number.
        """
        locale = locale or self.locale
        return numbers.format_percent(number, format=format, locale=locale)

    def format_scientific(self, number, format=None, locale=None):
        """Returns value formatted in scientific notation for a specific
        locale.

        .. code-block:: python

           >>> format_scientific(10000, locale='en_US')
           u'1E4'

        The format pattern can also be specified explicitly:

        .. code-block:: python

           >>> format_scientific(1234567, u'##0E00', locale='en_US')
           u'1.23E06'

        :param number:
            The number to format.
        :param format:
            Notation format.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            Value formatted in scientific notation.
        """
        locale = locale or self.locale
        return numbers.format_scientific(number, format=format, locale=locale)

    def parse_date(self, string, locale=None):
        """Parses a date from a string.

        This function uses the date format for the locale as a hint to
        determine the order in which the date fields appear in the string.

        .. code-block:: python

           >>> parse_date('4/1/04', locale='en_US')
           datetime.date(2004, 4, 1)
           >>> parse_date('01.04.2004', locale='de_DE')
           datetime.date(2004, 4, 1)

        :param string:
            The string containing the date.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The parsed date object.
        """
        locale = locale or self.locale
        return dates.parse_date(string, locale=locale)

    def parse_datetime(self, string, locale=None):
        """Parses a date and time from a string.

        This function uses the date and time formats for the locale as a hint
        to determine the order in which the time fields appear in the string.

        :param string:
            The string containing the date and time.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The parsed datetime object.
        """
        locale = locale or self.locale
        return dates.parse_datetime(string, locale=locale)

    def parse_time(self, string, locale=None):
        """Parses a time from a string.

        This function uses the time format for the locale as a hint to
        determine the order in which the time fields appear in the string.

        .. code-block:: python

           >>> parse_time('15:30:00', locale='en_US')
           datetime.time(15, 30)

        :param string:
            The string containing the time.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The parsed time object.
        """
        locale = locale or self.locale
        return dates.parse_time(string, locale=locale)

    def parse_number(self, string, locale=None):
        """Parses localized number string into a long integer.

        .. code-block:: python

           >>> parse_number('1,099', locale='en_US')
           1099L
           >>> parse_number('1.099', locale='de_DE')
           1099L

        When the given string cannot be parsed, an exception is raised:

        .. code-block:: python

           >>> parse_number('1.099,98', locale='de')
           Traceback (most recent call last):
               ...
           NumberFormatError: '1.099,98' is not a valid number

        :param string:
            The string to parse.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The parsed number.
        :raises:
            ``NumberFormatError`` if the string can not be converted to a
            number.
        """
        locale = locale or self.locale
        return numbers.parse_number(string, locale=locale)

    def parse_decimal(self, string, locale=None):
        """Parses localized decimal string into a float.

        .. code-block:: python

           >>> parse_decimal('1,099.98', locale='en_US')
           1099.98
           >>> parse_decimal('1.099,98', locale='de')
           1099.98

        When the given string cannot be parsed, an exception is raised:

        .. code-block:: python

           >>> parse_decimal('2,109,998', locale='de')
           Traceback (most recent call last):
               ...
           NumberFormatError: '2,109,998' is not a valid decimal number

        :param string:
            The string to parse.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The parsed decimal number.
        :raises:
            ``NumberFormatError`` if the string can not be converted to a
            decimal number.
        """
        locale = locale or self.locale
        return numbers.parse_decimal(string, locale=locale)

    def get_timezone_location(self, dt_or_tzinfo, locale=None):
        """Returns a representation of the given timezone using "location
        format".

        The result depends on both the local display name of the country and
        the city assocaited with the time zone:

        .. code-block:: python

           >>> from pytz import timezone
           >>> tz = timezone('America/St_Johns')
           >>> get_timezone_location(tz, locale='de_DE')
           u"Kanada (St. John's)"
           >>> tz = timezone('America/Mexico_City')
           >>> get_timezone_location(tz, locale='de_DE')
           u'Mexiko (Mexiko-Stadt)'

        If the timezone is associated with a country that uses only a single
        timezone, just the localized country name is returned:

        .. code-block:: python

           >>> tz = timezone('Europe/Berlin')
           >>> get_timezone_name(tz, locale='de_DE')
           u'Deutschland'

        :param dt_or_tzinfo:
            The ``datetime`` or ``tzinfo`` object that determines
            the timezone; if None, the current date and time in UTC is assumed.
        :param locale:
            A locale code. If not set, uses the current :attr:`locale`.
        :returns:
            The localized timezone name using location format.
        """
        locale = locale or self.locale
        return dates.get_timezone_name(dt_or_tzinfo, locale=locale)

    def get_store_for_request(self, request):
        """Returns a I18nStore bound to a given request.

        :param request:
            A :class:`tipfy.Request` instance.
        :returns:
            A new :class:`I18nStore` instance with locale and timezone set
            for the request.
        """
        locale = self.get_value_for_request(request,
            self.config['locale_request_lookup'], self.config['locale'])
        timezone = self.get_value_for_request(request,
            self.config['timezone_request_lookup'], self.config['timezone'])

        return self.__class__(self.app, self.loaded_translations, locale,
            timezone)

    def get_value_for_request(self, request, lookup_list, default=None):
        """Returns a locale code or timezone for the current request.

        It will use the configuration for ``locale_request_lookup`` or
        ``timezone_request_lookup`` to search for a key in ``GET``, ``POST``,
        session, cookie or keywords in the current URL rule. If no value is
        found, returns the default value.

        :param request:
            A :class:`tipfy.Request` instance.
        :param lookup_list:
            A list of `(attribute, key)` tuples to search in request, e.g.,
            ``[('args', 'lang'), ('session', 'locale')]``.
        :default:
            Default value to return in case none is found.
        :returns:
            A locale code or timezone setting.
        """
        value = None
        for method, key in lookup_list:
            # Get locale from GET, POST, session, cookies or rule_args.
            value = getattr(request, method).get(key, None)
            if value is not None:
                break
        else:
            value = default

        return value


def set_locale(locale):
    """See :meth:`I18nStore.set_locale`."""
    return Tipfy.request.i18n_store.set_locale(locale)


def gettext(string, **variables):
    """See :meth:`I18nStore.gettext`."""
    return Tipfy.request.i18n_store.gettext(string, **variables)


def ngettext(singular, plural, n, **variables):
    """See :meth:`I18nStore.ngettext`."""
    return Tipfy.request.i18n_store.ngettext(singular, plural, n, **variables)


def to_local_timezone(datetime):
    """See :meth:`I18nStore.to_local_timezone`."""
    return Tipfy.request.i18n_store.to_local_timezone(datetime)


def to_utc(datetime):
    """See :meth:`I18nStore.to_utc`."""
    return Tipfy.request.i18n_store.to_utc(datetime)


def format_date(date=None, format=None, locale=None, rebase=True):
    """See :meth:`I18nStore.format_date`."""
    return Tipfy.request.i18n_store.format_date(date, format, locale, rebase)


def format_datetime(datetime=None, format=None, locale=None, timezone=None,
    rebase=True):
    """See :meth:`I18nStore.format_datetime`."""
    return Tipfy.request.i18n_store.format_datetime(datetime, format, locale,
        timezone, rebase)


def format_time(time=None, format=None, locale=None, timezone=None,
    rebase=True):
    """See :meth:`I18nStore.format_time`."""
    return Tipfy.request.i18n_store.format_time(time, format, locale, timezone,
        rebase)


def format_timedelta(datetime_or_timedelta, granularity='second',
    threshold=.85, locale=None):
    """See :meth:`I18nStore.format_timedelta`."""
    return Tipfy.request.i18n_store.format_timedelta(datetime_or_timedelta,
        granularity, threshold, locale)


def format_number(number, locale=None):
    """See :meth:`I18nStore.format_number`."""
    return Tipfy.request.i18n_store.format_number(number, locale)


def format_decimal(number, format=None, locale=None):
    """See :meth:`I18nStore.format_decimal`."""
    return Tipfy.request.i18n_store.format_decimal(number, format, locale)


def format_currency(number, currency, format=None, locale=None):
    """See :meth:`I18nStore.format_currency`."""
    return Tipfy.request.i18n_store.format_currency(number, currency, format,
        locale)


def format_percent(number, format=None, locale=None):
    """See :meth:`I18nStore.format_percent`."""
    return Tipfy.request.i18n_store.format_percent(number, format, locale)


def format_scientific(number, format=None, locale=None):
    """See :meth:`I18nStore.format_scientific`."""
    return Tipfy.request.i18n_store.format_scientific(number, format, locale)


def parse_date(string, locale=None):
    """See :meth:`I18nStore.parse_date`"""
    return Tipfy.request.i18n_store.parse_date(string, locale)


def parse_datetime(string, locale=None):
    """See :meth:`I18nStore.parse_datetime`."""
    return Tipfy.request.i18n_store.parse_datetime(string, locale)


def parse_time(string, locale=None):
    """See :meth:`I18nStore.parse_time`."""
    return Tipfy.request.i18n_store.parse_time(string, locale)


def parse_number(string, locale=None):
    """See :meth:`I18nStore.parse_number`."""
    return Tipfy.request.i18n_store.parse_number(string, locale)


def parse_decimal(string, locale=None):
    """See :meth:`I18nStore.parse_decimal`."""
    return Tipfy.request.i18n_store.parse_decimal(string, locale)


def get_timezone_location(dt_or_tzinfo, locale=None):
    """See :meth:`I18nStore.get_timezone_location`"""
    return Tipfy.request.i18n_store.get_timezone_location(dt_or_tzinfo, locale)


def list_translations(dirname='locale'):
    """Returns a list of all the existing translations.  The list returned
    will be filled with actual locale objects and not just strings.

    :param dirname:
        Path to the translations directory.
    :returns:
        A list of ``babel.Locale`` objects.
    """
    if not os.path.isdir(dirname):
        return []

    result = []
    for folder in sorted(os.listdir(dirname)):
        if os.path.isdir(os.path.join(dirname, folder, 'LC_MESSAGES')):
            result.append(Locale.parse(folder))

    return result


def lazy_gettext(string, **variables):
    """A lazy version of :func:`gettext`.

    :param string:
        The string to be translated.
    :param variables:
        Variables to format the returned string.
    :returns:
        A ``babel.support.LazyProxy`` object that when accessed translates
        the string.
    """
    return support.LazyProxy(gettext, string, **variables)


def lazy_ngettext(singular, plural, n, **variables):
    """A lazy version of :func:`ngettext`.

    :param singular:
        The singular for of the string to be translated.
    :param plural:
        The plural for of the string to be translated.
    :param n:
        An integer indicating if this is a singular or plural. If greater
        than 1, it is a plural.
    :param variables:
        Variables to format the returned string.
    :returns:
        A ``babel.support.LazyProxy`` object that when accessed translates
        the string.
    """
    return support.LazyProxy(ngettext, singular, plural, n, **variables)


# Alias to gettext.
_ = gettext