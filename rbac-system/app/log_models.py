from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, DateTime, Boolean
import datetime

class FileAccessLog(Model):
    __tablename__ = 'file_access_log'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String(50))
    file_id = Column(Integer)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    success = Column(Boolean, default=True)
