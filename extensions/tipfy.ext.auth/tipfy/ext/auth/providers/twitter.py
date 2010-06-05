# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.providers.twitter
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of Twitter authentication scheme.

    Ported from `tornado.auth <http://github.com/facebook/tornado/blob/master/tornado/auth.py>`_.

    :copyright: 2009 Facebook.
    :copyright: 2010 tipfy.org.
    :license: Apache License Version 2.0, see LICENSE.txt for more details.
"""
from tipfy.ext.auth.providers.oauth import OAuthMixin


class TwitterMixin(OAuthMixin):
    """Twitter OAuth authentication.

    To authenticate with Twitter, register your application with
    Twitter at http://twitter.com/apps. Then copy your Consumer Key and
    Consumer Secret to the application settings 'twitter_consumer_key' and
    'twitter_consumer_secret'. Use this Mixin on the handler for the URL
    you registered as your application's Callback URL.

    When your application is set up, you can use this Mixin like this
    to authenticate the user with Twitter and get access to their stream:

    class TwitterHandler(tornado.web.RequestHandler,
                         tornado.auth.TwitterMixin):
        @tornado.web.asynchronous
        def get(self):
            if self.get_argument("oauth_token", None):
                self.get_authenticated_user(self.async_callback(self._on_auth))
                return
            self.authorize_redirect()

        def _on_auth(self, user):
            if not user:
                raise tornado.web.HTTPError(500, "Twitter auth failed")
            # Save the user using, e.g., set_secure_cookie()

    The user object returned by get_authenticated_user() includes the
    attributes 'username', 'name', and all of the custom Twitter user
    attributes describe at
    http://apiwiki.twitter.com/Twitter-REST-API-Method%3A-users%C2%A0show
    in addition to 'access_token'. You should save the access token with
    the user; it is required to make requests on behalf of the user later
    with twitter_request().
    """
    _OAUTH_REQUEST_TOKEN_URL = "http://api.twitter.com/oauth/request_token"
    _OAUTH_ACCESS_TOKEN_URL = "http://api.twitter.com/oauth/access_token"
    _OAUTH_AUTHORIZE_URL = "http://api.twitter.com/oauth/authorize"
    _OAUTH_AUTHENTICATE_URL = "http://api.twitter.com/oauth/authenticate"
    _OAUTH_NO_CALLBACKS = True

    def authenticate_redirect(self):
        """Just like authorize_redirect(), but auto-redirects if authorized.

        This is generally the right interface to use if you are using
        Twitter for single-sign on.
        """
        http = httpclient.AsyncHTTPClient()
        http.fetch(self._oauth_request_token_url(), self.async_callback(
            self._on_request_token, self._OAUTH_AUTHENTICATE_URL, None))

    def twitter_request(self, path, callback, access_token=None,
                           post_args=None, **args):
        """Fetches the given API path, e.g., "/statuses/user_timeline/btaylor"

        The path should not include the format (we automatically append
        ".json" and parse the JSON output).

        If the request is a POST, post_args should be provided. Query
        string arguments should be given as keyword arguments.

        All the Twitter methods are documented at
        http://apiwiki.twitter.com/Twitter-API-Documentation.

        Many methods require an OAuth access token which you can obtain
        through authorize_redirect() and get_authenticated_user(). The
        user returned through that process includes an 'access_token'
        attribute that can be used to make authenticated requests via
        this method. Example usage:

        class MainHandler(tornado.web.RequestHandler,
                          tornado.auth.TwitterMixin):
            @tornado.web.authenticated
            @tornado.web.asynchronous
            def get(self):
                self.twitter_request(
                    "/statuses/update",
                    post_args={"status": "Testing Tornado Web Server"},
                    access_token=user["access_token"],
                    callback=self.async_callback(self._on_post))

            def _on_post(self, new_entry):
                if not new_entry:
                    # Call failed; perhaps missing permission?
                    self.authorize_redirect()
                    return
                self.finish("Posted a message!")

        """
        # Add the OAuth resource request signature if we have credentials
        url = "http://api.twitter.com/1" + path + ".json"
        if access_token:
            all_args = {}
            all_args.update(args)
            all_args.update(post_args or {})
            consumer_token = self._oauth_consumer_token()
            method = "POST" if post_args is not None else "GET"
            oauth = self._oauth_request_parameters(
                url, access_token, all_args, method=method)
            args.update(oauth)
        if args: url += "?" + urllib.urlencode(args)
        callback = self.async_callback(self._on_twitter_request, callback)
        http = httpclient.AsyncHTTPClient()
        if post_args is not None:
            http.fetch(url, method="POST", body=urllib.urlencode(post_args),
                       callback=callback)
        else:
            http.fetch(url, callback=callback)

    def _on_twitter_request(self, callback, response):
        if response.error:
            logging.warning("Error response %s fetching %s", response.error,
                            response.request.url)
            callback(None)
            return
        callback(escape.json_decode(response.body))

    def _oauth_consumer_token(self):
        self.require_setting("twitter_consumer_key", "Twitter OAuth")
        self.require_setting("twitter_consumer_secret", "Twitter OAuth")
        return dict(
            key=self.settings["twitter_consumer_key"],
            secret=self.settings["twitter_consumer_secret"])

    def _oauth_get_user(self, access_token, callback):
        callback = self.async_callback(self._parse_user_response, callback)
        self.twitter_request(
            "/users/show/" + access_token["screen_name"],
            access_token=access_token, callback=callback)

    def _parse_user_response(self, callback, user):
        if user:
            user["username"] = user["screen_name"]
        callback(user)
