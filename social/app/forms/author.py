from django import forms


class FindRemoteAuthorForm(forms.Form):
    URI_REGEX = r'^(.+)//(?P<host>([^/]+))/.*author/(?P<pk>[0-9a-fA-F-]+)/?$'

    uri = forms.RegexField(
        required=True,
        help_text="Enter the remote Author's profile page URL here (e.g.: http://www.site.com/author/ab21...)",
        label="Remote Author URL",
        regex=URI_REGEX,
        strip=True,
        error_messages={
            'invalid': 'Invalid Author profile page URL. (e.g.: http://www.site.com/author/ab21.../)'
        }
    )
