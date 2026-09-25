from typing import List, Tuple, Dict
from itertools import combinations

lysines = [
    'k05',
    'k08',
    'k12',
    'k16',
]


def get_ac_state(ac_lysines: List[str]) -> Tuple[str]:
    return tuple(sorted(ac_lysines))


def get_ac_reaction(reactant: Tuple[str], product: Tuple[str]) -> Tuple[Tuple[str], Tuple[str]]:
    return tuple([reactant, product])


def get_motif(ac_state: Tuple[str]) -> str:
    global lysines
    if len(ac_state) == 0:
        return '0ac'
    if len(ac_state) == len(lysines):
        return '4ac'
    return ''.join(ac_state)


def get_species_id(ac_state: Tuple[str]) -> str:
    return 'x_' + get_motif(ac_state)


def get_species_name(ac_state: Tuple[str]) -> str:
    return 'x_{' + get_motif(ac_state) + '}'


def get_parameter_id(reactant: Tuple[str], product: Tuple[str]) -> str:
    return 'a_' + get_motif(reactant) + '_' + get_motif(product)


def get_parameter_name(reactant: Tuple[str], product: Tuple[str]) -> str:
    return 'a_{' + get_motif(reactant) + '\\\\rightarrow ' + get_motif(product) + '}'


# def get_switch_parameter_id(reactant: Tuple[str], product: Tuple[str]) -> str:
#     return 'switch_' + get_motif(reactant) + '_' + get_motif(product)
# 
# 
# def get_switch_parameter_name(reactant: Tuple[str], product: Tuple[str]) -> str:
#     return 'switch_{' + get_motif(reactant) + '\\\\rightarrow ' + get_motif(product) + '}'


def get_acetylation_reaction_id(reactant: Tuple[str], product: Tuple[str]) -> str:
    return 'r_a_' + get_motif(reactant) + '_' + get_motif(product)


def get_acetylation_reaction_name(reactant: Tuple[str], product: Tuple[str]) -> str:
    return 'r^a_{' + get_motif(reactant) + '\\\\rightarrow ' + get_motif(product) + '}'


def get_deacetylation_reaction_id(reactant: Tuple[str], product: Tuple[str]) -> str:
    return 'r_da_' + get_motif(reactant) + '_' + get_motif(product)


def get_deacetylation_reaction_name(reactant: Tuple[str], product: Tuple[str]) -> str:
    return 'r^{da}_{' + get_motif(reactant) + '\\\\rightarrow ' + get_motif(product) + '}'


# Get species (acetylation states)
ac_states = []
for r in range(len(lysines) + 1):
    for ac_lysines in combinations(lysines, r=r):
        ac_states.append(get_ac_state(ac_lysines))

# Get reactions (stepwise transitions between acetylation states)
acetylation_reactions = []
deacetylation_reactions = []
for ac_state in ac_states:
    reactant = ac_state
    for lysine in lysines:
        if lysine in ac_state:
            product = get_ac_state([ac_lysine for ac_lysine in ac_state if ac_lysine != lysine])
            deacetylation_reactions.append(get_ac_reaction(reactant, product))
        else:
            product = get_ac_state(list(ac_state) + [lysine])
            acetylation_reactions.append(get_ac_reaction(reactant, product))


all_species_dict = {
    ac_state: {
        'id': get_species_id(ac_state),
        'name': get_species_name(ac_state),
        'initialConcentration': 1 if not ac_state else 0,
    }
    for ac_state in ac_states
}


acetylation_reactions_dict = {
    reaction: {
        'id': get_acetylation_reaction_id(*reaction),
        'name': get_acetylation_reaction_name(*reaction),
        'reactant_id': get_species_id(reaction[0]),
        'product_id': get_species_id(reaction[1]),
        # 'formula': f'{get_parameter_id(*reaction)} * {get_species_id(reaction[0])} + {get_switch_parameter_id(*reaction)} * a_b',
        'formula': f'{get_parameter_id(*reaction)} * a_b * {get_species_id(reaction[0])}'
    }
    for reaction in acetylation_reactions
}

deacetylation_reactions_dict = {
    reaction: {
        'id': get_deacetylation_reaction_id(*reaction),
        'name': get_deacetylation_reaction_name(*reaction),
        'reactant_id': get_species_id(reaction[0]),
        'product_id': get_species_id(reaction[1]),
        'formula': f'da_b * {get_species_id(reaction[0])}',
    }
    for reaction in deacetylation_reactions
}


reactions_dict = {**acetylation_reactions_dict, **deacetylation_reactions_dict}

common_parameters = {
    # Basal acetylation rate
    'a_b': {
        'id': 'a_b',
        'name': 'a_b',
        'value': 0,
    },
    # Global deacetylation rate
    'da_b': {
        'id': 'da_b',
        'name': 'da_b',
        'value': 1,
    },
}

motif_specific_parameters = {
    get_parameter_id(*reaction): {
        'id': get_parameter_id(*reaction),
        'name': get_parameter_name(*reaction),
        'value': 0,
    }
    for reaction in acetylation_reactions
}

# switch_parameters = {
#     get_switch_parameter_id(*reaction): {
#         'id': get_switch_parameter_id(*reaction),
#         'name': get_switch_parameter_name(*reaction),
#         'value': 0,
#     }
#     for reaction in acetylation_reactions
# }

# parameters_dict = {**common_parameters, **motif_specific_parameters, **switch_parameters}
parameters_dict = {**common_parameters, **motif_specific_parameters}
