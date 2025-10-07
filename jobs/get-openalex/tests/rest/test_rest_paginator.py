"""Tests for the OpenAlex REST API paginator functionality."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from typing import Dict, Any, List, Union

from polus.aithena.jobs.getopenalex.rest import (
    PaginatorOptions,
    WorksPaginator,
    iter_filtered_works_cursor,
    iter_filtered_works_offset,
    iter_filtered_works_async,
)
from polus.aithena.jobs.getopenalex.rest.paginator import metrics_collector


class TestPaginatorOptions:
    """Test the PaginatorOptions model."""

    def test_defaults(self):
        """Test default values for PaginatorOptions."""
        options = PaginatorOptions(filters={"publication_year": 2020})

        assert options.filters == {"publication_year": 2020}
        assert options.per_page == 25
        assert options.max_results is None
        assert options.cursor_based is True
        assert options.convert_to_model is True
        assert options.async_enabled is False
        assert options.collect_metrics is True

    def test_validation(self):
        """Test validation for PaginatorOptions."""
        # Test valid values
        options = PaginatorOptions(
            filters={"publication_year": 2020},
            per_page=100,
            max_results=500,
            cursor_based=False,
            convert_to_model=False,
            async_enabled=True,
            collect_metrics=False,
        )

        assert options.per_page == 100
        assert options.max_results == 500
        assert options.cursor_based is False
        assert options.convert_to_model is False
        assert options.async_enabled is True
        assert options.collect_metrics is False

        # Test invalid per_page (less than 1)
        with pytest.raises(Exception):
            PaginatorOptions(filters={"publication_year": 2020}, per_page=0)

        # Test invalid per_page (greater than 200)
        with pytest.raises(Exception):
            PaginatorOptions(filters={"publication_year": 2020}, per_page=201)

        # Test extra fields
        with pytest.raises(Exception):
            PaginatorOptions(filters={"publication_year": 2020}, invalid_field="value")


class TestWorksPaginator:
    """Test the WorksPaginator class."""

    def test_init_with_options(self):
        """Test initializing with options object."""
        options = PaginatorOptions(
            filters={"publication_year": 2020}, per_page=50, max_results=100
        )

        with patch("polus.aithena.jobs.getopenalex.rest.paginator.Works") as mock_works:
            mock_instance = MagicMock()
            mock_works.return_value = mock_instance
            mock_instance.filter.return_value = "filtered_query"

            paginator = WorksPaginator(options=options)

            # Verify Works was called and filters were applied
            mock_works.assert_called_once()
            mock_instance.filter.assert_called_with(publication_year=2020)
            assert paginator._query == "filtered_query"
            assert paginator.options == options

    def test_init_with_kwargs(self):
        """Test initializing with keyword arguments."""
        with patch("polus.aithena.jobs.getopenalex.rest.paginator.Works") as mock_works:
            mock_instance = MagicMock()
            mock_works.return_value = mock_instance
            mock_instance.filter.return_value = "filtered_query"

            paginator = WorksPaginator(
                filters={"publication_year": 2020},
                per_page=50,
                max_results=100,
                cursor_based=False,
            )

            # Verify options were created from kwargs
            assert paginator.options.filters == {"publication_year": 2020}
            assert paginator.options.per_page == 50
            assert paginator.options.max_results == 100
            assert paginator.options.cursor_based is False

            # Verify Works was called and filters were applied
            mock_works.assert_called_once()
            mock_instance.filter.assert_called_with(publication_year=2020)
            assert paginator._query == "filtered_query"

    def test_properties(self):
        """Test property accessors."""
        options = PaginatorOptions(
            filters={"publication_year": 2020},
            per_page=50,
            max_results=100,
            cursor_based=False,
            convert_to_model=False,
            async_enabled=True,
            collect_metrics=False,
        )

        with patch("polus.aithena.jobs.getopenalex.rest.paginator.Works"):
            paginator = WorksPaginator(options=options)

            # Test all properties
            assert paginator.filters == {"publication_year": 2020}
            assert paginator.per_page == 50
            assert paginator.max_results == 100
            assert paginator.cursor_based is False
            assert paginator.convert_to_model is False
            assert paginator.async_enabled is True
            assert paginator.collect_metrics is False

    def test_query_property(self):
        """Test the query property with lazy initialization."""
        with patch("polus.aithena.jobs.getopenalex.rest.paginator.Works") as mock_works:
            mock_instance = MagicMock()
            mock_works.return_value = mock_instance
            mock_instance.filter.return_value = "filtered_query"

            # Create paginator with _query = None
            paginator = WorksPaginator(filters={"publication_year": 2020})
            paginator._query = None

            # Access query property to trigger lazy initialization
            query = paginator.query

            # Verify Works was called and filters were applied
            assert mock_works.call_count == 2  # Once in __init__, once in property
            assert mock_instance.filter.call_count == 2
            assert query == "filtered_query"

    @patch("polus.aithena.jobs.getopenalex.rest.paginator.iter_filtered_works_cursor")
    @patch("polus.aithena.jobs.getopenalex.rest.paginator.iter_filtered_works_offset")
    def test_iterator_cursor_based(self, mock_iter_offset, mock_iter_cursor):
        """Test the iterator with cursor-based pagination."""
        # Set up mocks
        mock_iter_cursor.return_value = ["work1", "work2"]

        # Create paginator with cursor_based=True
        paginator = WorksPaginator(
            filters={"publication_year": 2020},
            cursor_based=True,
            per_page=50,
            max_results=100,
            convert_to_model=True,
        )

        # Use the iterator
        results = list(paginator)

        # Verify the correct iterator was used
        assert results == ["work1", "work2"]
        mock_iter_cursor.assert_called_once_with(
            {"publication_year": 2020}, 50, 100, True
        )
        mock_iter_offset.assert_not_called()

    @patch("polus.aithena.jobs.getopenalex.rest.paginator.iter_filtered_works_cursor")
    @patch("polus.aithena.jobs.getopenalex.rest.paginator.iter_filtered_works_offset")
    def test_iterator_offset_based(self, mock_iter_offset, mock_iter_cursor):
        """Test the iterator with offset-based pagination."""
        # Set up mocks
        mock_iter_offset.return_value = ["work3", "work4"]

        # Create paginator with cursor_based=False
        paginator = WorksPaginator(
            filters={"publication_year": 2020},
            cursor_based=False,
            per_page=50,
            max_results=100,
            convert_to_model=True,
        )

        # Use the iterator
        results = list(paginator)

        # Verify the correct iterator was used
        assert results == ["work3", "work4"]
        mock_iter_offset.assert_called_once_with(
            {"publication_year": 2020}, 50, 100, True
        )
        mock_iter_cursor.assert_not_called()

    @pytest.mark.asyncio
    @patch("polus.aithena.jobs.getopenalex.rest.paginator.iter_filtered_works_async")
    async def test_iter_async(self, mock_iter_async):
        """Test the async iterator."""
        # Mock the async iterator
        mock_iter_results = ["work1", "work2"]

        # Create an async generator that yields the mock results
        async def mock_generator():
            for item in mock_iter_results:
                yield item

        mock_iter_async.return_value = mock_generator()

        # Create paginator
        paginator = WorksPaginator(
            filters={"publication_year": 2020},
            per_page=50,
            max_results=100,
            convert_to_model=True,
        )

        # Use the async iterator
        results = []
        async for work in paginator.iter_async():
            results.append(work)

        # Verify results
        assert results == mock_iter_results
        mock_iter_async.assert_called_with({"publication_year": 2020}, 50, 100, True)

    def test_iter_pages_cursor_based(self, mock_works_api):
        """Test iter_pages with cursor-based pagination."""
        # Set up mocks
        mock_works_api.return_value.paginate.return_value = [
            [MagicMock(), MagicMock()],
            [MagicMock(), MagicMock()],
        ]

        # Create paginator with cursor_based=True
        with patch(
            "polus.aithena.jobs.getopenalex.rest.paginator.Works",
            return_value=mock_works_api.return_value,
        ):
            paginator = WorksPaginator(
                filters={"publication_year": 2020},
                cursor_based=True,
                per_page=50,
                max_results=100,
                convert_to_model=False,  # Simplify test by not converting
            )

            # Use iter_pages
            pages = list(paginator.iter_pages())

            # Verify results
            assert len(pages) == 2
            assert len(pages[0]) == 2
            assert len(pages[1]) == 2
            mock_works_api.return_value.paginate.assert_called_with(
                per_page=50, n_max=100
            )

    def test_iter_pages_offset_based(self, mock_works_api):
        """Test iter_pages with offset-based pagination."""
        # Set up mocks for multiple page calls
        mock_works_api.return_value.get.side_effect = [
            {"meta": {"count": 5}, "results": [{"id": "W1"}, {"id": "W2"}]},
            {"meta": {"count": 5}, "results": [{"id": "W3"}, {"id": "W4"}]},
            {"results": []},  # Empty page to end iteration
        ]

        # Create paginator with cursor_based=False
        with patch(
            "polus.aithena.jobs.getopenalex.rest.paginator.PyalexWork"
        ) as mock_pyalex_work:
            mock_pyalex_work.side_effect = lambda data: MagicMock(id=data["id"])

            with patch(
                "polus.aithena.jobs.getopenalex.rest.paginator.Works",
                return_value=mock_works_api.return_value,
            ):
                paginator = WorksPaginator(
                    filters={"publication_year": 2020},
                    cursor_based=False,
                    per_page=2,
                    max_results=10,
                    convert_to_model=False,  # Simplify test by not converting
                )

                # Use iter_pages
                with patch("polus.aithena.jobs.getopenalex.rest.paginator.time.sleep"):
                    pages = list(paginator.iter_pages())

                    # Verify results
                    assert len(pages) == 2
                    assert len(pages[0]) == 2
                    assert len(pages[1]) == 2
                    assert pages[0][0].id == "W1"
                    assert pages[0][1].id == "W2"
                    assert pages[1][0].id == "W3"
                    assert pages[1][1].id == "W4"

                    # Verify API calls
                    assert mock_works_api.return_value.get.call_count == 3
                    mock_works_api.return_value.get.assert_any_call(page=1, per_page=2)
                    mock_works_api.return_value.get.assert_any_call(page=2, per_page=2)
                    mock_works_api.return_value.get.assert_any_call(page=3, per_page=2)

    def test_get_summary(self):
        """Test get_summary method."""
        # Create paginator
        paginator = WorksPaginator(
            filters={"publication_year": 2020},
            per_page=50,
            max_results=100,
            cursor_based=True,
            convert_to_model=True,
            async_enabled=True,
        )

        # Mock metrics
        with patch.object(metrics_collector, "get_summary") as mock_get_summary:
            mock_get_summary.return_value = {"total_requests": 10}

            # Get summary with metrics
            summary = paginator.get_summary()

            # Verify summary
            assert summary["filters"] == {"publication_year": 2020}
            assert summary["per_page"] == 50
            assert summary["max_results"] == 100
            assert summary["cursor_based"] is True
            assert summary["convert_to_model"] is True
            assert summary["async_enabled"] is True
            assert summary["metrics"] == {"total_requests": 10}
            mock_get_summary.assert_called_once()

        # Test with metrics disabled
        paginator.options.collect_metrics = False
        summary = paginator.get_summary()
        assert "metrics" not in summary
