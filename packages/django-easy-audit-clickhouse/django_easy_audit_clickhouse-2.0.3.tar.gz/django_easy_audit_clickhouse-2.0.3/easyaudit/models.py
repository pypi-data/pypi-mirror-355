from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class CRUDEvent(models.Model):
    CREATE = 1
    UPDATE = 2
    DELETE = 3
    M2M_CHANGE = 4
    M2M_CHANGE_REV = 5
    M2M_ADD = 6
    M2M_ADD_REV = 7
    M2M_REMOVE = 8
    M2M_REMOVE_REV = 9
    M2M_CLEAR = 10
    M2M_CLEAR_REV = 11

    TYPES = (
        (CREATE, _("Create")),
        (UPDATE, _("Update")),
        (DELETE, _("Delete")),
        (M2M_CHANGE, _("Many-to-Many Change")),
        (M2M_CHANGE_REV, _("Reverse Many-to-Many Change")),
        (M2M_ADD, _("Many-to-Many Add")),
        (M2M_ADD_REV, _("Reverse Many-to-Many Add")),
        (M2M_REMOVE, _("Many-to-Many Remove")),
        (M2M_REMOVE_REV, _("Reverse Many-to-Many Remove")),
        (M2M_CLEAR, _("Many-to-Many Clear")),
        (M2M_CLEAR_REV, _("Reverse Many-to-Many Clear")),
    )

    event_type = models.SmallIntegerField(choices=TYPES, verbose_name=_("Event type"))
    object_id = models.CharField(max_length=255, verbose_name=_("Object ID"))
    object_repr = models.TextField(
        default="", blank=True, verbose_name=_("Object representation")
    )
    object_json_repr = models.TextField(
        default="", blank=True, verbose_name=_("Object JSON representation")
    )
    changed_fields = models.TextField(
        default="", blank=True, verbose_name=_("Changed fields")
    )
    user_id = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text=_("String version of the user pk"),
        verbose_name=_("User PK as string"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date time"))

    class Meta:
        verbose_name = _("CRUD event")
        verbose_name_plural = _("CRUD events")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["object_id"])]

    def is_create(self):
        return self.event_type == self.CREATE

    def is_update(self):
        return self.event_type == self.UPDATE

    def is_delete(self):
        return self.event_type == self.DELETE


class LoginEvent(models.Model):
    LOGIN = 0
    LOGOUT = 1
    FAILED = 2
    TYPES = (
        (LOGIN, _("Login")),
        (LOGOUT, _("Logout")),
        (FAILED, _("Failed login")),
    )
    login_type = models.SmallIntegerField(choices=TYPES, verbose_name=_("Event type"))
    username = models.CharField(
        max_length=255, default="", blank=True, verbose_name=_("Username")
    )
    user_id = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text=_("String version of the user pk"),
        verbose_name=_("User PK as string"),
    )
    remote_ip = models.CharField(
        max_length=50, default="", db_index=True, verbose_name=_("Remote IP")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date time"))

    class Meta:
        verbose_name = _("login event")
        verbose_name_plural = _("login events")
        ordering = ["-created_at"]


class ExternalServiceLog(models.Model):
    """
    Protocol -> HTTP
    request_repr -> {
        endpoint: "/api/v1/users/",
        method: GET/POST/PUT/DELETE,
        headers: {
            "Authorization": "Bearer <token>",
        }
        body: {
            "username": "testuser",
        }
    }
    response_repr -> {
        status_code: 200,
        body: {
            "username": "testuser",
        }
    }

    Protocol -> SFTP
    request_repr -> {
        host: "sftp.example.com",
        operation: "upload"/"download"/"delete",
        remote_path: "/home/testuser",
        file_name: "testfile.txt",
    }
    response_repr -> {
        success: true
    }
    """

    service_name = models.CharField(max_length=255, verbose_name=_("Service"))
    protocol = models.CharField(max_length=255, verbose_name=_("Protocol"))
    request_repr = models.TextField(
        default="", blank=True, verbose_name=_("Request representation")
    )
    response_repr = models.TextField(
        default="", blank=True, verbose_name=_("Response representation")
    )
    error_message = models.TextField(
        default="", blank=True, verbose_name=_("Error message")
    )
    execution_time = models.FloatField(help_text="Time taken in seconds", null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date time"))
    user_id = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text=_("String version of the user pk"),
        verbose_name=_("User PK as string"),
    )

    class Meta:
        verbose_name = _("external client event")
        verbose_name_plural = _("external client events")
        ordering = ["-created_at"]
