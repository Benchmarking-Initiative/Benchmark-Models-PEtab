import libsbml

from model_info import (
    all_species_dict,
    reactions_dict,
    parameters_dict,
)


# Create model
sbml_document = libsbml.SBMLDocument(3, 2)
sbml_model = sbml_document.createModel()
sbml_model.setId('Blasi_CellSystems2016__select_motif_specific')
sbml_model.setName('Blasi_CellSystems2016__select_motif_specific')

# Add compartment
compartment_id = 'compartment'
compartment = sbml_model.createCompartment()
compartment.setId(compartment_id)
compartment.setName(compartment_id)
compartment.setSize(1)
compartment.setConstant(True)

# Add species
for species_dict in all_species_dict.values():
    species = sbml_model.createSpecies()
    species.setId(species_dict['id'])
    species.setName(species_dict['name'])
    species.setInitialConcentration(species_dict['initialConcentration'])
    species.setCompartment(compartment_id)
    species.setConstant(False)
    species.setBoundaryCondition(False)
    species.setHasOnlySubstanceUnits(False)

# Add parameters
for parameter_dict in parameters_dict.values():
    parameter = sbml_model.createParameter()
    parameter.setId(parameter_dict['id'])
    parameter.setName(parameter_dict['name'])
    parameter.setValue(parameter_dict['value'])
    parameter.setConstant(True)

# Add reactions
for reaction_dict in reactions_dict.values():
    # Create reaction
    reaction = sbml_model.createReaction()
    reaction.setId(reaction_dict['id'])
    reaction.setName(reaction_dict['name'])
    reaction.setReversible(False)

    # Add reactant
    reactant = reaction.createReactant()
    reactant.setSpecies(reaction_dict['reactant_id'])
    reactant.setConstant(True)

    # Add product
    product = reaction.createProduct()
    product.setSpecies(reaction_dict['product_id'])
    product.setConstant(True)

    # Add kinetic
    math_ast = libsbml.parseL3Formula(reaction_dict['formula'])
    kinetic_law = reaction.createKineticLaw()
    kinetic_law.setMath(math_ast)

libsbml.writeSBMLToFile(sbml_document, 'output/model/model.xml')
