"""Fixture validation tests for Views models."""

from ab.api.models.views import GridViewAccessEntry, GridViewDetails, StoredProcedureColumn
from tests.conftest import assert_no_extra_fields, require_fixture


class TestViewsModels:
    def test_grid_view_details(self):
        data = require_fixture("GridViewDetails", "GET", "/views/all")
        model = GridViewDetails.model_validate(data)
        assert isinstance(model, GridViewDetails)
        assert_no_extra_fields(model)

    def test_grid_view_access_entry(self):
        """GET /views/{id}/accessinfo returns one grant per row, not a record.

        GridViewAccess (the PUT body) used to serve this too, so every field the
        GET returns was undeclared and the list response could not validate.
        """
        data = require_fixture("GridViewAccessEntry", "GET", "/views/{id}/accessinfo")
        assert isinstance(data, list), "accessinfo returns a collection"
        for row in data:
            model = GridViewAccessEntry.model_validate(row)
            assert isinstance(model, GridViewAccessEntry)
            assert_no_extra_fields(model)

    def test_stored_procedure_column(self):
        data = require_fixture("StoredProcedureColumn", "GET", "/views/datasetsps")
        model = StoredProcedureColumn.model_validate(data)
        assert isinstance(model, StoredProcedureColumn)
        assert_no_extra_fields(model)
