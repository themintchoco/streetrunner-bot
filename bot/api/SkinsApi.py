from marshmallow import Schema, fields, EXCLUDE

from bot.api.api import ApiSchema


class SkinProperty(ApiSchema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String()
    value = fields.String()


class SkinsApi(ApiSchema):
    __endpoints__ = ['https://sessionserver.mojang.com/session/minecraft/profile/{uuid}/']

    class Meta:
        unknown = EXCLUDE

    id = fields.String()
    name = fields.String()
    properties = fields.Nested(SkinProperty, many=True)
