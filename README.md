# bloggercmd

This little script provides the following functionality:

1. **insert**

    Submit your html file as draft to your blog

2. **publish**

    Publish your submitted draft

3. **revert**

    Change your published post back to draft

4. **update**

    Update your post and make it as draft

5. **tag**

    Save all tags of a blog in a file locally and provide a handy way to track tag information in the local file.

## Before use -  Get OAuth client ID

Go to [google console credentials](https://console.developers.google.com/apis/credentials) to create a [OAuth 2.0](https://support.google.com/cloud/answer/6158849?hl=en&ref_topic=6262490) client ID (select web application works well). Don't forget to set URI as http://localhost:8080/ (to make redirection goes smoothly). Download the JSON file and save it as `bloggercmd/client_secret.json`

## References

API usage (Python): <https://developers.google.com/resources/api-libraries/documentation/blogger/v3/python/latest/index.html>

Git-command like args: <http://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html>

APIs explorer (play with API): <https://developers.google.com/apis-explorer/?hl=en_US#p/blogger/v3/>

Google Python API repo: <https://github.com/google/google-api-python-client>

Particularly Blogger API: <https://github.com/google/google-api-python-client/tree/master/samples/blogger>

Blogger API general intro: <https://developers.google.com/blogger/>

My motivation originally from laziness and having fun, and I find it is possible when I find this: <https://github.com/Adept-/crankyblogger>