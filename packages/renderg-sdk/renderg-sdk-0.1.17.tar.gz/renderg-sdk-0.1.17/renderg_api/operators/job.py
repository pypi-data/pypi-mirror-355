from renderg_api.connect import Connect
from renderg_api.constants import ControlType
from renderg_utils import *


class JobOperator(object):

    def __init__(self, connect: 'Connect'):
        self._connect = connect

    def new_job(self, dcc_file_path, project_id, env_id):
        params = {
            'scene_path': dcc_file_path,
            'scene_type': SceneType.get_scene_file_type(dcc_file_path),
            'project_id': project_id,
            'env_id': env_id,
            'submit_type': 902,
            'transport': '2',

            # other msg
            'client_version': get_version(),
            'client_address': get_pc_ip(),
            'os': get_pc_version(),
            'mac': get_mac_address(),
            'submit_user': get_pc_name()
        }
        response = self._connect.post(self._connect.urls.NewJob, params)
        return response.get("job_id")

    def update_job_status(self, job_id, status):
        params = {
            "job_id": job_id,
            "status": status
        }
        return self._connect.post(self._connect.urls.UpdateJobStatus, params)

    def _control_job(self, job_ids: 'list', control_type, tiled_job_ids: 'list' = []):
        params = {
            'job_array': job_ids,
            'tiled_job_array': tiled_job_ids,
            "type": control_type
        }
        return self._connect.post(self._connect.urls.ControlJob, params)

    def start_job(self, job_ids: 'list', tiled_job_ids: 'list' = []):
        return self._control_job(job_ids, ControlType.START, tiled_job_ids)

    def stop_job(self, job_ids: 'list', tiled_job_ids: 'list' = []):
        return self._control_job(job_ids, ControlType.STOP, tiled_job_ids)

    def speedup_job(self, job_ids: 'list', tiled_job_ids: 'list' = []):
        return self._control_job(job_ids, ControlType.SPEEDUP, tiled_job_ids)

    def requeue_job(self, job_ids: 'list', tiled_job_ids: 'list' = []):
        return self._control_job(job_ids, ControlType.REQUEUE, tiled_job_ids)

    def delete_job(self, job_ids: 'list'):
        params = {'job_ids': job_ids}
        return self._connect.post(self._connect.urls.DelJob, params)

    def set_job_config(self, job_id, zone, ram):
        params = {
            'job_id': job_id,
            'ram_limit': ram,
            'cluster_id': self._connect.cluster_id,
            'zone_id': zone
        }
        return self._connect.post(self._connect.urls.SetJobConfig, params)

    def submit_job(self, job_id):
        params = {
            'job_id': job_id,
            'submit_version': "2"
        }
        return self._connect.post(self._connect.urls.SubmitJob, params)

    def get_jobs_info(self, job_id):
        return self._connect.get(self._connect.urls.JobInfo + str(job_id))
