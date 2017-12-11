from core.dbconnector.conditions import BaseCondiction
from core.dbconnector.joins import BaseJoin


def wait(f):
    def decorator(*args, **kwargs):
        while args[0].isLock():
            pass
        return f(*args, **kwargs)
    return decorator


class Model:
    def __init__(self, table, field, db_conn):
        self.table = table
        self.field = field
        self.db = db_conn
        self.mutex = 0

    def lock(self):
        self.mutex = 1

    def unlock(self):
        self.mutex = 0
        
    def isLock(self):
        return self.mutex

    @wait
    def search(self, conditions=None, fields=None, order: dict = None, group=None, limit=None, is_format_filed=True):
        sql = '''SELECT {fields} FROM `{table}`'''.format(fields='*' if not fields else ", ".join(
            ['`' + field + '`' if field[0] is not '`' else field for field in fields]
            if is_format_filed else
            [field for field in fields]
        ), table=self.table)

        if conditions:
            if not isinstance(conditions, BaseJoin) and not isinstance(conditions, BaseCondiction):
                raise TypeError('Must Be Condition Class')
            conditions = conditions.format()
            sql += ' WHERE ' + conditions

        if group:
            fields = ", ".join(group)
            statement = ' GROUP BY `{fields}`'.format(fields=fields)
            sql += statement

        if order:
            field = ", ".join(order['fields'])
            sort = order.get('sort', 'ASC')

            statement = " ORDER BY `{field}` {sort}".format(field=field, sort=sort)
            sql += statement

        if limit:
            limit = [str(ele) for ele in limit]
            statement = " LIMIT " + ", ".join(limit)
            sql += statement

        sql = sql.replace("None", "NULL")

        self.lock()
        ret = self.db.execute(sql)
        self.unlock()

        if ret.suc:
            ret.rows = self.__total(conditions)

        return ret

    @wait
    def update(self, conditions: BaseCondiction or BaseJoin, **options):
        if not isinstance(conditions, BaseCondiction) and not isinstance(conditions, BaseJoin):
            raise TypeError('Must Be Condition Class')

        values = []

        if 'params' in options.keys():
            options = options.get('params')

        for k, v in options.items():
            v = '"%s"' % v if isinstance(v, str) else v
            values.append('`{key}` = {value}'.format(key=k, value=v))

        sql = 'UPDATE `{table}` SET {values} WHERE {conditions}'.format(table=self.table, values=", ".join(values),
                                                                        conditions=conditions.format())

        self.lock()
        ret = self.db.execute(sql)
        self.unlock()

        return ret

    @wait
    def delete(self, conditions=None):
        if not conditions:
            statement = '''DELETE FROM `{table}`'''.format(table=self.table)
        else:
            if not isinstance(conditions, BaseCondiction) and not isinstance(conditions, BaseJoin):
                raise TypeError('Must Be Condition Class')

            statement = '''DELETE FROM `{table}` WHERE {conditions}'''.format(table=self.table,
                                                                              conditions=conditions.format())

        self.lock()
        ret = self.db.execute(statement)
        self.unlock()

        return ret

    @wait
    def add(self, **options):
        key_tmp = []
        value_tmp = []

        if 'params' in options.keys():
            options = options.get('params')

        for key, value in options.items():
            key_tmp.append('`' + key + '`')
            value_tmp.append(str(value) if isinstance(value, int) or value is None else "'%s'" % str(value).replace("'", '"'))

        statement = '''INSERT INTO `{table}`({key_tmp}) VALUES({value_tmp})'''.format(
            table=self.table,
            key_tmp=", ".join(key_tmp),
            value_tmp=", ".join(value_tmp)
        )

        statement = statement.replace("None", "NULL")

        self.lock()
        ret = self.db.insert(statement)
        self.unlock()

        return ret

    def __total(self, conditions=None):
        sql = '''SELECT COUNT(id) FROM `{table}`'''.format(table=self.table)
        if conditions:
            sql += ' WHERE ' + conditions
        return self.db.execute(sql).result[0]['COUNT(id)']
