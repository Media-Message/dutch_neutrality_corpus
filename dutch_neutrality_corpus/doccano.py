

def apply_filter_for_doccano_format(row):

    first_object = row[0]
    # TODO: remove hack later...
    if first_object.get('text'):
        return {
            'text': first_object.get('text'),
            'labels': first_object.get('labels'),
            'meta': {
                'is_revision': first_object.get('is_revision'),
                'revision_id': first_object.get('revision_id'),
                'revision_url': first_object.get('revision_url')
            }
        }
