PYLTI_CONFIG = {
    "consumers": {"secret1": {"secret": "secret2"}},
    "method_hooks": {
        "valid_lti_request": "opentalti.views.valid_lti_request",
        "invalid_lti_request": "opentalti.views.invalid_lti_request",
    },
    "next_url": "/",
}
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SECURE_SSL_REDIRECT = False
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
