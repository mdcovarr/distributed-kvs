PORT = 13800
IP_ADDRESS = '0.0.0.0'
KEY_LENGTH = 50
ADDED_MESSAGE = 'Added successfully'
UPDATED_MESSAGE = 'Updated successfully'
RETRIEVED_MESSAGE = 'Retrieved successfully'
KEY_ERROR = 'Key does not exist'
GET_ERROR_MESSAGE = 'Error in GET'
DELETE_SUCCESS_MESSAGE = 'Deleted successfully'
DELETE_ERROR_MESSAGE = 'Error in DELETE'

MISSING_RESPONSE = {
    "error": "Value is missing",
    "message": "Error in PUT"
}

BAD_FORMAT_RESPONSE = {
    "error": "Bad json format",
    "message": "Error in PUT"
}

ADD_AND_REPLACE_RESPONSE = {
    "message": "Added successfully",
    "replaced": False
}

LONG_KEY_RESPONSE = {
    "error": "Key is too long",
    "message": "Error in PUT"
}

TIMEOUT = 3
