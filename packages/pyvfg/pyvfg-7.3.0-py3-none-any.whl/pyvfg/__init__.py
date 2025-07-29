# -*- coding: utf-8 -*-
from .errors import (
    ValidationError as ValidationError,
    ModelTypeError as ModelTypeError,
    JsonSerializationError as JsonSerializationError,
    ValidationErrors as ValidationErrors,
    MissingDistribution as MissingDistribution,
    MultipleDistributions as MultipleDistributions,
    CyclicGraph as CyclicGraph,
    MultivariateDistributionNotConditional as MultivariateDistributionNotConditional,
    InvalidFactorRole as InvalidFactorRole,
    MissingFactors as MissingFactors,
    InvalidVariableName as InvalidVariableName,
    InvalidVariableItemCount as InvalidVariableItemCount,
    MissingVariable as MissingVariable,
    MissingProbability as MissingProbability,
    VariableMissingInVariableList as VariableMissingInVariableList,
    IncorrectTensorShape as IncorrectTensorShape,
    DuplicateVariablesError as DuplicateVariablesError,
    DuplicateElementsError as DuplicateElementsError,
    NormalizationError as NormalizationError,
    MissingTransition as MissingTransition,
    StateVarMissingLikelihood as StateVarMissingLikelihood,
    ObsVarMissingLikelihood as ObsVarMissingLikelihood,
    VariableRoleIndeterminate as VariableRoleIndeterminate,
    NoTransitionFactors as NoTransitionFactors,
    NoLikelihoodFactors as NoLikelihoodFactors,
    NonPotentialInMRF as NonPotentialInMRF,
    NegativePotentialError as NegativePotentialError,
)
from .versions.vfg_0_5_0 import (
    VFG as VFG,
    BayesianNetwork as BayesianNetwork,
    MarkovRandomField as MarkovRandomField,
    POMDP as POMDP,
    Factor as Factor,
    FactorRole as FactorRole,
    Variable as Variable,
    VariableRole as VariableRole,
    ModelType as ModelType,
    Distribution as Distribution,
    Smoothing as Smoothing,
    NumPreviousObservations as NumPreviousObservations,
    FactorInitialization as FactorInitialization,
    Metadata as Metadata,
    InitializationStrategy as InitializationStrategy,
    DiscreteVariableNamedElements as DiscreteVariableNamedElements,
    DiscreteVariableAnonymousElements as DiscreteVariableAnonymousElements,
    GenerateJsonSchemaIgnoreInvalid as GenerateJsonSchemaIgnoreInvalid,
)
from .versions.vfg_0_5_0_utils import (
    vfg_from_dict as vfg_from_dict,
    vfg_from_json as vfg_from_json,
    vfg_to_json as vfg_to_json,
    vfg_to_json_schema as vfg_to_json_schema,
    vfg_upgrade as vfg_upgrade,
)


# by request
@property
def __version__() -> str:
    import importlib.metadata

    return importlib.metadata.version("pyvfg")


# for compatibility
VFGPydanticType = VFG
validate_graph = VFG.validate
