class BaseCondiction:
    def __init__(self, field, case, symbol, is_format=True):
        self.field = field
        self.case = case
        self.symbol = symbol
        self.is_format = is_format

    def format(self):
        case = self.case
        if isinstance(self.case, str):
            if self.is_format:
                case = '"{case}"'.format(case=case)
            else:
                case = '{case}'.format(case=case)

        return '`{field}` {symbol} {case}'.format(field=self.field, symbol=self.symbol, case=case)


class IsCondition(BaseCondiction):
    def __init__(self, field, case, flag: bool = True, is_format=True):
        if flag:
            symbol = '='
        else:
            symbol = '!='

        if case is None:
            symbol = 'IS' if flag else 'IS NOT'

        super().__init__(field, case, symbol=symbol, is_format=is_format)


class IsGreaterCondition(BaseCondiction):
    def __init__(self, field, case, flag: bool = True, is_format=True):
        if flag:
            symbol = '>'
        else:
            symbol = '<'
        super().__init__(field, case, symbol=symbol, is_format=is_format)


class IsGECondition(BaseCondiction):
    def __init__(self, field, case, flag: bool = True, is_format=True):
        if flag:
            symbol = '>='
        else:
            symbol = '<='
        super().__init__(field, case, symbol=symbol, is_format=is_format)


class LikeCondition(BaseCondiction):
    def __init__(self, field, case, is_format=True):
        super().__init__(field, '%' + case + '%', symbol='like', is_format=is_format)


class IsInCondition(BaseCondiction):
    def __init__(self, field, case, flag: bool = True, is_format=True):
        if not isinstance(case, list):
            raise TypeError('must a list')
        values = []

        for value in case:
            if isinstance(value, int):
                values.append(str(value))
            elif isinstance(value, str):
                if is_format:
                    values.append('"{value}"'.format(value=value))
                else:
                    values.append('{value}'.format(value=value))

        case = '({values})'.format(values=", ".join(values))
        if flag:
            symbol = 'IN'
        else:
            symbol = 'NOT IN'
        super().__init__(field, case, symbol=symbol, is_format=is_format)

    def format(self):
        return '`{field}` {symbol} {case}'.format(field=self.field, symbol=self.symbol, case=self.case)
