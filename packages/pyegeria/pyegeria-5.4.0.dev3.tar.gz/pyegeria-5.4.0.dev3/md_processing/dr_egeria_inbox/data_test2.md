# Create Term
## In Glossary
Coco Pharmaceuticals Clinical Trial Terminology
## Term Name
Hospital Identifier
## Description
Identifies each hospital uniquely. Used within the PatientId field.

___

#  Create Data Dictionary
## Name
Clinical Trial Data Dictionary

## Description
A data dictionary for clinical trial data elements.


#  Create Data Dictionary
## Name
Pharma Data Dictionary

## Description
A data dictionary of elements relevant to the Pharma communities.


___

# Create Data Spec

## Data Specification 

Data Specification for the Teddy Bear Drop Foot Clinical Trial

## Description
Principle data requirements for Teddy Bear Drop Foot Clinical Trial. Meow

## Qualified Name
DataSpec::Data Specification for the Teddy Bear Drop Foot Clinical Trial

## Classifications

## Guid


___


# Create Data Specification

## Data Specification Name 

Test Spec2

## Description
A test spec - Meow

## Qualified Name

## Classifications

## Guid

## Additional Properties
{
    "a prop" : "meow",
    "another" : "woof"
}
___

# Create Data Dictionary

## Dictionary Name 

dw

## Description
A data dictionary for dan..
## Qualified Name
DataDict::dw

## Classifications

## GUID


___


# Create Data Structure

## Data Structure Name 

TBDF-Incoming Weekly Measurement Data

## Description
This describes the weekly measurement data for each patient for the Teddy Bear drop foot clinical trial. 

## Qualified Name
DataStruct::TBDF-Incoming Weekly Measurement Data

## Namespace

## In Data Specification
Data Specification for the Teddy Bear Drop Foot Clinical Trial, Test Spec2

## Version Identifier


## Guid


___

# Create Data Structure

## Data Structure Name 

WWT-Incoming Weekly Measurement Data

## Description
A collection of data fields that form a data structure.

## Qualified Name
DataStruct::WWT-Incoming Weekly Measurement Data

## In Data Specification
Test Spec2

## Namespace


## Version Identifier


## GUID



___

# Create Data Field

## Data Field Name 

PatientId

## Description
Unique identifier of the patient

## Qualified Name
DataField::PatientId


## Data Type

String

## Guid

## Data Class

## In Data Dictionary
DataDict::Clinical Trial Data Dictionary, Pharma Data Dictionary

## In Data Structure
TBDF-Incoming Weekly Measurement Data
DataStruct::WWT-Incoming Weekly Measurement Data

## Glossary Term
GlossaryTerm::ClinicalTrialTerminology::PatientId
___



# Create Data Field

## Data Field Name

HospitalId

## Description
Unique identifier for a hospital. Used in forming PatientId.

## Qualified Name
DataField::HospitalId

## Data Type
String

## In Data Dictionary
DataDict::Clinical Trial Data Dictionary

## In Data Structure

DataStruct::TBDF-Incoming Weekly Measurement Data
DataStruct::WWT-Incoming Weekly Measurement Data

## Position
1

## Min Cardinality
0

## Max Cardinality
1

## Glossary Term
Term::Hospital Identifier

## Parent Data Field
DataField::PatientId

## Journal Entry
Just creating this term

___

# Create Data Field

## Data Field Name 

PatientSN

## Description
Unique identifier of the patient within a hospital.

## Qualified Name
DataField::PatientSN


## Data Type

String
## Position
2

## Min Cardinality
0

## Max Cardinality
1

## In Data Dictionary
DataDict::Clinical Trial Data Dictionary

## In Data Structure
DataStruct::TBDF-Incoming Weekly Measurement Data
DataStruct::WWT-Incoming Weekly Measurement Data

## Parent Data Field
DataField::PatientId

## Journal Entry
Just creating this term

___

# foo Create Data Class

## Data Class Name 

ISO-Date

## Description
ISO 8601 standard date. A date of the form YYYY-MM-DD

## Qualified Name
DataClass::ISO-Date

## Data Type
Date
## Position
0

## Min Cardinality
0

## Max Cardinality
1

## In Data Dictionary
DataDict::Clinical Trial Data Dictionary


## Containing Data Class

## Specializes Data Class

## Journal Entry
Just creating this date


___


# Update Data Field

## Data Field Name 

Date

## Description
A date of the form YYYY-MM-DD

## Qualified Name
DataField::Date


## Data Type
Date

## Position
0

## Min Cardinality
0

## Max Cardinality
1

## In Data Dictionary
DataDict::Clinical Trial Data Dictionary

## In Data Structure
TBDF-Incoming Weekly Measurement Data
DataStruct::WWT-Incoming Weekly Measurement Data

## Parent Data Field

## Data Class
DataClass::ISO-Date

## Journal Entry
Just creating this date


___



# foo Create Data Class

## Data Class Name 

Address

## Description
Address Class

## Qualified Name



## Data Type

String
## Position
0

## Min Cardinality
0

## Max Cardinality
1

## In Data Dictionary
DataDict::Clinical Trial Data Dictionary


## Containing Data Class

## Specializes Data Class

## Journal Entry
Just creating this date
