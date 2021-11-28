from .view_test import ViewTest
from faker import Faker


class TestAuth(ViewTest):

    faker = Faker('it_IT')

    @classmethod
    def setUpClass(cls):
        super(TestAuth, cls).setUpClass()

    def test_login(self):
        # login for a customer
        user = self.login_test_user()

        # login with a wrong email
        data = {
            'email': user.email,
            'password': TestAuth.faker.password()
        }

        response = self.client.post('/login', json=data)
        json_response = response.json

        assert response.status_code == 401
        assert json_response["authentication"] == 'failure'
        assert json_response['user'] is None




    
    


