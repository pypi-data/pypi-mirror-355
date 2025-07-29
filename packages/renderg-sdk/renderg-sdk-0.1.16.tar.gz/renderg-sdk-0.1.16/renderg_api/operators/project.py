
class ProjectOperator(object):

    def __init__(self, connect):
        self._connect = connect

    def get_project_list(self):
        response = self._connect.post(self._connect.urls.GetEnvList)
        return response.get("data")
