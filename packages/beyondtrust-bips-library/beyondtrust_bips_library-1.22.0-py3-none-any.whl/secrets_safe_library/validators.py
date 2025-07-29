"""Custom validator for Cerberus."""

from cerberus import Validator


class CustomValidator(Validator):
    def _validate_is_required_if(self, is_required_if, field, value):
        """
        Custom rule to make a field required if another field has a specific value.

        The rule's arguments are validated against this schema:
        {'type': 'dict', 'schema': {'field': {'type': 'string'}, 'value': {}}}
        """
        other_field = is_required_if["field"]
        required_value = is_required_if["value"]

        # Check if the other field exists and has the required value
        if (
            other_field in self.document
            and self.document[other_field] == required_value
        ):
            if value is None or value == "":
                self._error(
                    field,
                    f"'{field}' is required when '{other_field}' is {required_value}",
                )
