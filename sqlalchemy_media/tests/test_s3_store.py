import io
import logging
import threading
import unittest
from os.path import join, dirname, abspath, getsize

import requests
from moto.server import DomainDispatcherApplication, create_backend_app, run_simple
from werkzeug.serving import run_simple

from sqlalchemy_media.exceptions import S3Error
from sqlalchemy_media.stores import S3Store

TEST_HOST = '127.0.0.1'
TEST_PORT = 10002
TEST_BUCKET = '127'
TEST_ACCESS_KEY = 'test_access_key'
TEST_SECRET_KEY = 'test_secret_key'
TEST_BASE_URL = 'http://{0}:{1}'.format(TEST_HOST, TEST_PORT)
RUNNING = False


def run_s3_mock_server():
    global RUNNING

    mock_app = DomainDispatcherApplication(create_backend_app, 's3')
    mock_app.debug = False
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    def run():
        run_simple(TEST_HOST, TEST_PORT, mock_app, threaded=True)

    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
    RUNNING = True

    # create test bucket
    res = requests.put(TEST_BASE_URL)
    assert res.status_code == 200


class S3StoreTestCase(unittest.TestCase):

    def setUp(self):
        if not RUNNING:
            run_s3_mock_server()
        self.base_url = 'http://static1.example.orm'
        self.this_dir = abspath(dirname(__file__))
        self.stuff_path = join(self.this_dir, 'stuff')
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def test_put_from_stream(self):
        store = S3Store(TEST_BUCKET, TEST_ACCESS_KEY, TEST_SECRET_KEY, '')
        store.base_url = TEST_BASE_URL
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)
        length = store.put(target_filename, stream)
        self.assertEqual(length, len(content))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

    def test_delete(self):
        store = S3Store(TEST_BUCKET, TEST_ACCESS_KEY, TEST_SECRET_KEY, '')
        store.base_url = TEST_BASE_URL
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        store.delete(target_filename)
        with self.assertRaises(S3Error):
            store.open(target_filename)

    def test_open(self):
        store = S3Store(TEST_BUCKET, TEST_ACCESS_KEY, TEST_SECRET_KEY, '')
        store.base_url = TEST_BASE_URL
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        # Reading
        with store.open(target_filename, mode='rb') as stored_file, \
                open(self.sample_text_file1, mode='rb') as original_file:
            self.assertEqual(stored_file.read(), original_file.read())


if __name__ == '__main__':  # pragma: no cover
    unittest.main()