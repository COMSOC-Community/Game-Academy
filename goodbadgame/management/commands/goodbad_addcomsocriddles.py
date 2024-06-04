from django.core.management.base import BaseCommand

from goodbadgame.models import *


def add_riddle_question(slug_prefix, title, question_text, alts_text):
    alt_objs = []
    for alt_index, alt_text in enumerate(alts_text):
        alt, _ = Alternative.objects.update_or_create(
            slug=slug_prefix + '_alt' + str(alt_index + 1),
            defaults={
                'text': alt_text,
                'image': ''
            }
        )
        alt_objs.append(alt)

    # Convention is that first in alt_dicts is the correct one
    question, _ = Question.objects.update_or_create(
        slug=slug_prefix,
        defaults={
            'text': question_text,
            'title': title,
            'correct_alt': alt_objs[0]
        }
    )
    question.alternatives.clear()
    for alt in alt_objs:
        question.alternatives.add(alt)
    question.save()


class Command(BaseCommand):
    help = 'Add the questions to database'

    def handle(self, *args, **options):
        add_riddle_question('GaleShapley', 'COMSOC Riddle 1', 'What type of marriage are Gale and Shapley aiming for?',
                            ['stable', 'happy', 'long', 'successful', 'romantic'])
        add_riddle_question('VonNeumannMorgenstern', 'COMSOC Riddle 2',
                            'Complete the sentence: To satisfy the von Neumann--Morgenstern axioms, you must maximise '
                            'expected ________.',
                            ['utility', 'welfare', 'optimality', 'outcomes'])
        add_riddle_question('TransitivityPairwiseMajority', 'COMSOC Riddle 3',
                            'Consider the three-voter preference profile with x >₁ y >₁ z and y >₂ z >₂ x and z >₃ x '
                            '>₃ y. The main problem with this profile is that ...',
                            ['its pairwise majority relation is not transitive', 'it is single-peaked',
                             "it is a counterexample to Arrow's Impossibility Theorem",
                             'its construction requires the axiom of choice'])
        add_riddle_question('NumberLinearOrders', 'COMSOC Riddle 4',
                            'How many ways are there to rank 4 alternatives in a linear order?', ['24', '4', '6', '16'])
        add_riddle_question('ApprovalVoting', 'COMSOC Riddle 5',
                            'Under approval voting, what is the winning alternative for the profile ({1, 2, 3}, {2}, '
                            '{2, 3}, {1, 4}, {5, 6, 7, 8})?',
                            ['2', '1', '3', '4', '5'])
        add_riddle_question('HedonicGame', 'COMSOC Riddle 6',
                            'Complete the sentence: A hedonic game is a type of ________ formation game.',
                            ['coalition', 'committee', 'preference', 'strategic'])
        add_riddle_question('Borda', 'COMSOC Riddle 7',
                            'What is the name of the 1700s French innovator whose voting rule was intended only for '
                            '"honest men"?',
                            ['Borda', 'Condorcet', 'Laplace', 'Arrow'])
        add_riddle_question('NumberHouseAssignments', 'COMSOC Riddle 8',
                            'How many ways are there to assign three houses to three agents, so that each agent '
                            'receives exactly one house?',
                            ['6', '3', '8', '9'])
        add_riddle_question('CharacterisationMajority', 'COMSOC Riddle 9',
                            'Who characterised the majority rule as the only voting rule that satisfies anonymity, '
                            'neutrality, and a particular monotonicity axiom?',
                            ['May', 'Arrow', 'Black', 'Condorcet'])
        add_riddle_question('ParisCOMSOCHub', 'COMSOC Riddle 10',
                            'Complete the sentence: There are more people working on computational social choice '
                            'living in ________ than in any other city in the world.',
                            ['Paris', 'Amsterdam', 'Beijing', 'London', 'New York'])
        add_riddle_question('AcronymsCOMSOC', 'COMSOC Riddle 11',
                            'Which acronym is not commonly found in papers on computational social choice?',
                            ['ZFC', 'EFX', 'IIA', 'PAV', 'SCF'])
        add_riddle_question('PotentialFunction', 'COMSOC Riddle 12',
                            'Complete the sentence: To prove that a dynamic process converges, a useful proof '
                            'technique is a ________ function argument, where a bounded function is shown to increase '
                            'with every iteration.',
                            ['potential', 'welfare', 'alternating', 'real-valued'])
        add_riddle_question('EnvyFreeness', 'COMSOC Riddle 13', 'Which of these is a fairness notion?',
                            ['EF1', 'APX', 'PSPACE', 'CMT', 'AAAI'])
        add_riddle_question('Stratergyproofness', 'COMSOC Riddle 14',
                            'Complete the sentence: A voting rule is called ________ if a voter cannot obtain a '
                            'better outcome by reporting false preferences.',
                            ['strategyproof', 'fair', 'optimal', 'impossible'])
        add_riddle_question('Impossibility', 'COMSOC Riddle 15',
                            'How many different voting rules are resolute, onto, strategyproof, and non-dictatorial '
                            'when there are 5 alternatives and 7 voters?',
                            ['0', '1', '7', '120'])
        add_riddle_question('AustraliaRule', 'COMSOC Riddle 16',
                            'Which country uses instant runoff voting to elect members of a national parliament?',
                            ['Australia', 'Germany', 'Israel', 'Netherlands', 'USA'])
        add_riddle_question('ShapleyValue', 'COMSOC Riddle 17',
                            'Suppose you have a transferable-utility game and impose additivity, symmetry, dummy, '
                            'and efficiency on a real-valued function on the set of players. What do you get?',
                            ['Shapley value', 'Nash equilibrium', 'Condorcet winner', 'Borda rule'])
        add_riddle_question('ProportionalityFairDivision', 'COMSOC Riddle 18',
                            'Complete the sentence: In fair division, an allocation is said to be ________ if each '
                            'agent gets utility at least 1/n times the utility of all available resources.',
                            ['proportional', 'fair', 'envy-free'])
        add_riddle_question('NashBargain', 'COMSOC Riddle 19',
                            'What is the name of the inventor of the bargaining solution that involves multiplying '
                            'utilities?',
                            ['John Nash', 'Jeremy Bentham', 'John Stuart Mill', 'Armartya Sen'])
        add_riddle_question('LiquidDemocracy', 'COMSOC Riddle 20',
                            'Complete the sentence: In ________ democracy, voters may delegate their vote.',
                            ['liquid', 'representative', 'direct', 'perfect'])
        add_riddle_question('AdditiveValuations', 'COMSOC Riddle 21',
                            'Which of these is a false statement about additive valuations?',
                            ['they allow voters to express substitutes and complements',
                             'they can be concisely represented',
                             'they allow voters to be indifferent between all bundles',
                             'they are both submodular and supermodular', 'they make research easier'])
        add_riddle_question('VetoRule', 'COMSOC Riddle 22',
                            'Completes the sentence: In voting theory, the antiplurality rule is also known as the '
                            '________ rule.',
                            ['veto', 'inverse', 'minority', 'scoring'])
        add_riddle_question('OptimumDistortion', 'COMSOC Riddle 23',
                            'Complete the sentence: In the study of distortion, an omniscient mechanism with access '
                            'to all information achieves distortion __.',
                            ['1', '0', 'infinite'])
        add_riddle_question('StableMatching', 'COMSOC Riddle 24',
                            'Complete the sentence: A matching is ________ if there is no pair of agents each of whom '
                            'prefers the other to their partner in the matching.',
                            ['stable', 'efficient', 'strategyproof', 'perfect'])
        add_riddle_question('Profile', 'COMSOC Riddle 25',
                            'Complete the sentence: A vector of preferences, one for each voter, is also known as a '
                            'preference ________.',
                            ['profile', 'order', 'ranking', 'rule', 'set'])
        add_riddle_question('CaenSocietyForSCW', 'COMSOC Riddle 26',
                            'What is the name of the town housing the offices of the Society for Social Choice and '
                            'Welfare?',
                            ['Caen', 'Cannes', 'Canterbury', 'Coventry'])
