from flask_appbuilder import ModelView
from flask_appbuilder.api import ModelRestApi, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from .models import File
from .log_models import FileAccessLog
from flask import request, jsonify
from flask_login import current_user
import datetime, json

class FileView(ModelView):
    datamodel = SQLAInterface(File)
    class_permission_name = 'File'
    def post_add(self, item): self._log('CREATE', item.id)
    def post_update(self, item): self._log('UPDATE', item.id)
    def pre_delete(self, item): self._log('DELETE', item.id)
    def _log(self, action, file_id):
        try:
            log = FileAccessLog()
            log.user_id = current_user.id
            log.action = action
            log.file_id = file_id
            log.ip_address = request.remote_addr or '127.0.0.1'
            log.timestamp = datetime.datetime.utcnow()
            log.success = True
            self.datamodel.session.add(log)
            self.datamodel.session.commit()
        except Exception as e: print(f"日志失败: {e}")

class FileApi(ModelRestApi):
    datamodel = SQLAInterface(File)
    resource_name = 'file'
    allow_browser_login = True
    show_columns = ['id', 'filename', 'content', 'file_size', 'created_at']

    def check_permission(self, action):
        """viewer 禁止增删改"""
        if current_user.is_authenticated:
            roles = [r.name for r in current_user.roles]
            if 'viewer' in roles and action in ['can_add', 'can_edit', 'can_delete', 'can_post', 'can_put']:
                return False
        return super().check_permission(action)

    @expose('/upload', methods=['POST'])
    def upload(self):
        f = request.files.get('file')
        if not f: return self.response_400(message="没有文件")
        filename = f.filename
        content = f.read().decode('utf-8', errors='ignore')
        file_size = len(content)
        item = File()
        item.filename = filename
        item.content = content
        item.file_size = file_size
        item.owner_id = current_user.id if current_user.is_authenticated else 1
        item.created_at = datetime.datetime.utcnow()
        self.datamodel.session.add(item)
        self.datamodel.session.commit()
        self._log('CREATE', item.id)
        return self.response(201, id=item.id, filename=item.filename, file_size=item.file_size)

    def post_headless(self):
        result = super().post_headless()
        data = json.loads(result.get_data(as_text=True))
        if 'id' in data: self._log('CREATE', data['id'])
        return result
    def put_headless(self, pk):
        result = super().put_headless(pk)
        self._log('UPDATE', pk)
        return result
    def delete_headless(self, pk):
        self._log('DELETE', pk)
        return super().delete_headless(pk)
    def _log(self, action, file_id):
        try:
            log = FileAccessLog()
            log.user_id = current_user.id if current_user.is_authenticated else 1
            log.action = action
            log.file_id = file_id
            log.ip_address = request.remote_addr or '127.0.0.1'
            log.timestamp = datetime.datetime.utcnow()
            log.success = True
            self.datamodel.session.add(log)
            self.datamodel.session.commit()
        except Exception as e: print(f"日志失败: {e}")
