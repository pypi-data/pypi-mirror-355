from bottle import SimpleTemplate


class SqlTemplate:
    def __init__(self, template):
        self.sTemplate = SimpleTemplate(template)
        self.sTemplate._escape = self._escape_replacement
        self.trackedParams = []

    def render(self, *args, **kwargs):
        paramTemplate = self.sTemplate.render(*args, **kwargs)
        params = tuple(self.trackedParams)
        self.trackedParams = []
        return paramTemplate, params

    def _escape_replacement(self, string):
        self.trackedParams.append(string)
        return "?"


def render(template, *args, **kwargs):
    return SqlTemplate(template).render(*args, **kwargs)

