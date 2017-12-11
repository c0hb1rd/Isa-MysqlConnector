from core.dbconnector.conditions import BaseCondiction


class BaseJoin:
    def __init__(self, symbol, conditions: list):
        self.conditions = []
        self.symbol = " {symbol} ".format(symbol=symbol.strip())
        self.is_join = False

        if not isinstance(conditions, list):
            conditions = [conditions]

        if len(conditions) == 1 and (isinstance(conditions[0], BaseJoin) or isinstance(conditions[0], BaseCondiction)):
            self.is_join = True
            self.conditions = conditions[0].format()
        else:
            for condition in conditions:
                if isinstance(condition, BaseCondiction) or isinstance(condition, BaseJoin):
                    self.conditions.append(condition.format())
                else:
                    raise TypeError('must a condiction class')

    def format(self):
        if self.is_join:
            return self.conditions
        return "(%s)" % self.symbol.join(self.conditions)

    def add(self, condition):
        self.conditions.append(condition)


class AndJoin(BaseJoin):
    def __init__(self, conditions):
        super().__init__(symbol='AND', conditions=conditions)


class OrJoin(BaseJoin):
    def __init__(self, conditions):
        super().__init__(symbol='OR', conditions=conditions)
