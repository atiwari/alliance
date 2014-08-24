import urlparse

from alliance.thrift.service.ttypes import AException
from alliance.openstack.common import gettextutils as u

_FATAL_EXCEPTION_FORMAT_ERRORS = False


class RedirectException(Exception):
    def __init__(self, url):
        self.url = urlparse.urlparse(url)

class ErrorCode(object):
    #1 for TXT issues
    TKT_UNWRAP_FAILED = 1101
    TKT_SESSION_KEY_MISMATCH = 1102
    TKT_VERIFICATION_FAILED = 1103
    TKT_AMBIGUEUS_SESSION_ATTEMPT = 1104
    #2 for partner issues
    PARTNER_NOT_FOUND = 2404
    #5 for server issue
    INTERNAL_SERVER_ERROR = 501
    CONFIG_ISSUES = 502

     
    
class AllianceException(AException):
    message = u._("An unknown exception occurred")

    def __init__(self, code=None, message=None, *args, **kwargs):
        
        if not code:
            code = self.code
        if not message:
            message = self.message
        try:
            message = message % kwargs
        except Exception as e:
            if _FATAL_EXCEPTION_FORMAT_ERRORS:
                raise e
            else:
                pass
        super(AllianceException, self).__init__(code, message)

class PartnerNotFound(AllianceException):
    message = u._("Partner with cloud_id '%(cloud_id)s' not found.")

    def __init__(self, *args, **kwargs):
        super(PartnerNotFound, self).__init__(*args, **kwargs)
        self.cloud_id = kwargs.get('cloud_id')


class PartnerValidationFailed(AllianceException):
    message = u._("Validation failed for cloud_id '%(cloud_id)s'.")

    def __init__(self, *args, **kwargs):
        super(PartnerValidationFailed, self).__init__(*args, **kwargs)
        self.cloud_id = kwargs.get('cloud_id')


class ConfigurationIssues(AllianceException):
    message = u._("Configuration issues for cloud_id '%(cloud_id)s'.")

    def __init__(self, *args, **kwargs):
        super(ConfigurationIssues, self).__init__(*args, **kwargs)
        self.cloud_id = kwargs.get('cloud_id')
        
class NotFound(AllianceException):
    message = u._("An object with the specified identifier was not found.")



class FeatureNotImplemented(AllianceException):
    message = u._("Feature not implemented for value set on field "
                  "'%(field)s' on " "schema '%(schema)s': %(reason)s")

    def __init__(self, *args, **kwargs):
        super(FeatureNotImplemented, self).__init__(*args, **kwargs)
        self.invalid_field = kwargs.get('field')

"""
raise exception.FeatureNotImplemented(field='type',
                                                  schema=schema_name,
                                                  reason=u._("Feature not"
                                                             " implemented for"
                                                             " 'certificate'")
                                                  )
class MissingArgumentError(AllianceException):
    message = u._("Missing required argument.")


class MissingCredentialError(AllianceException):
    message = u._("Missing required credential: %(required)s")


class BadAuthStrategy(AllianceException):
    message = u._("Incorrect auth strategy, expected \"%(expected)s\" but "
                  "received \"%(received)s\"")

class UnknownScheme(AllianceException):
    message = u._("Unknown scheme '%(scheme)s' found in URI")


class BadStoreUri(AllianceException):
    message = u._("The Store URI was malformed.")


class Duplicate(AllianceException):
    message = u._("An object with the same identifier already exists.")


class StorageFull(AllianceException):
    message = u._("There is not enough disk space on the image storage media.")


class StorageWriteDenied(AllianceException):
    message = u._("Permission to write image storage media denied.")


class AuthBadRequest(AllianceException):
    message = u._("Connect error/bad request to Auth service at URL %(url)s.")


class AuthUrlNotFound(AllianceException):
    message = u._("Auth service at URL %(url)s not found.")


class AuthorizationFailure(AllianceException):
    message = u._("Authorization failed.")


class NotAuthenticated(AllianceException):
    message = u._("You are not authenticated.")


class Forbidden(AllianceException):
    message = u._("You are not authorized to complete this action.")


class NotSupported(AllianceException):
    message = u._("Operation is not supported.")


class ForbiddenPublicImage(Forbidden):
    message = u._("You are not authorized to complete this action.")


class ProtectedImageDelete(Forbidden):
    message = u._("Image %(image_id)s is protected and cannot be deleted.")


#NOTE(bcwaldon): here for backwards-compatibility, need to deprecate.
class NotAuthorized(Forbidden):
    message = u._("You are not authorized to complete this action.")


class Invalid(AllianceException):
    message = u._("Data supplied was not valid.")


class NoDataToProcess(AllianceException):
    message = u._("No data supplied to process.")


class InvalidSortKey(Invalid):
    message = u._("Sort key supplied was not valid.")


class InvalidFilterRangeValue(Invalid):
    message = u._("Unable to filter using the specified range.")


class ReadonlyProperty(Forbidden):
    message = u._("Attribute '%(property)s' is read-only.")


class ReservedProperty(Forbidden):
    message = u._("Attribute '%(property)s' is reserved.")


class AuthorizationRedirect(AllianceException):
    message = u._("Redirecting to %(uri)s for authorization.")


class DatabaseMigrationError(AllianceException):
    message = u._("There was an error migrating the database.")


class ClientConnectionError(AllianceException):
    message = u._("There was an error connecting to a server")


class ClientConfigurationError(AllianceException):
    message = u._("There was an error configuring the client.")


class MultipleChoices(AllianceException):
    message = u._("The request returned a 302 Multiple Choices. This "
                  "generally means that you have not included a version "
                  "indicator in a request URI.\n\nThe body of response "
                  "returned:\n%(body)s")


class LimitExceeded(AllianceException):
    message = u._("The request returned a 413 Request Entity Too Large. This "
                  "generally means that rate limiting or a quota threshold "
                  "was breached.\n\nThe response body:\n%(body)s")

    def __init__(self, *args, **kwargs):
        super(LimitExceeded, self).__init__(*args, **kwargs)
        self.retry_after = (int(kwargs['retry']) if kwargs.get('retry')
                            else None)


class ServiceUnavailable(AllianceException):
    message = u._("The request returned 503 Service Unavilable. This "
                  "generally occurs on service overload or other transient "
                  "outage.")

    def __init__(self, *args, **kwargs):
        super(ServiceUnavailable, self).__init__(*args, **kwargs)
        self.retry_after = (int(kwargs['retry']) if kwargs.get('retry')
                            else None)


class ServerError(AllianceException):
    message = u._("The request returned 500 Internal Server Error.")


class UnexpectedStatus(AllianceException):
    message = u._("The request returned an unexpected status: %(status)s."
                  "\n\nThe response body:\n%(body)s")


class InvalidContentType(AllianceException):
    message = u._("Invalid content type %(content_type)s")


class InvalidContentEncoding(AllianceException):
    message = u._("Invalid content encoding %(content_encoding)s")


class PayloadDecodingError(AllianceException):
    message = u._("Error while attempting to decode payload.")


class BadRegistryConnectionConfiguration(AllianceException):
    message = u._("Registry was not configured correctly on API server. "
                  "Reason: %(reason)s")


class BadStoreConfiguration(AllianceException):
    message = u._("Store %(store_name)s could not be configured correctly. "
                  "Reason: %(reason)s")


class BadDriverConfiguration(AllianceException):
    message = u._("Driver %(driver_name)s could not be configured correctly. "
                  "Reason: %(reason)s")


class StoreDeleteNotSupported(AllianceException):
    message = u._("Deleting images from this store is not supported.")


class StoreAddDisabled(AllianceException):
    message = u._("Configuration for store failed. Adding images to this "
                  "store is disabled.")


class InvalidNotifierStrategy(AllianceException):
    message = u._("'%(strategy)s' is not an available notifier strategy.")


class MaxRedirectsExceeded(AllianceException):
    message = u._("Maximum redirects (%(redirects)s) was exceeded.")


class InvalidRedirect(AllianceException):
    message = u._("Received invalid HTTP redirect.")


class NoServiceEndpoint(AllianceException):
    message = u._("Response from Keystone does not contain a "
                  "Barbican endpoint.")


class RegionAmbiguity(AllianceException):
    message = u._("Multiple 'image' service matches for region %(region)s. "
                  "This generally means that a region is required and you "
                  "have not supplied one.")


class WorkerCreationFailure(AllianceException):
    message = u._("Server worker creation failed: %(reason)s.")


class SchemaLoadError(AllianceException):
    message = u._("Unable to load schema: %(reason)s")


class InvalidObject(AllianceException):
    message = u._("Provided object does not match schema "
                  "'%(schema)s': %(reason)s")

    def __init__(self, *args, **kwargs):
        super(InvalidObject, self).__init__(*args, **kwargs)
        self.invalid_property = kwargs.get('property')


class UnsupportedField(AllianceException):
    message = u._("No support for value set on field '%(field)s' on "
                  "schema '%(schema)s': %(reason)s")

    def __init__(self, *args, **kwargs):
        super(UnsupportedField, self).__init__(*args, **kwargs)
        self.invalid_field = kwargs.get('field')


class FeatureNotImplemented(AllianceException):
    message = u._("Feature not implemented for value set on field "
                  "'%(field)s' on " "schema '%(schema)s': %(reason)s")

    def __init__(self, *args, **kwargs):
        super(FeatureNotImplemented, self).__init__(*args, **kwargs)
        self.invalid_field = kwargs.get('field')


class UnsupportedHeaderFeature(AllianceException):
    message = u._("Provided header feature is unsupported: %(feature)s")


class InUseByStore(AllianceException):
    message = u._("The image cannot be deleted because it is in use through "
                  "the backend store outside of Barbican.")


class ImageSizeLimitExceeded(AllianceException):
    message = u._("The provided image is too large.")
"""