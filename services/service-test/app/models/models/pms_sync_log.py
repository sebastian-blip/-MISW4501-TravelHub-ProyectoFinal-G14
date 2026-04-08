from tortoise import fields
from tortoise.models import Model


class PmsSyncLog(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    pms_provider = fields.CharField(max_length=100)
    sync_type = fields.CharField(max_length=50)
    status = fields.CharField(max_length=50)
    records_synced = fields.IntField(default=0)
    error_message = fields.TextField(null=True)
    started_at = fields.DatetimeField()
    completed_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pms_sync_logs"
        app = "pms_service"

    def __str__(self):
        return f"PMS Sync {self.pms_provider} - {self.sync_type}"
