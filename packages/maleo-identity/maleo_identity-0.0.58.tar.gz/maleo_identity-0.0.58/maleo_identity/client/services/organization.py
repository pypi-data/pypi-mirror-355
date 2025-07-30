from typing import Dict, Optional
from maleo_foundation.authorization import Authorization
from maleo_foundation.managers.client.maleo import MaleoClientService
from maleo_foundation.utils.exceptions import BaseExceptions
from maleo_identity.client.controllers import MaleoIdentityOrganizationControllers
from maleo_identity.enums.general import MaleoIdentityGeneralEnums
from maleo_identity.models.transfers.parameters.general.organization_role \
    import MaleoIdentityOrganizationRoleGeneralParametersTransfers
from maleo_identity.models.transfers.parameters.general.organization \
    import MaleoIdentityOrganizationGeneralParametersTransfers
from maleo_identity.models.transfers.parameters.general.user_organization \
    import MaleoIdentityUserOrganizationGeneralParametersTransfers
from maleo_identity.models.transfers.parameters.general.user_organization_role \
    import MaleoIdentityUserOrganizationRoleGeneralParametersTransfers
from maleo_identity.models.transfers.parameters.client.organization_role \
    import MaleoIdentityOrganizationRoleClientParametersTransfers
from maleo_identity.models.transfers.parameters.client.organization \
    import MaleoIdentityOrganizationClientParametersTransfers
from maleo_identity.models.transfers.parameters.client.user_organization \
    import MaleoIdentityUserOrganizationClientParametersTransfers
from maleo_identity.models.transfers.parameters.client.user_organization_role \
    import MaleoIdentityUserOrganizationRoleClientParametersTransfers
from maleo_identity.models.transfers.results.client.organization_role \
    import MaleoIdentityOrganizationRoleClientResultsTransfers
from maleo_identity.models.transfers.results.client.organization \
    import MaleoIdentityOrganizationClientResultsTransfers
from maleo_identity.models.transfers.results.client.user_organization \
    import MaleoIdentityUserOrganizationClientResultsTransfers
from maleo_identity.models.transfers.results.client.user_organization_role \
    import MaleoIdentityUserOrganizationRoleClientResultsTransfers
from maleo_identity.types.results.client.organization_role \
    import MaleoIdentityOrganizationRoleClientResultsTypes
from maleo_identity.types.results.client.organization \
    import MaleoIdentityOrganizationClientResultsTypes
from maleo_identity.types.results.client.user_organization \
    import MaleoIdentityUserOrganizationClientResultsTypes
from maleo_identity.types.results.client.user_organization_role \
    import MaleoIdentityUserOrganizationRoleClientResultsTypes

class MaleoIdentityOrganizationClientService(MaleoClientService):
    def __init__(
        self,
        key,
        logger,
        service_manager,
        controllers:MaleoIdentityOrganizationControllers
    ):
        super().__init__(key, logger, service_manager)
        self._controllers = controllers

    @property
    def controllers(self) -> MaleoIdentityOrganizationControllers:
        raise self._controllers

    async def get_organizations(
        self,
        parameters:MaleoIdentityOrganizationClientParametersTransfers.GetMultiple,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityOrganizationClientResultsTypes.GetMultiple:
        """Retrieve organizations from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving organizations",
            logger=self._logger,
            fail_result_class=MaleoIdentityOrganizationClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityOrganizationClientParametersTransfers.GetMultiple,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve organizations using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_organizations(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                if controller_result.content["data"] is None:
                    return (
                        MaleoIdentityOrganizationClientResultsTransfers
                        .NoData
                        .model_validate(controller_result.content)
                    )
                else:
                    return (
                        MaleoIdentityOrganizationClientResultsTransfers
                        .MultipleData
                        .model_validate(controller_result.content)
                    )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_structured_organizations(
        self,
        parameters:MaleoIdentityOrganizationClientParametersTransfers.GetMultipleStructured,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityOrganizationClientResultsTypes.GetMultipleStructured:
        """Retrieve structured organizations from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving structured organizations",
            logger=self._logger,
            fail_result_class=MaleoIdentityOrganizationClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityOrganizationClientParametersTransfers.GetMultipleStructured,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve structured organizations using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_structured_organizations(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                if controller_result.content["data"] is None:
                    return (
                        MaleoIdentityOrganizationClientResultsTransfers
                        .NoData
                        .model_validate(controller_result.content)
                    )
                else:
                    return (
                        MaleoIdentityOrganizationClientResultsTransfers
                        .MultipleStructured
                        .model_validate(controller_result.content)
                    )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_organization(
        self,
        parameters:MaleoIdentityOrganizationGeneralParametersTransfers.GetSingle,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityOrganizationClientResultsTypes.GetSingle:
        """Retrieve organization from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving organization",
            logger=self._logger,
            fail_result_class=MaleoIdentityOrganizationClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityOrganizationGeneralParametersTransfers.GetSingle,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve organization using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_organization(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .SingleData
                    .model_validate(controller_result.content)
                )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_structured_organization(
        self,
        parameters:MaleoIdentityOrganizationGeneralParametersTransfers.GetSingle,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityOrganizationClientResultsTypes.GetSingleStructured:
        """Retrieve structured organization from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving structured organization",
            logger=self._logger,
            fail_result_class=MaleoIdentityOrganizationClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityOrganizationGeneralParametersTransfers.GetSingle,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve structured organization using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_structured_organization(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .SingleStructured
                    .model_validate(controller_result.content)
                )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_organization_children(
        self,
        parameters:MaleoIdentityOrganizationClientParametersTransfers.GetMultipleChildren,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityOrganizationClientResultsTypes.GetMultiple:
        """Retrieve organization's children from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving organization's children",
            logger=self._logger,
            fail_result_class=MaleoIdentityOrganizationClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityOrganizationClientParametersTransfers.GetMultipleChildren,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve organization's children using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_organization_children(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                if controller_result.content["data"] is None:
                    return (
                        MaleoIdentityOrganizationClientResultsTransfers
                        .NoData
                        .model_validate(controller_result.content)
                        .model_dump(mode="json")
                    )
                else:
                    return (
                        MaleoIdentityOrganizationClientResultsTransfers
                        .MultipleData
                        .model_validate(controller_result.content)
                        .model_dump(mode="json")
                    )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def create(
        self,
        parameters:MaleoIdentityOrganizationGeneralParametersTransfers.Create,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityOrganizationClientResultsTypes.CreateOrUpdate:
        """Create a new organization in MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="creating a new organization",
            logger=self._logger,
            fail_result_class=MaleoIdentityOrganizationClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityOrganizationGeneralParametersTransfers.Create,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Create a new organization using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .create(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .SingleData
                    .model_validate(controller_result.content)
                )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def update(
        self,
        parameters:MaleoIdentityOrganizationGeneralParametersTransfers.Update,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityOrganizationClientResultsTypes.CreateOrUpdate:
        """Update organization's data in MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="updating organization's data",
            logger=self._logger,
            fail_result_class=MaleoIdentityOrganizationClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityOrganizationGeneralParametersTransfers.Update,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Update organization's data using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .update(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                return (
                    MaleoIdentityOrganizationClientResultsTransfers
                    .SingleData
                    .model_validate(controller_result.content)
                )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_organization_users(
        self,
        parameters:MaleoIdentityUserOrganizationClientParametersTransfers.GetMultipleFromOrganization,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityUserOrganizationClientResultsTypes.GetMultiple:
        """Retrieve organization's users from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving organization's users",
            logger=self._logger,
            fail_result_class=MaleoIdentityUserOrganizationClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityUserOrganizationClientParametersTransfers.GetMultipleFromOrganization,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityUserOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve organization's users using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_organization_users(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityUserOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityUserOrganizationClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                if controller_result.content["data"] is None:
                    return (
                        MaleoIdentityUserOrganizationClientResultsTransfers
                        .NoData
                        .model_validate(controller_result.content)
                    )
                else:
                    return (
                        MaleoIdentityUserOrganizationClientResultsTransfers
                        .MultipleData
                        .model_validate(controller_result.content)
                    )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_organization_user(
        self,
        parameters:MaleoIdentityUserOrganizationGeneralParametersTransfers.GetSingle,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityUserOrganizationClientResultsTypes.GetSingle:
        """Retrieve organization's user from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving organization's user",
            logger=self._logger,
            fail_result_class=MaleoIdentityUserOrganizationClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityUserOrganizationGeneralParametersTransfers.GetSingle,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityUserOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve organization's user using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_organization_user(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityUserOrganizationClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityUserOrganizationClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                return (
                    MaleoIdentityUserOrganizationClientResultsTransfers
                    .SingleData
                    .model_validate(controller_result.content)
                )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_organization_roles(
        self,
        parameters:MaleoIdentityOrganizationRoleClientParametersTransfers.GetMultipleFromOrganization,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityOrganizationRoleClientResultsTypes.GetMultiple:
        """Retrieve organization's roles from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving organization's roles",
            logger=self._logger,
            fail_result_class=MaleoIdentityOrganizationRoleClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityOrganizationRoleClientParametersTransfers.GetMultipleFromOrganization,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityOrganizationRoleClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve organization's roles using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_organization_roles(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityOrganizationRoleClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityOrganizationRoleClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                if controller_result.content["data"] is None:
                    return (
                        MaleoIdentityOrganizationRoleClientResultsTransfers
                        .NoData
                        .model_validate(controller_result.content)
                    )
                else:
                    return (
                        MaleoIdentityOrganizationRoleClientResultsTransfers
                        .MultipleData
                        .model_validate(controller_result.content)
                    )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_organization_role(
        self,
        parameters:MaleoIdentityOrganizationRoleGeneralParametersTransfers.GetSingle,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityOrganizationRoleClientResultsTypes.GetSingle:
        """Retrieve organization's role from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving organization's role",
            logger=self._logger,
            fail_result_class=MaleoIdentityOrganizationRoleClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityOrganizationRoleGeneralParametersTransfers.GetSingle,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityOrganizationRoleClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve organization's role using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_organization_role(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityOrganizationRoleClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityOrganizationRoleClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                return (
                    MaleoIdentityOrganizationRoleClientResultsTransfers
                    .SingleData
                    .model_validate(controller_result.content)
                )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_organization_user_roles(
        self,
        parameters:MaleoIdentityUserOrganizationRoleClientParametersTransfers.GetMultipleFromUserOrOrganization,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityUserOrganizationRoleClientResultsTypes.GetMultiple:
        """Retrieve organization's user roles from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving organization's user roles",
            logger=self._logger,
            fail_result_class=MaleoIdentityUserOrganizationRoleClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityUserOrganizationRoleClientParametersTransfers.GetMultipleFromUserOrOrganization,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityUserOrganizationRoleClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve organization's user roles using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_organization_user_roles(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityUserOrganizationRoleClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityUserOrganizationRoleClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                if controller_result.content["data"] is None:
                    return (
                        MaleoIdentityUserOrganizationRoleClientResultsTransfers
                        .NoData
                        .model_validate(controller_result.content)
                    )
                else:
                    return (
                        MaleoIdentityUserOrganizationRoleClientResultsTransfers
                        .MultipleData
                        .model_validate(controller_result.content)
                    )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )

    async def get_organization_user_role(
        self,
        parameters:MaleoIdentityUserOrganizationRoleGeneralParametersTransfers.GetSingle,
        controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
        authorization:Optional[Authorization] = None,
        headers:Optional[Dict[str, str]] = None
    ) -> MaleoIdentityUserOrganizationRoleClientResultsTypes.GetSingle:
        """Retrieve organization's user role from MaleoIdentity"""
        @BaseExceptions.service_exception_handler(
            operation="retrieving organization's user role",
            logger=self._logger,
            fail_result_class=MaleoIdentityUserOrganizationRoleClientResultsTransfers.Fail
        )
        async def _impl(
            parameters:MaleoIdentityUserOrganizationRoleGeneralParametersTransfers.GetSingle,
            controller_type:MaleoIdentityGeneralEnums.ClientControllerType = MaleoIdentityGeneralEnums.ClientControllerType.HTTP,
            authorization:Optional[Authorization] = None,
            headers:Optional[Dict[str, str]] = None
        ):
            #* Validate chosen controller type
            if not isinstance(
                controller_type,
                MaleoIdentityGeneralEnums.ClientControllerType
            ):
                message = "Invalid controller type"
                description = "The provided controller type did not exists"
                return MaleoIdentityUserOrganizationRoleClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Retrieve organization's user role using chosen controller
            if controller_type == MaleoIdentityGeneralEnums.ClientControllerType.HTTP:
                controller_result = (
                    await self._controllers.http
                    .get_organization_user_role(
                        parameters=parameters,
                        authorization=authorization,
                        headers=headers
                    )
                )
            else:
                message = "Invalid controller type"
                description = "The provided controller type has not been implemented"
                return MaleoIdentityUserOrganizationRoleClientResultsTransfers.Fail(
                    message=message,
                    description=description
                )
            #* Return proper response
            if not controller_result.success:
                return (
                    MaleoIdentityUserOrganizationRoleClientResultsTransfers
                    .Fail
                    .model_validate(controller_result.content)
                )
            else:
                return (
                    MaleoIdentityUserOrganizationRoleClientResultsTransfers
                    .SingleData
                    .model_validate(controller_result.content)
                )
        return await _impl(
            parameters=parameters,
            controller_type=controller_type,
            authorization=authorization,
            headers=headers
        )