# Faraday Penetration Test IDE
# Copyright (C) 2016  Infobyte LLC (http://www.infobytesec.com/)
# See the file 'doc/LICENSE' for the license information
import time

import flask
from flask import Blueprint
from marshmallow import fields, post_load

from server.api.base import AutoSchema, ReadWriteWorkspacedView
from server.models import Credential, Host, Service, db

credentials_api = Blueprint('credentials_api', __name__)


class CredentialSchema(AutoSchema):
    _id = fields.Integer(dump_only=True, attribute='id')
    _rev = fields.String(default='', dump_only=True)
    metadata = fields.Method('get_metadata')
    owned = fields.Boolean(default=False)
    owner = fields.String(dump_only=True, attribute='creator.username', default='')
    username = fields.String(default='')
    password = fields.String(default='')
    description = fields.String(default='')
    couchdbid = fields.String(default='')  # backwards compatibility
    parent_type = fields.Method('get_parent_type', required=True)
    parent = fields.Method('get_parent', required=True)

    def get_parent(self, obj):
        return obj.parent.id

    def get_parent_type(self, obj):
        return obj.parent.__class__.__name__

    def get_metadata(self, obj):
        return {
            "command_id": "e1a042dd0e054c1495e1c01ced856438",
            "create_time": time.mktime(obj.create_date.utctimetuple()),
            "creator": "Metasploit",
            "owner": "", "update_action": 0,
            "update_controller_action": "No model controller call",
            "update_time": time.mktime(obj.update_date.utctimetuple()),
            "update_user": ""
        }


    class Meta:
        model = Credential
        fields = ('id', '_id', "_rev", 'parent',
                  'username', 'description',
                  'name', 'password',
                  'owner', 'owned', 'couchdbid',
                  'parent', 'parent_type',
                  'metadata')

    @post_load
    def set_parent(self, data):
        parent_type = data.pop('parent_type', None)
        parent_id = data.pop('parent', None)
        if parent_type == 'Host':
            parent_class = Host
            parent_field = 'host_id'
        if parent_type == 'Service':
            parent_class = Service
            parent_field = 'service_id'
        parent = db.session.query(parent_class).filter_by(id=parent_id).first()
        data[parent_field] = parent.id
        return data


class CredentialView(ReadWriteWorkspacedView):
    route_base = 'credential'
    model_class = Credential
    schema_class = CredentialSchema

    def _envelope_list(self, objects, pagination_metadata=None):
        credentials = []
        for credential in objects:
            credentials.append({
                'id': credential['_id'],
                'key': credential['_id'],
                'value': credential
            })
        return {
            'rows': credentials,
        }


CredentialView.register(credentials_api)
