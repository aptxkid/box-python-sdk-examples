from __future__ import unicode_literals

import json
from threading import Thread

from boxsdk.client import Client
from boxsdk.config import API
from boxsdk.auth.oauth2 import OAuth2
from boxsdk.network.default_network import DefaultNetwork, DefaultNetworkResponse


class NonBlockingNetwork(DefaultNetwork):
    """Implementation of a non-blocking network layer."""

    def __init__(self):
        super(NonBlockingNetwork, self).__init__()

    def request(self, method, url, access_token, **kwargs):
        """Base class override.
        Make a non-blocking network request.
        """

        deferred_request_response = {}

        def _make_request():
            default_network_response = super(NonBlockingNetwork, self).request(method, url, access_token, **kwargs)
            deferred_request_response['response'] = default_network_response
            print 'response received. ({} {})'.format(method, url)

        thread = Thread(target=_make_request)
        thread.start()

        return DeferredNetworkResponse(deferred_request_response, access_token, thread)


class DeferredNetworkResponse(DefaultNetworkResponse):
    """Implementation of a deferred network response."""

    def __init__(self, request_response, access_token_used, worker_thread):
        super(DeferredNetworkResponse, self).__init__(request_response, access_token_used)
        self._worker_thread = worker_thread

    def _wait_worker_thread(self):
        self._worker_thread.join()

    def json(self):
        print 'json wait'
        self._wait_worker_thread()
        return self._request_response['response'].json()

    @property
    def status_code(self):
        return 200

    @property
    def content(self):
        print 'content wait'
        self._wait_worker_thread()
        return self._request_response['response'].content

    @property
    def ok(self):
        return True

    @property
    def response_as_stream(self):
        print 'response as a stream wait'
        self._wait_worker_thread()
        return self._request_response['response'].raw

    @property
    def headers(self):
        print 'headers wait'
        self._wait_worker_thread()
        return self._request_response['response'].headers


def main():
    network_layer = NonBlockingNetwork()
    oauth = OAuth2(
        client_id='',
        client_secret='',
        access_token='',
    )
    non_blocking_client = Client(oauth, network_layer=network_layer)

    non_blocking_client.make_request(
        'POST',
        '{}/files/content'.format(API.UPLOAD_URL),
        data={'attributes': json.dumps({
            'name': 'test.txt',
            'parent': {'id': '0'},
        })},
        files={
            'file': ('unused', open('/Users/lpan/Desktop/logs', 'rb')),
        },
        expect_json_response=False,
    )
    print 'Made request to upload a file'


if __name__ == '__main__':
    main()