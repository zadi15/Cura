# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Logger import Logger

from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry

from .GlobalStack import GlobalStack
from .ExtruderStack import ExtruderStack
from .CuraContainerStack import CuraContainerStack

##  Contains helper functions to create new machines.
class CuraStackBuilder:
    ##  Create a new instance of a machine.
    #
    #   \param name The name of the new machine.
    #   \param definition_id The ID of the machine definition to use.
    #
    #   \return The new global stack or None if an error occurred.
    @classmethod
    def createMachine(cls, name: str, definition_id: str) -> GlobalStack:
        cls.__registry = ContainerRegistry.getInstance()
        definitions = cls.__registry.findDefinitionContainers(id = definition_id)
        if not definitions:
            Logger.log("w", "Definition {definition} was not found!", definition = definition_id)
            return None

        machine_definition = definitions[0]
        name = cls.__registry.createUniqueName("machine", "", name, machine_definition.name)

        new_global_stack = cls.createGlobalStack(
            new_stack_id = name,
            definition = machine_definition,
            quality = "default",
            material = "default",
            variant = "default",
        )

        for extruder_definition in cls.__registry.findDefinitionContainers(machine = machine_definition.id):
            position = extruder_definition.getMetaDataEntry("position", None)
            if not position:
                Logger.log("w", "Extruder definition %s specifies no position metadata entry.", extruder_definition.id)

            new_extruder_id = cls.__registry.uniqueName(extruder_definition.id)
            new_extruder = cls.createExtruderStack(
                new_extruder_id = new_extruder_id,
                definition = extruder_definition,
                machine_definition = machine_definition,
                quality = "default",
                material = "default",
                variant = "default",
                next_stack = new_global_stack
            )

        return new_global_stack

    ##  Create a new Extruder stack
    #
    #   \param new_stack_id The ID of the new stack.
    #   \param definition The definition to base the new stack on.
    #   \param machine_definition The machine definition to use for the user container.
    #   \param kwargs You can add keyword arguments to specify IDs of containers to use for a specific type, for example "variant": "0.4mm"
    #
    #   \return A new Global stack instance with the specified parameters.
    @classmethod
    def createExtruderStack(cls, new_stack_id: str, definition: DefinitionContainer, machine_definition: DefinitionContainer, **kwargs) -> ExtruderStack:
        cls.__registry = ContainerRegistry.getInstance()

        stack = ExtruderStack(new_stack_id)
        stack.setDefinition(definition)
        stack.addMetaDataEntry("position", definition.getMetaDataEntry("position"))

        user_container = InstanceContainer(new_stack_id + "_user")
        user_container.addMetaDataEntry("type", "user")
        user_container.addMetaDataEntry("extruder", new_stack_id)

        stack.setUserChanges(user_container)

        if "next_stack" in kwargs:
            stack.setNextStack(kwargs["next_stack"])

        # Important! The order here matters, because that allows functions like __setStackQuality to
        # assume the material and variant have already been set.
        if "definition_changes" in kwargs:
            stack.setDefinitionChangesById(kwargs["definition_changes"])

        if "variant" in kwargs:
            cls.__setStackVariant(stack, kwargs["variant"])

        if "material" in kwargs:
            cls.__setStackMaterial(stack, kwargs["material"])

        if "quality" in kwargs:
            cls.__setStackQuality(stack, kwargs["quality"])

        if "quality_changes" in kwargs:
            stack.setQualityChangesById(kwargs["quality_changes"])

        # Only add the created containers to the registry after we have set all the other
        # properties. This makes the create operation more transactional, since any problems
        # setting properties will not result in incomplete containers being added.
        cls.__registry.addContainer(stack)
        cls.__registry.addContainer(user_container)

        return stack

    ##  Create a new Global stack
    #
    #   \param new_stack_id The ID of the new stack.
    #   \param definition The definition to base the new stack on.
    #   \param kwargs You can add keyword arguments to specify IDs of containers to use for a specific type, for example "variant": "0.4mm"
    #
    #   \return A new Global stack instance with the specified parameters.
    @classmethod
    def createGlobalStack(cls, new_stack_id: str, definition: DefinitionContainer, **kwargs) -> GlobalStack:
        cls.__registry = ContainerRegistry.getInstance()

        stack = GlobalStack(new_stack_id)
        stack.setDefinition(definition)

        user_container = InstanceContainer(new_stack_id + "_user")
        user_container.addMetaDataEntry("type", "user")
        user_container.addMetaDataEntry("machine", new_stack_id)
        user_container.setDefinition(definition)

        stack.setUserChanges(user_container)

        # Important! The order here matters, because that allows functions like __setStackQuality to
        # assume the material and variant have already been set.
        if "definition_changes" in kwargs:
            stack.setDefinitionChangesById(kwargs["definition_changes"])

        if "variant" in kwargs:
            cls.__setStackVariant(stack, kwargs["variant"])

        if "material" in kwargs:
            cls.__setStackMaterial(stack, kwargs["material"])

        if "quality" in kwargs:
            cls.__setStackQuality(stack, kwargs["quality"])

        if "quality_changes" in kwargs:
            stack.setQualityChangesById(kwargs["quality_changes"])

        cls.__registry.addContainer(stack)
        cls.__registry.addContainer(user_container)

        return stack
