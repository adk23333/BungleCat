from tortoise import Model, fields


class Thread(Model):
    """
    记录已加入检查队列的主题贴

    Notes: 有记录的主题贴不代表已经检查过，当检查过程中终止程序，可能会有主题贴未被检查
    """
    tid = fields.BigIntField(pk=True)
    fid = fields.BigIntField()
    last_time = fields.BigIntField()

    class Meta:
        table = "review_thread"


class Post(Model):
    """
    记录已加入检查队列的楼层及楼中楼

    Notes: 有记录的楼层及楼中楼不代表已经检查过，当检查过程中终止程序，可能会有楼层及楼中楼未被检查
    """
    pid = fields.BigIntField(pk=True)
    tid = fields.BigIntField()
    ppid = fields.BigIntField(null=True, default=None)
    reply_num = fields.IntField(null=True, default=None)

    class Meta:
        table = "review_post"