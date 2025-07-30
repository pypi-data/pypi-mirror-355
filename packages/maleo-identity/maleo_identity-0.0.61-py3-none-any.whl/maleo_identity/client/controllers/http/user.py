from typing import Dict, Optional
from maleo_foundation.authorization import Authorization
from maleo_foundation.managers.client.base import BearerAuth
from maleo_foundation.managers.client.maleo import MaleoClientHTTPController
from maleo_foundation.models.transfers.results.client.controllers.http \
    import BaseClientHTTPControllerResults
from maleo_foundation.utils.merger import deep_merge
from maleo_identity.models.transfers.parameters.general.user \
    import MaleoIdentityUserGeneralParametersTransfers
from maleo_identity.models.transfers.parameters.general.user_organization \
    import MaleoIdentityUserOrganizationGeneralParametersTransfers
from maleo_identity.models.transfers.parameters.general.user_system_role \
    import MaleoIdentityUserSystemRoleGeneralParametersTransfers
from maleo_identity.models.transfers.parameters.general.user_organization_role \
    import MaleoIdentityUserOrganizationRoleGeneralParametersTransfers
from maleo_identity.models.transfers.parameters.client.user \
    import MaleoIdentityUserClientParametersTransfers
from maleo_identity.models.transfers.parameters.client.user_organization \
    import MaleoIdentityUserOrganizationClientParametersTransfers
from maleo_identity.models.transfers.parameters.client.user_system_role \
    import MaleoIdentityUserSystemRoleClientParametersTransfers
from maleo_identity.models.transfers.parameters.client.user_organization_role \
    import MaleoIdentityUserOrganizationRoleClientParametersTransfers

class MaleoIdentityUserHTTPController(MaleoClientHTTPController):
    async def get_users(
        self,
        parameters:MaleoIdentityUserClientParametersTransfers.GetMultiple,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Fetch users from MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/"

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserClientParametersTransfers
                .GetMultipleQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(
                    exclude={"sort_columns", "date_filters"},
                    exclude_none=True
                )
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.get(url=url, params=params, headers=headers, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def get_user(
        self,
        parameters:MaleoIdentityUserGeneralParametersTransfers.GetSingle,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Fetch user from MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/{parameters.identifier}/{parameters.value}"

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserGeneralParametersTransfers
                .GetSingleQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(exclude_none=True)
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.get(url=url, params=params, headers=headers, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def create(
        self,
        parameters:MaleoIdentityUserGeneralParametersTransfers.Create,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Create a new user in MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/"

            #* Declare body
            json = (
                MaleoIdentityUserGeneralParametersTransfers
                .CreateData
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump()
            )

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserGeneralParametersTransfers
                .CreateOrUpdateQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(exclude_none=True)
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.post(url=url, json=json, params=params, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def update(
        self,
        parameters:MaleoIdentityUserGeneralParametersTransfers.Update,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Update user's data in MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/{parameters.identifier}/{parameters.value}"

            #* Declare body
            json = (
                MaleoIdentityUserGeneralParametersTransfers
                .UpdateData
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump()
            )

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserGeneralParametersTransfers
                .CreateOrUpdateQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(exclude_none=True)
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.put(url=url, json=json, params=params, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def get_password(
        self,
        parameters:MaleoIdentityUserGeneralParametersTransfers.GetSinglePassword,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Get user's password from MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/{parameters.identifier}/{parameters.value}/password"

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.get(url=url, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def get_user_system_roles(
        self,
        parameters:MaleoIdentityUserSystemRoleClientParametersTransfers.GetMultipleFromUser,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Get user's system roles from MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/{parameters.user_id}/system-roles/"

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserSystemRoleClientParametersTransfers
                .GetMultipleFromUserQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(
                    exclude={"sort_columns", "date_filters"},
                    exclude_none=True
                )
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.get(url=url, params=params, headers=headers, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def get_user_system_role(
        self,
        parameters:MaleoIdentityUserSystemRoleGeneralParametersTransfers.GetSingle,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Get user's system role from MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/{parameters.user_id}/system-roles/{parameters.system_role}"

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserSystemRoleGeneralParametersTransfers
                .GetSingleQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(exclude_none=True)
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.get(url=url, params=params, headers=headers, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def get_user_organizations(
        self,
        parameters:MaleoIdentityUserOrganizationClientParametersTransfers.GetMultipleFromUser,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Get user's organization roles from MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/{parameters.user_id}/organizations/"

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserOrganizationClientParametersTransfers
                .GetMultipleFromUserQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(
                    exclude={"sort_columns", "date_filters"},
                    exclude_none=True
                )
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.get(url=url, params=params, headers=headers, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def get_user_organization(
        self,
        parameters:MaleoIdentityUserOrganizationGeneralParametersTransfers.GetSingle,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Get user's organization role from MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/{parameters.user_id}/organizations/{parameters.organization_id}"

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserOrganizationGeneralParametersTransfers
                .GetSingleQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(exclude_none=True)
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.get(url=url, params=params, headers=headers, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def get_user_organization_roles(
        self,
        parameters:MaleoIdentityUserOrganizationRoleClientParametersTransfers.GetMultipleFromUserOrOrganization,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Get user's organization roles from MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/{parameters.user_id}/organizations/{parameters.organization_id}/roles/"

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserOrganizationRoleClientParametersTransfers
                .GetMultipleFromUserOrOrganizationQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(
                    exclude={"sort_columns", "date_filters"},
                    exclude_none=True
                )
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.get(url=url, params=params, headers=headers, auth=auth)
            return BaseClientHTTPControllerResults(response=response)

    async def get_user_organization_role(
        self,
        parameters:MaleoIdentityUserOrganizationRoleGeneralParametersTransfers.GetSingle,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> BaseClientHTTPControllerResults:
        """Get user's organization role from MaleoIdentity"""
        async with self._manager.get_client() as client:
            #* Define URL
            url = f"{self._manager.url}/v1/users/{parameters.user_id}/organizations/{parameters.organization_id}/roles/{parameters.key}"

            #* Parse parameters to query params
            params = (
                MaleoIdentityUserOrganizationRoleGeneralParametersTransfers
                .GetSingleQuery
                .model_validate(
                    parameters.model_dump()
                )
                .model_dump(exclude_none=True)
            )

            #* Create headers
            base_headers = {
                "Content-Type": "application/json"
            }
            if headers is not None:
                headers = deep_merge(
                    base_headers,
                    headers
                )
            else:
                headers = base_headers

            #* Create auth
            token = None
            if authorization and authorization.scheme == "Bearer":
                token = authorization.credentials
            elif self._service_manager.token:
                token = self._service_manager.token
            auth = BearerAuth(token) if token else None

            #* Send request and wait for response
            response = await client.get(url=url, params=params, headers=headers, auth=auth)
            return BaseClientHTTPControllerResults(response=response)