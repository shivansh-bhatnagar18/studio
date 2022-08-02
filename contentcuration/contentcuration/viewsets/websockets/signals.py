from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from contentcuration.models import Change


@receiver(post_save, sender=Change, weak=False)
def broadcast_new_change_model_handler(sender, instance, created, **kwargs):
    broadcast_new_change_model(instance)


def broadcast_new_change_model(instance):
    channel_layer = get_channel_layer()
    serialized_change_object = Change.serialize(instance)
    # Name of channel group
    room_group_name = str(instance.channel_id or "dummy")

    # name of indiviual_user group
    indiviual_room_group_name = str(instance.user_id or "dummy")

    print("DEBUG", room_group_name)
    print("DEBUG", indiviual_room_group_name)

    # if the change object is errored then we broadcast the info back to indiviual user
    if instance.errored:
        async_to_sync(channel_layer.group_send)(
            instance.created_by_id,
            {
                'type': 'broadcast_changes',
                'errored': serialized_change_object
            }
        )

    # if the change is related to channel we broadcast changes to channel group
    if not indiviual_room_group_name and room_group_name:
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'broadcast_changes',
                'change': serialized_change_object
            }
        )
    # if the change is only related to indiviual user
    elif indiviual_room_group_name and not room_group_name:
        async_to_sync(channel_layer.group_send)(
            indiviual_room_group_name,
            {
                'type': 'broadcast_changes',
                'change': serialized_change_object
            }
        )
    # if the change is realted to both user and channel then we will broadcast to both of the groups
    elif indiviual_room_group_name and room_group_name:
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'broadcast_changes',
                'change': serialized_change_object
            }
        )
        async_to_sync(channel_layer.group_send)(
            indiviual_room_group_name,
            {
                'type': 'broadcast_changes',
                'change': serialized_change_object
            }
        )
