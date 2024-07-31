import cwpl.db as db
import sqlalchemy as sa


class BaseTestCase:
    def setup_class(self):
        self.sql_uri = "sqlite:///:memory:"

        # setup DB engine and init DB
        db.sql_engine = sa.create_engine(self.sql_uri)
        db.init_db()


class TestAddUser(BaseTestCase):
    def test_func_answer(self):
        assert db.add_user("test").name == "test"
