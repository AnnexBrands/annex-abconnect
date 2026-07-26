# Test Contract: Contact Search (/contacts/v2/search)

This feature adds no new API contracts. It tests the existing contract defined in `specs/022-fix-contact-search/contracts/contact-search.md`.

## Test Surface

### Request Validation (ContactSearchRequest)

**Input**: `tests/fixtures/requests/ContactSearchRequest.json`

```json
{
  "mainSearchRequest": {
    "contactDisplayId": 1,
    "fullName": "Training",
    "companyName": "Training",
    "companyCode": "Training",
    "email": "training@example.com",
    "phone": "+3334445566",
    "companyDisplayId": 694618
  },
  "loadOptions": {
    "pageNumber": 1,
    "pageSize": 10,
    "sortingBy": "fullName",
    "sortingDirection": 0
  }
}
```

**Permutation strategy**: Load fixture, remove key(s), validate. Optional removals succeed; required removals raise `ValidationError`.

### Response Validation (SearchContactEntityResult)

**Input**: `tests/fixtures/mocks/SearchContactEntityResult.json`

Field-level assertions on mock data:
- `contact_id` = 30760 (int)
- `contact_full_name` = "Emery Brook" (str)
- `contact_email` = "casey.cedar@example.com" (str)
- `company_name` = "Brightwater Interiors" (str)
- `is_prefered` = True (bool)
- `total_records` = 1 (int)
