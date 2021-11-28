from mib.dao.manager import Manager
from mib.models.message import Message


class MessageManager(Manager):
    '''
    TODO

    @staticmethod
    def create_user(user: User):
        Manager.create(user=user)

    @staticmethod
    def retrieve_by_id(id_) -> User:
        Manager.check_none(id=id_)
        return User.query.get(id_)

    @staticmethod
    def retrieve_by_email(email) -> User:
        Manager.check_none(email=email)
        return User.query.filter(User.email == email).first()

    @staticmethod
    def update_user(user: User):
        Manager.update(user=user)
    
    @staticmethod
    def retrieve_users_by_blacklist(id: int, blacklist):
        Manager.check_none(id=id)
        Manager.check_none(blacklist=blacklist)
        all_users = User.query.filter(User.id != id).filter(~User.id.in_(blacklist))\
            .filter(User.is_active == True).filter(User.is_admin == False).all()
        
        return all_users


    # TODO controllare utilità

    @staticmethod
    def delete_user(user: User):
        Manager.delete(user=user)

    @staticmethod
    def delete_user_by_id(id_: int):
        user = UserManager.retrieve_by_id(id_)
        UserManager.delete_user(user)
    '''
