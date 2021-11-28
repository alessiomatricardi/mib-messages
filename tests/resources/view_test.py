import unittest


class ViewTest(unittest.TestCase):
    """
    This class should be implemented by
    all classes that tests resources
    """
    client = None

    @classmethod
    def setUpClass(cls):
        from mib import create_app
        app = create_app()
        cls.client = app.test_client()

        from tests.models.test_user import TestUser
        cls.test_user = TestUser

        from mib.dao.user_manager import UserManager
        cls.user_manager = UserManager()

    def login_test_user(self):
        """
        Simulate the user login for testing the resources
        :return: user
        """
        user = self.test_user.generate_random_user()
        psw = user.password
        user.set_password(user.password)

        self.user_manager.create_user(user=user)
        data = {
            'email': user.email,
            'password': psw,
        }

        response = self.client.post('/login', json=data)
        json_response = response.json

        assert response.status_code == 200
        assert json_response["authentication"] == 'success'
        assert json_response['user'] is not None

        return user
