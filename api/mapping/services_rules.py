from data.models import Concept, ConceptRelationship

from mapping.models import ScanReportConcept
from mapping.serializers import ConceptSerializer


class NonStandardConceptMapsToSelf(Exception):
    pass

def get_concept_from_concept_code(concept_code,
                                  vocabulary_id,
                                  no_source_concept=False):
    """
    Given a concept_code and vocabularly id, 
    return the source_concept and concept objects

    If the concept is a standard concept, 
    source_concept will be the same object

    Parameters:
      concept_code (str) : the concept code  
      vocabulary_id (str) : SNOMED etc.
      no_source_concept (bool) : only return the concept
    Returns:
      tuple( source_concept(Concept), concept(Concept) )
      OR
      concept(Concept)
    """
    #obtain the source_concept given the code and vocab
    source_concept = Concept.objects.get(
        concept_code = concept_code,
        vocabulary_id = vocabulary_id
    )

    #if the source_concept is standard
    if source_concept.standard_concept == 'S':
        #the concept is the same as the source_concept
        concept = source_concept
    else:
        #otherwise we need to look up 
        concept = find_standard_concept(source_concept)

    if no_source_concept:
        #only return the concept
        return concept
    else:
        #return both as a tuple
        return (source_concept,concept)


def find_standard_concept(source_concept):
    """
    Parameters:
      - source_concept(Concept): originally found, potentially non-standard concept
    Returns:
      - Concept: either the same object as input (if input is standard), or a newly found 
    """

    #if is standard, return self
    if source_concept.standard_concept != 'S':
        return source_concept

    #find the concept relationship, of what this non-standard concept "Maps to"
    concept_relation = ConceptRelationship.objects.get(
        concept_id_1=source_concept.concept_id,
        relationship_id__contains='Maps to'
    )

    if concept_relation.concept_id_2 == concept_relation.concept_id_1:
        raise NonStandardConceptMapsToSelf('For a non-standard concept '
                                           'the concept_relation is mapping to itself '
                                           'i.e. it cannot find an associated standard concept')

    #look up the associated standard-concept
    concept = Concept.objects.get(
        concept_id=concept_relation.concept_id_2
    )
    return concept


class Concept2OMOP:

    @staticmethod
    def get_rules_by_scan_report_concept(scan_report_concept_id):

        print("scan_report_concept_id: {}".format(scan_report_concept_id))

        _scan_report_concept = ScanReportConcept.objects.get(pk=scan_report_concept_id)

        print("concept_id: {}".format(_scan_report_concept.concept.concept_id))

        _concept = Concept.objects.get(concept_id=_scan_report_concept.concept.concept_id)

        serializer = ConceptSerializer(_concept)

        concept = serializer.data

        if concept.get('domain_id') == 'Condition':
            """
            https://ohdsi.github.io/TheBookOfOhdsi/CommonDataModel.html#conditionOccurrence

            condition_occurrence_id: This is typically an autogenerated value creating a unique identifier for each record.
            person_id: This is a foreign key to Laura’s record in the PERSON table and links PERSON to CONDITION_OCCURRENCE.
            condition_concept_id: A foreign key referring to the SNOMED code 266599000: 194696.
            condition_start_date: The date when the instance of the Condition is recorded.
            condition_source_value: This is the original source value representing the Condition. In Lauren’s case of dysmenorrhea the SNOMED code for that Condition is stored here, while the Concept representing the code went to the CONDITION_SOURCE_CONCEPT_ID and the Standard Concept mapped from that is stored in the CONDITION_CONCEPT_ID field.
            condition_source_concept_id: If the condition value from the source is coded using a vocabulary that is recognized by OHDSI, the concept ID that represents that value would go here. In the example of dysmennorhea the source value is a SNOMED code so the Concept representing that code is 194696. In this case it has the same value as the CONDITION_CONCEPT_ID field.
            """
            pass

        return concept
