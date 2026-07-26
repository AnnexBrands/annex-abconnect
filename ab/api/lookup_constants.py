"""Master-constant lookup values as enums (GENERATED — do not edit by hand).

Each enum mirrors one ``GET /lookup/{masterConstantKey}`` group: members map a
value's display name to its id (a GUID, or an int for ContactTypes). Use these
instead of pasting GUIDs, e.g.::

    api.jobs.save_feedback(job_id, CancelledTypes.NO_LONGER_NEEDS_OUR_SERVICE, cancel_job=True)

Regenerate from the committed fixtures with::

    python -m scripts.capture_lookups            # offline, from tests/fixtures/lookups/
    python -m scripts.capture_lookups --capture  # refresh fixtures from the live API first
"""

# ruff: noqa: E501  (generated data table — value labels kept inline as comments)

from __future__ import annotations

from enum import Enum

from ab.api.models.enums import MasterConstantKey


class BasisTypes(str, Enum):
    """BasisTypes — GET /lookup/BasisTypes (MasterConstantKey.BASIS_TYPES)."""

    LOCAL = 'aa1dadff-6009-40cd-8e08-9a731ab3895b'  # Local
    C3 = '832bc395-c900-4082-8c14-9adf032960aa'  # C3
    LAST = '98f141d0-bfb3-48ce-a48a-ca45db3ec8b6'  # Last
    T1 = '89f17afd-b0d9-458b-a590-e62888c7c41f'  # T1
    INF = '54449c04-7153-ea11-822b-fcb1a6dfbbb6'  # INF
    INP = '55449c04-7153-ea11-822b-fcb1a6dfbbb6'  # INP
    IND = '51db900b-7153-ea11-822b-fcb1a6dfbbb6'  # IND
    ONF = '372a2c14-7153-ea11-822b-fcb1a6dfbbb6'  # ONF
    OND = 'c670981c-7153-ea11-822b-fcb1a6dfbbb6'  # OND
    ONP = 'c770981c-7153-ea11-822b-fcb1a6dfbbb6'  # ONP
    T2 = '8597402c-534f-4e74-b2f8-f3fb10637990'  # T2
    C2 = '639ca20d-6696-48fd-a70e-0de8769f235c'  # C2
    C1 = '73214435-c98b-42e8-88c7-5b71ab1251f9'  # C1
    T3 = '70cfc6ed-8d86-443d-bd41-3e7e2be5a0a6'  # T3


class CancelledTypes(str, Enum):
    """CancelledTypes — GET /lookup/CancelledTypes (MasterConstantKey.CANCELLED_TYPES)."""

    FRAUD = '414f1c2a-e8c4-e711-8f3f-00155d426802'  # Fraud
    NO_LONGER_NEEDS_OUR_SERVICE = '8276cb83-28e0-e711-8f3f-00155d426802'  # No longer needs our service
    INSUFFICIENT_DETAILS_CANNOT_REACH_CUSTOMER = 'af307e3c-00e1-e711-8f3f-00155d426802'  # Insufficient details, cannot reach customer
    DUPLICATE = 'f636c012-e965-e311-b6f8-000c298b59ee'  # Duplicate
    TRAINING = 'a436431c-e965-e311-b6f8-000c298b59ee'  # Training
    QUOTED_NO_RESPONSE = 'a7340432-53f9-e611-9f52-00155d426802'  # Quoted - No Response
    WE_DIDNT_ANSWER = '86b6e109-56f9-e611-9f52-00155d426802'  # We didn't answer
    REFERRED_TO_RETAIL = 'bf1062d4-3a2f-e611-ba2b-00155d426802'  # Referred to Retail
    PRICE = '590aada9-2d08-4003-b8d2-65c389a62547'  # Price
    SPAM = 'e9450e12-9dd5-e911-822b-fcb1a6dfbbb6'  # Spam
    A_HOT_LEAD = 'cee0b0a3-4dff-e911-822b-fcb1a6dfbbb6'  # A - Hot Lead
    B_PROSPECT = 'cfe0b0a3-4dff-e911-822b-fcb1a6dfbbb6'  # B - Prospect
    C_UNQUALIFIED = '3bd90bad-4dff-e911-822b-fcb1a6dfbbb6'  # C - Unqualified
    OUTSIDE_OF_OUR_COVERAGE = 'afdd87db-f16e-4120-84c0-868caee5208e'  # Outside of our coverage
    LOST_TO_COMPETITION = 'ecbe9cdd-429c-48f4-8b34-8a0b04d076d5'  # Lost to Competition


class CFillType(str, Enum):
    """CFillType — GET /lookup/CFillType (MasterConstantKey.C_FILL_TYPE)."""

    FIP = 'dd374cdd-d8e4-416b-a617-aa65ba0a7087'  # FIP
    HON = '7c1443ab-3b96-4843-af31-e69d342b82ab'  # HON
    ESP = 'd4109f70-c8e8-4962-ace2-e41b3cba510c'  # ESP
    RAN = '105838b1-6ff3-47f2-aeb9-7a06816f56ac'  # RAN
    SPF = '2fb2d7bc-8089-4a0f-b86b-4c041ed44c18'  # SPF
    LOO = 'f0971a11-0d91-4f14-8b41-12299096f811'  # LOO


class CommodityCategory(str, Enum):
    """CommodityCategory — GET /lookup/CommodityCategory (MasterConstantKey.COMMODITY_CATEGORY)."""

    AUTOMOTIVE = 'c5406e17-1f59-ec11-822e-a4aa13c701a3'  # Automotive
    INDUSTRIAL_MANUFACTURING = '4068dea2-1a07-ec11-89e2-001a7dda710b'  # Industrial/Manufacturing
    MEDICAL = '4168dea2-1a07-ec11-89e2-001a7dda710b'  # Medical
    TECHNOLOGY = '4268dea2-1a07-ec11-89e2-001a7dda710b'  # Technology
    STAGING_DISPLAY_EVENTS = '4368dea2-1a07-ec11-89e2-001a7dda710b'  # Staging/Display/Events
    RETAIL_MERCHANDISE = '4468dea2-1a07-ec11-89e2-001a7dda710b'  # Retail/Merchandise
    ART_SCULPTURES = '4568dea2-1a07-ec11-89e2-001a7dda710b'  # Art & Sculptures
    ANTIQUES_COLLECTIBLES = '4668dea2-1a07-ec11-89e2-001a7dda710b'  # Antiques & Collectibles
    FURNITURE_DESIGN = '4768dea2-1a07-ec11-89e2-001a7dda710b'  # Furniture & Design
    RESIDENTIAL_MOVE = '4868dea2-1a07-ec11-89e2-001a7dda710b'  # Residential Move
    OFFICE_MOVE = '4968dea2-1a07-ec11-89e2-001a7dda710b'  # Office Move
    ESTATE_DISTRIBUTION = '4a68dea2-1a07-ec11-89e2-001a7dda710b'  # Estate Distribution
    OTHER = '4b68dea2-1a07-ec11-89e2-001a7dda710b'  # Other


class CompanyTypes(str, Enum):
    """CompanyTypes — GET /lookup/CompanyTypes (MasterConstantKey.COMPANY_TYPES)."""

    CORPORATE = '8ec06e36-7e6a-4ed6-a27c-7cc0c13a7292'  # Corporate
    CARRIER = '88a541e1-456e-4e6e-b445-af75311b694f'  # Carrier
    VENDOR = '4176c2d7-b7ae-ec11-822e-a4aa13c701a3'  # Vendor
    FRANCHISEE = 'e7f85166-34cf-429b-805d-261b44cb0c04'  # Franchisee
    CUSTOMER = '8e809044-8d69-4618-9533-265d7e71db13'  # Customer
    AGENT = '697cc861-d271-4baf-8cbb-2eb055a1005a'  # Agent
    TERMINAL = '65d232c9-3031-4682-83b5-594da868d9dd'  # Terminal
    NATIONAL_ACCOUNT = '27654fb3-9507-e811-8f3f-00155d426802'  # National Account


class ContactTypes(int, Enum):
    """ContactTypes — GET /lookup/ContactTypes (MasterConstantKey.CONTACT_TYPES)."""

    CARRIER = 1  # Carrier
    CUSTOMERS = 2  # Customers
    EMPLOYEE = 3  # Employee
    FRANCHISEE = 4  # Franchisee
    INDUSTRY = 5  # Industry
    VENDOR = 6  # Vendor


class ContainerType(str, Enum):
    """ContainerType — GET /lookup/ContainerType (MasterConstantKey.CONTAINER_TYPE)."""

    DR = 'd2e349e5-df74-4229-81ce-2723516664f9'  # DR
    CO = 'a017245a-bed8-46d8-adea-36629a3f9e2f'  # CO
    D = 'b45b52c8-f263-4f71-8c3a-455e0e085931'  # D
    SB = '4e636f78-e1b4-46c7-92f6-cfe18de0f1f9'  # SB
    SC = 'df5dd632-1fd7-4e57-afac-af4d8b53b289'  # SC
    FAC = 'f3942062-4712-4935-8d7e-93b05a5476fd'  # FAC


class CPackType(str, Enum):
    """CPackType — GET /lookup/CPackType (MasterConstantKey.C_PACK_TYPE)."""

    N_3 = 'c0648365-2962-4b0d-a8d5-68fefc06c1c6'  # 3
    N_4 = '31ae52cc-7d0f-41e9-b4d9-a15865de0217'  # 4
    N_1 = '16bd6885-6356-4242-b4c0-e32f4b22e563'  # 1
    N_2 = '463f245d-0dba-406b-9439-f3486e387ec2'  # 2
    PBO = 'a8506744-85db-4e08-b564-e7fb68fb1eb7'  # PBO


class DocumentTags(str, Enum):
    """DocumentTags — GET /lookup/DocumentTags (MasterConstantKey.DOCUMENT_TAGS)."""

    PICKUP = '48c9cf0b-49ab-ee11-ac1c-0a15ce13c9bf'  # Pickup
    PACK_PROGRESS = 'e8249926-49ab-ee11-ac1c-0a15ce13c9bf'  # Pack Progress
    INTAKE = '6a8c801b-8644-ef11-ac1c-0a15ce13c9bf'  # Intake
    DAMAGE = 'e2d725f1-1ed8-4019-b893-0cecac3d7621'  # Damage
    ITEMS = 'd467ba5e-ca04-45e6-8a3e-5082ec565396'  # Items
    PACKED_FINAL = 'b6e90f3f-d235-4884-b234-14475f133815'  # Packed / Final
    TRANSPORTATION = '00cbe4ce-82c1-4244-88c6-dd285eec2573'  # Transportation
    CUSTOMER_PROVIDED = '90cf4b11-99d2-47d4-ac03-c40365a5807e'  # Customer Provided
    CONDITION = '73be4eb4-c559-45ac-a162-c7346bd0cb55'  # Condition
    SUPPORTING_DOCUMENTS = 'b4c472e4-cec1-4de0-a8fb-966a27b2f4fd'  # Supporting Documents


class FollowupHeatOption(str, Enum):
    """FollowupHeatOption — GET /lookup/FollowupHeatOption (MasterConstantKey.FOLLOWUP_HEAT_OPTION)."""

    A = 'a91ec87e-b817-e811-8f3f-00155d426802'  # A
    B = 'aa1ec87e-b817-e811-8f3f-00155d426802'  # B
    C = 'ab1ec87e-b817-e811-8f3f-00155d426802'  # C
    D = 'ac1ec87e-b817-e811-8f3f-00155d426802'  # D
    E = 'ad1ec87e-b817-e811-8f3f-00155d426802'  # E


class FollowupPipelineOption(str, Enum):
    """FollowupPipelineOption — GET /lookup/FollowupPipelineOption (MasterConstantKey.FOLLOWUP_PIPELINE_OPTION)."""

    E_MAIL = 'a71ec87e-b817-e811-8f3f-00155d426802'  # E-mail
    PHONE = 'a81ec87e-b817-e811-8f3f-00155d426802'  # Phone


class FranchiseeTypes(str, Enum):
    """FranchiseeTypes — GET /lookup/FranchiseeTypes (MasterConstantKey.FRANCHISEE_TYPES)."""

    NEW = '260f47f0-d1bf-4299-8747-edcce63f2156'  # New
    PROBATIONARY = '7cbd2962-23eb-48d1-a3ef-d2b174279af6'  # Probationary
    MATURE = '50f7d54f-7023-4697-a187-8bcda433bad2'  # Mature


class FreightClass(str, Enum):
    """FreightClass — GET /lookup/FreightClass (MasterConstantKey.FREIGHT_CLASS)."""

    N_77 = 'daa9b28b-fe52-4196-9540-0a7252442b32'  # 77
    N_110 = '4368d21f-d4c3-418c-9bd4-0da6616e9b3b'  # 110
    N_125 = '72f1b12f-951b-4532-912c-0db48d89a2cb'  # 125
    N_150 = '166edbf1-4c97-444d-bf21-0eee49329bd0'  # 150
    N_85 = '540951ca-f25c-4124-b464-0bb49e2d96d3'  # 85
    N_92_5 = '4e9c0533-f1fe-42ca-b802-0c7f50c3fc5e'  # 92.5
    N_100 = '43deade7-e605-47c6-915d-0cdd6d759b29'  # 100
    N_175 = 'bbacc794-98e5-4895-b75b-100656f1cfcb'  # 175
    N_200 = 'd43667b2-9b1e-4a45-8998-102f1bc17c31'  # 200
    N_50 = '4ad296ed-7671-46f4-bcfb-063ff4215cfc'  # 50
    N_65 = 'a0b8197c-1531-46c6-8596-04a53785571b'  # 65
    N_60 = 'b5387f34-fabe-43de-a191-0319041e4b00'  # 60
    N_55 = 'f4523e84-307e-e111-b526-00155d6b2c30'  # 55
    N_70 = 'ac891fb5-d7d1-4a9e-8aa7-1f11d84133b2'  # 70
    N_500 = '4dfb8548-c72e-4f2d-8bee-1dfbf3996f28'  # 500
    N_250 = 'fcb66f9d-e11c-4327-9528-14b3dddd5955'  # 250
    N_300 = '35b304e6-f8d1-449a-b544-15e5331dab72'  # 300
    N_400 = '32b556f4-80b2-41ac-8843-17837fb9c94a'  # 400


class FreightTypes(str, Enum):
    """FreightTypes — GET /lookup/FreightTypes (MasterConstantKey.FREIGHT_TYPES)."""

    DRUMS = '2928495e-d380-43e3-b7c1-111cd66c6e96'  # DRUMS
    BAGS = 'f21ae924-6d4d-48b6-9b8f-3d6138bd6b3f'  # BAGS
    PALLETS = 'af79fcd4-e493-4931-9dbf-729a15e8fdc4'  # PALLETS
    CARPETS = 'c6e6af49-3553-46ec-a3c6-e0f956a2d0f7'  # CARPETS
    BOXES = '49285672-2337-447c-b177-e38ad20b4dbe'  # BOXES
    PAILS = 'e4249214-9946-45d6-a5f2-d368d4eb892b'  # PAILS
    CYLINDERS = 'db78bde6-739d-40ee-be1b-bfd617967d0d'  # CYLINDERS
    CARTONS = '7085ad09-d716-4e65-8503-c1490ad80863'  # CARTONS
    ROLLS = 'd3ce54d2-cb34-408c-a01e-b9d936921a40'  # ROLLS
    CRATES = '4a5d1df4-d11f-4689-9ee3-9575491f1fef'  # CRATES


class IndustryTypes(str, Enum):
    """IndustryTypes — GET /lookup/IndustryTypes (MasterConstantKey.INDUSTRY_TYPES)."""

    MUSEUM = '6b1ab07d-8d9a-e811-9c34-00155d426802'  # Museum
    RECREATION = 'a21a55d9-0132-497a-a0dc-0714b6474ce8'  # Recreation
    MANUFACTURING_AND_INDUSTRIAL = '12850ba9-ae25-4767-8125-0b07114af08d'  # Manufacturing and Industrial
    BUSINESS_AND_PROFESSIONAL_SERVICES = '037d0e9d-9dfd-4228-95b3-0a64010120e3'  # Business and Professional Services
    TRANSPORTATION_LOGISTICS = '6664ddb1-b7f1-e311-b7f5-000c298b59ee'  # Transportation & Logistics
    ENERGY_AND_UTILITIES = '4e9f03a2-e8c0-4933-bf3d-5c6b658f84cf'  # Energy and Utilities
    RETAIL = '30c87388-a5db-4876-8f86-4a70a3a518cd'  # Retail
    ENGINEERING = '395b267c-7603-4427-ac75-3acdfa978066'  # Engineering
    EDUCATION = 'ee58ec68-fe6b-4dce-b2a9-165d8f4f38d9'  # Education
    HEALTHCARE = '748a9de7-49aa-4c7e-adb8-fc02976c5ade'  # Healthcare
    HOSPITALITY = '6fddba98-a1cc-4cc0-85d1-f59c64c5615d'  # Hospitality
    INFORMATION_TECHNOLOGY_AND_TELECOM = '0c0e868b-2605-4578-8ff7-f370a0ee75ec'  # Information Technology and Telecom
    E_COMMERCE = '74106aa3-ab17-eb11-822b-fcb1a6dfbbb6'  # E-commerce
    EQUIPMENT_BROKER = '609f68de-d929-eb11-822b-fcb1a6dfbbb6'  # Equipment Broker
    STUDENT = 'aac5e24d-e6e0-4b29-b456-f8270e2f9cc9'  # Student
    AUCTION_BUSINESS = '1e0a3719-5c54-4d22-b462-fd1630f0cd3b'  # Auction (Business)
    ART_AND_ANTIQUES = 'c7b3b557-57f3-48c8-890c-91dd8fd9941a'  # Art and Antiques
    RESIDENTIAL_BUSINESS = '3c0e3ef6-1647-ec11-822e-a4aa13c701a3'  # Residential Business
    OTHER = '65a5fa19-5d8f-4f99-a740-a1fc62a27b0c'  # Other
    ESTATE_AND_SENIOR = 'b861828f-54cc-429a-8aa3-82f3c060b3cc'  # Estate and Senior
    INTERIOR_DESIGN = 'c097edf9-7c6d-4623-9cbe-86923de3c8b4'  # Interior Design
    FINANCIAL_SERVICES = '3a8541db-decb-437f-bfde-9309028dca20'  # Financial Services
    ENTERTAINMENT_AND_MEDIA = '665034a9-10bf-4be9-9449-c40d1a160277'  # Entertainment and Media
    GOVERNMENT_AND_DEFENSE = '2c3409ed-346e-4aed-b727-c89d762c9d8e'  # Government and Defense
    HOME_FURNISHINGS = 'edd4ed3b-eb83-4905-8459-ba4a72fff4d6'  # Home Furnishings


class InsuranceOption(str, Enum):
    """InsuranceOption — GET /lookup/InsuranceOption (MasterConstantKey.INSURANCE_OPTION)."""

    MTC_INSURED = 'a2ec2676-d35f-e711-896b-708bcd82aba4'  # MTC Insured
    MTC_DECLINED = 'a3ec2676-d35f-e711-896b-708bcd82aba4'  # MTC Declined
    SELF_INSURED = 'a4ec2676-d35f-e711-896b-708bcd82aba4'  # Self-insured
    PACK_ONLY = 'a5ec2676-d35f-e711-896b-708bcd82aba4'  # Pack Only


class InsuranceType(str, Enum):
    """InsuranceType — GET /lookup/InsuranceType (MasterConstantKey.INSURANCE_TYPE)."""

    NEW = '1e18bb08-25b2-e111-b36c-00155d6b2c30'  # New
    MATURE = 'eea23c05-29b2-e111-b36c-00155d6b2c30'  # Mature
    AF1 = '9e204a2e-29b2-e111-b36c-00155d6b2c30'  # AF1
    AF2 = 'aa6f4e74-29b2-e111-b36c-00155d6b2c30'  # AF2
    AF3 = '66eeed8f-29b2-e111-b36c-00155d6b2c30'  # AF3
    NLS = 'a80291af-29b2-e111-b36c-00155d6b2c30'  # NLS
    PACKAGING_STORE = 'a0400fda-baf7-4b56-99dc-1b43adcb5e14'  # Packaging Store


class ItemNotedConditions(str, Enum):
    """ItemNotedConditions — GET /lookup/ItemNotedConditions (MasterConstantKey.ITEM_NOTED_CONDITIONS)."""

    CRACKED = '9bdb9b25-5859-ef11-ac1c-0a15ce13c9bf'  # Cracked
    SCRATCHED = '9cdb9b25-5859-ef11-ac1c-0a15ce13c9bf'  # Scratched
    DAMAGED = '9ddb9b25-5859-ef11-ac1c-0a15ce13c9bf'  # Damaged


class ItemTypes(str, Enum):
    """ItemTypes — GET /lookup/ItemTypes (MasterConstantKey.ITEM_TYPES)."""

    ARTWORK = 'd7db6e80-0042-40c2-a311-5c54755f8a5f'  # ArtWork
    APOFF = 'b88ca665-0c3a-4b7d-9b13-19a826bc6bef'  # APOff


class JobIntacctStatus(str, Enum):
    """JobIntacctStatus — GET /lookup/JobIntacctStatus (MasterConstantKey.JOB_INTACCT_STATUS)."""

    # No values returned by the API at capture time.
    pass


class JobManagementStatus(str, Enum):
    """Job Management Status — GET /lookup/Job Management Status (MasterConstantKey.JOB_MANAGEMENT_STATUS)."""

    N_1_NEW_JOB = '35b3c7da-1d3f-4755-937f-92c177fa96ca'  # 1 - New Job
    N_8_CARRIER_PICKUP_COMPLETE = 'd8dce069-a45a-4975-8522-974d1b4b03ea'  # 8 - Carrier Pickup Complete
    N_2_2_RECEIVING = '91606d73-a368-42b5-94a3-9b9169183a17'  # 2.2 Receiving
    N_10_DELIVERED = 'd9ec6689-6b0f-4fdf-a92e-b9560a0528bd'  # 10 - Delivered
    N_2_1_PICKUP_IN_PROGRESS = 'dbfcdde3-b55a-4eb2-940d-c64732d84f13'  # 2.1 Pickup in progress
    N_6_STORAGE = 'e7b13009-a4cb-4267-a1a3-fba1c31feace'  # 6 - Storage
    N_9_1_FINAL_MILE_INCOMING = 'a212ee9b-d8c3-41fe-9734-4232c662fbe6'  # 9.1 Final Mile – Incoming
    N_9_4_FINAL_MILE_IN_PROGRESS = 'b231994a-132f-404a-b4c0-3636de860d4a'  # 9.4 Final Mile – In Progress
    N_9_3_FINAL_MILE_SCHEDULED = '1f6ae3bb-176e-473b-84e7-2057560f12e3'  # 9.3 Final Mile – Scheduled
    N_2_SCHEDULED = '9736bc14-cf49-4181-926e-2501312fec3f'  # 2 - Scheduled
    N_7_CARRIER_PICKUP_SCHEDULED = '58748fa9-7b9d-487a-b0c1-6ed3a530b0ce'  # 7 - Carrier Pickup Scheduled
    N_9_FINAL_MILE_IN_PROGRESS = '2d73f273-2fd9-4244-87a4-79e886b6c262'  # 9 - Final Mile in Progress
    N_4_PACKAGING_STARTED = 'a9de6a26-60f4-4db0-a352-5f0ccc488e54'  # 4 - Packaging Started
    N_9_2_FINAL_MILE_ARRIVED = '5c35e2c8-d987-4170-9e66-517ca793c22a'  # 9.2 Final Mile – Arrived
    N_3_RECEIVED = '69f49f71-a3ab-46d8-a54a-53378739c22c'  # 3 - Received
    N_5_PACKAGING_COMPLETED = '4df29f0e-1202-4f9c-b20c-0a68c077eaf8'  # 5 - Packaging Completed


class JobMgmtTypes(str, Enum):
    """JobMgmtTypes — GET /lookup/JobMgmtTypes (MasterConstantKey.JOB_MGMT_TYPES)."""

    INHOUSE = '566ef222-92fe-4659-99de-4ddbcb5cbd01'  # Inhouse
    INBOUND = 'd8de7428-49f8-4913-956f-759af38b4e53'  # Inbound
    LAST_MILE = 'fbffccc3-6461-4bb4-87c4-b688acc240ec'  # Last Mile
    DELIVERED = '05fda338-3723-486b-85b5-aea5d26cfeff'  # Delivered


class JobNoteCategory(str, Enum):
    """JobNoteCategory — GET /lookup/JobNoteCategory (MasterConstantKey.JOB_NOTE_CATEGORY)."""

    HOME_OFFICE = '5e5e88dd-307e-40ac-87ce-edd2e193b905'  # Home Office
    SCHEDULING = 'fcf47517-ac1d-481e-8c7e-f64e1a5507c7'  # Scheduling
    CUSTOMER = '97b6e37c-4464-46d0-ad76-f557c597ac59'  # Customer
    CARRIER_TRANSPORTATION = '1e9cde64-fb56-46b8-acf3-d692cef8983d'  # Carrier Transportation
    DELIVERY = '2e738b14-22e3-4565-b762-a00b76541c14'  # Delivery
    JOB_HISTORY = 'd0e97b6f-2d3f-44fd-b497-7f4a00135178'  # Job History
    EVENT_LOG = 'bdff4ec5-0f8a-4745-8f74-4a6f53c69302'  # Event Log
    ACCESSORIAL_NOTE = '6411f197-c195-4227-8652-4621f0c7417b'  # Accessorial Note
    INVOICE_BILL = 'a9f62697-f48e-49ac-8753-464acfacc60a'  # Invoice/Bill
    PACKAGING = '170db87e-4f21-4754-ab36-475006d42d15'  # Packaging
    PICKUP = '07b1bd49-1903-4554-827b-22a6e20f54ca'  # Pickup
    JOB_HOLD = 'b1d1dd1a-633e-e811-8f3f-00155d426802'  # Job Hold
    STORAGE = '10260505-2db5-44d3-a241-101b8a2d84c8'  # Storage


class JobsStatusTypes(str, Enum):
    """JobsStatusTypes — GET /lookup/JobsStatusTypes (MasterConstantKey.JOBS_STATUS_TYPES)."""

    BOOKED = 'b178547d-02d8-4433-a744-a38987ab4a14'  # Booked
    QUOTED = '1686699a-d4ac-4120-9911-baca36cc3bbc'  # Quoted
    ESTIMATE = 'cc2e2912-82db-4f7e-9312-d3204ed5bff1'  # Estimate
    TEMPLATE = '0172864e-8694-4a63-ab8e-36ee394b5dc9'  # Template
    CANCELLED = '8c5f2cf5-74cc-4f1b-bcb9-6639278fbb75'  # Cancelled
    COMPLETED = 'a986726f-7d14-488d-80f3-69033643c398'  # Completed


class JobType(str, Enum):
    """JobType — GET /lookup/JobType (MasterConstantKey.JOB_TYPE)."""

    PAD_WRAP = 'f1bb0878-6e10-4606-bb59-608583f04f2f'  # Pad-Wrap
    PICK_PACK = '344d7c2e-1004-ec11-89e2-001a7dda710b'  # Pick & Pack
    FULL_JOB = '354d7c2e-1004-ec11-89e2-001a7dda710b'  # Full Job
    LAST_MILE_ONLY = '364d7c2e-1004-ec11-89e2-001a7dda710b'  # Last Mile Only
    N_3PL = '374d7c2e-1004-ec11-89e2-001a7dda710b'  # 3PL
    STORAGE = '384d7c2e-1004-ec11-89e2-001a7dda710b'  # Storage


class OnHoldNextStep(str, Enum):
    """OnHoldNextStep — GET /lookup/OnHoldNextStep (MasterConstantKey.ON_HOLD_NEXT_STEP)."""

    WAIT_FOR_CUSTOMER = 'd47558fb-bca0-ea11-822b-fcb1a6dfbbb6'  # Wait for customer
    ESCALATE = 'd57558fb-bca0-ea11-822b-fcb1a6dfbbb6'  # Escalate


class OnHoldReason(str, Enum):
    """OnHoldReason — GET /lookup/OnHoldReason (MasterConstantKey.ON_HOLD_REASON)."""

    FORCE_MAJEURE = '2521f4c6-f60c-ec11-822b-fcb1a6dfbbb6'  # Force Majeure
    BAD_INFO = '82158430-1f63-e811-9c34-00155d426802'  # Bad Info
    CONTACT_ISSUE = '83158430-1f63-e811-9c34-00155d426802'  # Contact Issue
    ITEM_CHANGE = '84158430-1f63-e811-9c34-00155d426802'  # Item Change
    NO_ITEMS = '85158430-1f63-e811-9c34-00155d426802'  # No Items
    NO_RESPONSE = '86158430-1f63-e811-9c34-00155d426802'  # No Response
    NO_SHOW = '87158430-1f63-e811-9c34-00155d426802'  # No Show
    NOT_READY = '88158430-1f63-e811-9c34-00155d426802'  # Not Ready
    REFUSED = '89158430-1f63-e811-9c34-00155d426802'  # Refused
    SCHED_DELAY = '8a158430-1f63-e811-9c34-00155d426802'  # Sched Delay
    STORAGE = '8b158430-1f63-e811-9c34-00155d426802'  # Storage


class OnHoldResolvedCode(str, Enum):
    """OnHoldRecolvedCode — GET /lookup/OnHoldRecolvedCode (MasterConstantKey.ON_HOLD_RESOLVED_CODE)."""

    LABEL_READY_TO_SCHEDULE = 'd67558fb-bca0-ea11-822b-fcb1a6dfbbb6'  # [Label] ready to schedule
    ITEMS_READY = 'd77558fb-bca0-ea11-822b-fcb1a6dfbbb6'  # Items Ready


class PaymentStatuses(str, Enum):
    """PaymentStatuses — GET /lookup/PaymentStatuses (MasterConstantKey.PAYMENT_STATUSES)."""

    ABANDONED = 'a100cc12-8129-4e83-a881-1185f96bdc67'  # Abandoned
    MICRODEPOSIT_VERIFICATION_REQUIRED = '66201eea-d17d-46ba-a105-4068d4bab4f3'  # Microdeposit verification required
    CANCELED = 'e71a0ff9-f923-e811-8f3f-00155d426802'  # Canceled
    PAID_OUT = '6641ee0d-28c0-e711-8f3f-00155d426802'  # Paid out
    WAITING = '4a93f20c-f591-ed11-abaa-0a1acf9519cf'  # Waiting
    CC_PAY_TO_AGENT = 'a8f84d1f-2dff-4997-99c9-0ed8459f26bd'  # CC pay to agent
    PAYMENT_RCVD = '885d5bcb-7b68-4ad5-8737-9bd665e74c2e'  # Payment Rcvd
    INVOICED = '041a275e-ec05-471d-954b-a33cd5c3a970'  # Invoiced
    DISPUTE = '01904de5-00df-4299-b02d-d1a770db37fa'  # Dispute
    READY_TO_INVOICE = '1d70912e-171c-445d-905d-d291169d762f'  # Ready to invoice
    STARTED = 'a0cc7a8e-6323-479d-89c1-ffec1921e211'  # Started


class PricingToUse(str, Enum):
    """PricingToUse — GET /lookup/PricingToUse (MasterConstantKey.PRICING_TO_USE)."""

    CORPORATE = '1bd75737-21f5-4bdc-af67-b05bb8fbb11e'  # Corporate
    SELF = '4e8e4f3b-65f9-4625-bba0-fad6fa5e7d6e'  # Self
    PARENT_COMPANY = '1fc886e9-9ef4-46bf-8c31-0352786a4af8'  # Parent Company


class QbJobTransType(str, Enum):
    """QBJobTransType — GET /lookup/QBJobTransType (MasterConstantKey.QB_JOB_TRANS_TYPE)."""

    CUSTOMERQUERY = '34e94703-a1cd-49fa-b454-d68a408906aa'  # CustomerQuery
    INVOICEADD = '9da64325-e6f3-45b4-b463-e48648e43a03'  # InvoiceAdd
    BILLADD = 'ae075e74-b788-4ca3-a3d9-e6a75938fb32'  # BillAdd
    CUSTOMERADDMOD = 'd7797141-3164-4d7a-84e6-4f2fcc995a69'  # CustomerAddMod
    NONE = 'f01c247e-aa39-4f12-9af1-3ee36d84e475'  # None


class QbWsTransType(str, Enum):
    """QBWSTransType — GET /lookup/QBWSTransType (MasterConstantKey.QB_WS_TRANS_TYPE)."""

    SENDREQUESTXML = 'fdafc8fb-fb70-4f31-9de7-3e3454489303'  # sendRequestXML
    CONNECTIONERROR = 'd3478202-14f7-417f-ac5a-6152baad61a0'  # connectionError
    RECEIVERESPONSEXML = 'f2abd17a-3061-4b40-b2f0-a5497b3650ad'  # receiveResponseXML
    GETLASTERROR = '3d492403-8593-4b4f-9fe8-d712bd231e19'  # getLastError
    CLOSECONNECTION = '3ba6aa34-d208-4a10-8492-fc2323290a65'  # closeConnection
    AUTHENTICATE = '6f7ee5a0-8b07-4ee8-b139-ea20b5504730'  # authenticate


class ResponsibilityParty(str, Enum):
    """ResponsibilityParty — GET /lookup/ResponsibilityParty (MasterConstantKey.RESPONSIBILITY_PARTY)."""

    HUB = '6f89c42b-0706-49cc-8d7f-1438099f499f'  # Hub
    CARRIER = '7e158430-1f63-e811-9c34-00155d426802'  # Carrier
    CUSTOMER = '7f158430-1f63-e811-9c34-00155d426802'  # Customer
    DEALER = '80158430-1f63-e811-9c34-00155d426802'  # Dealer
    BUYER = '81158430-1f63-e811-9c34-00155d426802'  # Buyer


class RoomTypes(str, Enum):
    """RoomTypes — GET /lookup/RoomTypes (MasterConstantKey.ROOM_TYPES)."""

    KITCHEN = '5dd6b05f-530e-42af-b6ad-88e6d0feccd0'  # Kitchen
    LIVINGROOM = '791fba1b-c322-4e77-b51d-b8146bbab95b'  # LivingRoom
    BEDROOM = '053ca4dc-2502-472b-9e06-4e59c6753871'  # BedRoom


class TransRules(str, Enum):
    """TransRules — GET /lookup/TransRules (MasterConstantKey.TRANS_RULES)."""

    VAN = '2a60d1ee-914c-4363-aea0-04ac7875fbf0'  # VAN
    OCEAN = 'b7e9a7d1-863c-4202-95f6-7306b7497028'  # OCEAN
    PARCEL = '778a28ef-4866-4878-a87a-9fa6333a48a6'  # PARCEL
    AIR2 = 'ab36ee3f-7318-4b55-abb4-e335a39afb72'  # AIR2
    AIR1 = 'ee044ce4-a6e3-46bc-968b-e5c0a763f93d'  # AIR1
    AIR3 = '5f30c1c1-4044-4e7f-b51a-ebe02d48de39'  # AIR3
    LTL = 'd6a05ae8-1c3b-4a0f-ba73-fabc9d496ff3'  # LTL


class TransTypes(str, Enum):
    """TransTypes — GET /lookup/TransTypes (MasterConstantKey.TRANS_TYPES)."""

    ISP = '44268166-337a-41cb-9282-5d5d2b44055b'  # ISP
    NSP = '330b86eb-93fc-4ee5-acf6-7b4248c6e820'  # NSP
    LTL = '48522d39-3738-4700-a7d9-1e19b3bc1cc7'  # LTL


class YesNo(str, Enum):
    """YesNo — GET /lookup/YesNo (MasterConstantKey.YES_NO)."""

    NO = '6f15bd64-ad26-44d6-8923-6b0b3ec2f0cc'  # No
    YES = 'c17716b8-20ed-4874-9d3e-9a1976bb8e15'  # Yes


LOOKUP_CONSTANTS: dict[MasterConstantKey, type[Enum]] = {
    MasterConstantKey.BASIS_TYPES: BasisTypes,
    MasterConstantKey.CANCELLED_TYPES: CancelledTypes,
    MasterConstantKey.C_FILL_TYPE: CFillType,
    MasterConstantKey.COMMODITY_CATEGORY: CommodityCategory,
    MasterConstantKey.COMPANY_TYPES: CompanyTypes,
    MasterConstantKey.CONTACT_TYPES: ContactTypes,
    MasterConstantKey.CONTAINER_TYPE: ContainerType,
    MasterConstantKey.C_PACK_TYPE: CPackType,
    MasterConstantKey.DOCUMENT_TAGS: DocumentTags,
    MasterConstantKey.FOLLOWUP_HEAT_OPTION: FollowupHeatOption,
    MasterConstantKey.FOLLOWUP_PIPELINE_OPTION: FollowupPipelineOption,
    MasterConstantKey.FRANCHISEE_TYPES: FranchiseeTypes,
    MasterConstantKey.FREIGHT_CLASS: FreightClass,
    MasterConstantKey.FREIGHT_TYPES: FreightTypes,
    MasterConstantKey.INDUSTRY_TYPES: IndustryTypes,
    MasterConstantKey.INSURANCE_OPTION: InsuranceOption,
    MasterConstantKey.INSURANCE_TYPE: InsuranceType,
    MasterConstantKey.ITEM_NOTED_CONDITIONS: ItemNotedConditions,
    MasterConstantKey.ITEM_TYPES: ItemTypes,
    MasterConstantKey.JOB_INTACCT_STATUS: JobIntacctStatus,
    MasterConstantKey.JOB_MANAGEMENT_STATUS: JobManagementStatus,
    MasterConstantKey.JOB_MGMT_TYPES: JobMgmtTypes,
    MasterConstantKey.JOB_NOTE_CATEGORY: JobNoteCategory,
    MasterConstantKey.JOBS_STATUS_TYPES: JobsStatusTypes,
    MasterConstantKey.JOB_TYPE: JobType,
    MasterConstantKey.ON_HOLD_NEXT_STEP: OnHoldNextStep,
    MasterConstantKey.ON_HOLD_REASON: OnHoldReason,
    MasterConstantKey.ON_HOLD_RESOLVED_CODE: OnHoldResolvedCode,
    MasterConstantKey.PAYMENT_STATUSES: PaymentStatuses,
    MasterConstantKey.PRICING_TO_USE: PricingToUse,
    MasterConstantKey.QB_JOB_TRANS_TYPE: QbJobTransType,
    MasterConstantKey.QB_WS_TRANS_TYPE: QbWsTransType,
    MasterConstantKey.RESPONSIBILITY_PARTY: ResponsibilityParty,
    MasterConstantKey.ROOM_TYPES: RoomTypes,
    MasterConstantKey.TRANS_RULES: TransRules,
    MasterConstantKey.TRANS_TYPES: TransTypes,
    MasterConstantKey.YES_NO: YesNo,
}


__all__ = [
    "BasisTypes",
    "CancelledTypes",
    "CFillType",
    "CommodityCategory",
    "CompanyTypes",
    "ContactTypes",
    "ContainerType",
    "CPackType",
    "DocumentTags",
    "FollowupHeatOption",
    "FollowupPipelineOption",
    "FranchiseeTypes",
    "FreightClass",
    "FreightTypes",
    "IndustryTypes",
    "InsuranceOption",
    "InsuranceType",
    "ItemNotedConditions",
    "ItemTypes",
    "JobIntacctStatus",
    "JobManagementStatus",
    "JobMgmtTypes",
    "JobNoteCategory",
    "JobsStatusTypes",
    "JobType",
    "OnHoldNextStep",
    "OnHoldReason",
    "OnHoldResolvedCode",
    "PaymentStatuses",
    "PricingToUse",
    "QbJobTransType",
    "QbWsTransType",
    "ResponsibilityParty",
    "RoomTypes",
    "TransRules",
    "TransTypes",
    "YesNo",
    "LOOKUP_CONSTANTS",
]
