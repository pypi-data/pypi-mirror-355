from rest_framework import serializers


class CRUDEventSerializer(serializers.Serializer):
    event_type = serializers.IntegerField(read_only=True)
    object_id = serializers.CharField(read_only=True, default="")
    object_repr = serializers.CharField(read_only=True, default="")
    object_json_repr = serializers.CharField(read_only=True, default="")
    changed_fields = serializers.CharField(read_only=True, default="")
    user_id = serializers.CharField(read_only=True, default="")
    created_at = serializers.SerializerMethodField(read_only=True)

    def get_created_at(self, obj):
        return obj.created_at


class LoginEventSerializer(serializers.Serializer):
    login_type = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True, default="")
    user_id = serializers.CharField(read_only=True, default="")
    remote_ip = serializers.CharField(read_only=True, default="")
    created_at = serializers.SerializerMethodField(read_only=True)

    def get_created_at(self, obj):
        return obj.created_at


class ExternalServiceLogSerializer(serializers.Serializer):
    service_name = serializers.CharField(read_only=True, default="")
    protocol = serializers.CharField(read_only=True, default="")
    request_repr = serializers.CharField(read_only=True, default="")
    response_repr = serializers.CharField(read_only=True, default="")
    error_message = serializers.CharField(read_only=True, default="")
    execution_time = serializers.FloatField(read_only=True, default=0)
    created_at = serializers.SerializerMethodField(read_only=True)
    user_id = serializers.CharField(read_only=True, default="")

    def get_created_at(self, obj):
        return obj.created_at
