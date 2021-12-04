from marshmallow import Schema, fields


class UserSchema(Schema):
    id = fields.Int()
    username = fields.String()
    discriminator = fields.String()
    nickname = fields.String()
    avatar = fields.Url()


class ChannelSchema(Schema):
    id = fields.Int()
    name = fields.String()
    category = fields.String()


class EmbedSchema(Schema):
    """Refer to https://discord.com/developers/docs/resources/channel#embed-object"""
    pass


class ReactionSchema(Schema):
    reaction = fields.String()
    users = fields.List(fields.Int())


class MessageSchema(Schema):
    author = fields.Integer()
    content = fields.String()
    embeds = fields.List(fields.Nested(EmbedSchema))
    reactions = fields.List(fields.Nested(ReactionSchema))


class MessageQuerySchema(Schema):
    embeds = fields.Bool()
    reactions = fields.Bool()


class MessageUpdateSchema(Schema):
    content = fields.String()
    embeds = fields.List(fields.Nested(EmbedSchema))


class MessageUpdateResponseSchema(Schema):
    id = fields.Integer()
