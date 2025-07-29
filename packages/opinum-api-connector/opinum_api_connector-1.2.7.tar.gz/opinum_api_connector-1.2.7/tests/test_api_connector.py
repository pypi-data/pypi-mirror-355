import unittest
from opinum_api_connector import ApiConnector
import json
from io import BytesIO

with open('local.settings.json') as f:
    environment = json.load(f)


def get_number_of_sources(connector, source_ids):
    sources = connector.get('sources', ids=source_ids).json()
    return len(sources)


class MyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MyTestCase, self).__init__(*args, **kwargs)
        self.api_connector = ApiConnector(environment=environment, account_id=836)
        self.api_connector_duplicate = ApiConnector(environment=environment, account_id=336)

    def test_instance_creation_with_bad_credentials(self):
        with self.assertRaises(Exception) as context:
            api_connector = ApiConnector(environment={
                'OPINUM_CLIENT_ID': 'client',
                'OPINUM_USERNAME': 'user',
                'OPINUM_PASSWORD': 'password',
                'OPINUM_SECRET': 'secret'
            })
        self.assertTrue('(invalid_client) ' in str(context.exception))

    def test_simple_query_with_account_change(self):
        self.assertEqual(len(self.api_connector.get('sources', siteId=204488).json()), 3)
        self.assertEqual(len(self.api_connector_duplicate.get('sources', siteId=204488).json()), 0)

    def test_file_storage(self):
        with BytesIO() as hello:
            hello.write(b'Hello World!')
            hello.seek(0)
            azure_id = self.api_connector.send_file_to_storage('Hello.txt', hello, 'text/plain').json()
        self.assertIsNotNone(self.api_connector.get(f"storage/{azure_id}").json())


if __name__ == '__main__':
    unittest.main()
