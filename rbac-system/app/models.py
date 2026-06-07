from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
import datetime

class File(Model):
    __tablename__ = 'file'
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, default='')
    file_size = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey('ab_user.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
