from src.handlers.database import RealmWriteHandler


class Controller:

    @staticmethod
    def run():

        r_a = RealmWriteHandler('a')
        r_h = RealmWriteHandler('h')

        for realm_id in RealmWriteHandler.REALM_LIST_EU:
            r_a.run_session(realm_id)
            r_h.run_session(realm_id)


if __name__ == '__main__':
    Controller.run()