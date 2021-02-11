

def apply_conversion_to_doccano_format(row):
    return {
        'text': row.get('text'),
        'labels': row.get('labels'),
        'meta': {
            'is_revision': row.get('is_revision'),
            'revision_id': row.get('revision_id'),
            'revision_url': row.get('revision_url')
        }
    }
