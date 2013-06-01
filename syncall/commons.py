import os
import uuid


def generate_uuid(storage_file):
    # Store UUID based on the hostname and current time to have
    # a unique identifier of this PC
    program_id = str(uuid.uuid1())

    with open(storage_file, 'w') as store:
        store.write(program_id)

    return program_id


def get_uuid(storage_file):
    if os.path.isfile(storage_file):
        with open(storage_file, 'r') as store:
            program_id = store.read()

        return program_id
    else:
        return generate_uuid(storage_file)
