

def automoderate(instance, user):
    '''
    Auto moderates given model instance on user. Returns moderation status:
    0 - Rejected
    1 - Approved
    '''
    instance.moderated_object.changed_by = user
    instance.moderated_object.save()
    
    return instance.moderated_object.moderation_status
