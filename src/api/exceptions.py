class ApiException(Exception):
    def __init__(self, message):
        super(ApiException, self).__init__(message)
        self.message = message


class InvalidPropertyDataType(ApiException):
    def __init__(self, property_id, provided_data_type, needed_data_type):
        self.property_id = property_id
        self.provided_data_type = provided_data_type
        self.needed_data_type = needed_data_type
        message = (
            f"Invalid data type for the property {property_id}: "
            f"'{provided_data_type}' was provided but it needs '{needed_data_type}'."
        )
        return super().__init__(message)


class NonexistantPropertyOrNoDataType(ApiException):
    def __init__(self, property_id):
        self.property_id = property_id
        message = (
            f"The property {property_id} does not exist or "
            "does not have a data type."
        )
        return super().__init__(message)


class NoStatementsForThatProperty(ApiException):
    def __init__(self, entity_id, property_id):
        self.entity_id = entity_id
        self.property_id = property_id
        message = (
            f"The entity {entity_id} has no statements "
            f"for the property {property_id}"
        )
        return super().__init__(message)


class NoStatementsWithThatValue(ApiException):
    def __init__(self, entity_id, property_id, value):
        self.entity_id = entity_id
        self.property_id = property_id
        self.value = value
        message = (
            f"The entity {entity_id} has no statements "
            f"with value '{value}' for the property {property_id}"
        )
        return super().__init__(message)


class UserError(ApiException):
    def __init__(self, response_code, response_message):
        self.response_code = response_code
        self.response_message = response_message
        message = f"Error ('{response_code}'): {response_message}"
        return super().__init__(message)


class ServerError(ApiException):
    def __init__(self, response_json):
        self.response_json = response_json
        message = f"The server failed to process the request: {response_json}"
        return super().__init__(message)


class ApiNotImplemented(ApiException):
    def __init__(self):
        message = "That functionality is not implemented yet"
        return super().__init__(message)


class EntityTypeNotImplemented(ApiException):
    def __init__(self, entity_id):
        message = f"{entity_id}: entity type not supported"
        return super().__init__(message)


class NoToken(ApiException):
    def __init__(self, username):
        self.username = username
        message = f"We don't have an authentication token for the user '{username}'"
        return super().__init__(message)


class InternalInvalidState(ApiException):
    def __init__(self, message):
        message = f"There's something wrong in our side: {message}"
        return super().__init__(message)
