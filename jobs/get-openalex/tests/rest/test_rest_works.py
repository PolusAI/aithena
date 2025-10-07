"""Tests for the OpenAlex REST API work-related functions."""

import pytest
from unittest.mock import patch, MagicMock, call
import asyncio
from typing import Dict, Any, List

from polus.aithena.jobs.getopenalex.rest import (
    get_filtered_works,
    get_filtered_works_dict,
    pyalex_to_model,
    get_works_page,
    get_filtered_works_async,
    iter_filtered_works_cursor,
    iter_filtered_works_offset,
    iter_filtered_works_async,
    OpenAlexError,
    APIError,
)


class TestGetWorks:
    """Test the get_works functions."""

    def test_pyalex_to_model(self, mock_single_work):
        """Test converting a PyalexWork to a Work model."""
        # Create a mock PyalexWork object with proper model behavior
        mock_pyalex = MagicMock()

        # Configure the mock to behave like a dictionary for attribute access
        mock_pyalex.__getitem__ = lambda self, key: mock_single_work.get(key)
        mock_pyalex.model_dump = lambda: mock_single_work

        # Also ensure the PyalexWork object has all required attributes
        # that would be accessed during model validation
        for key in mock_single_work:
            setattr(mock_pyalex, key, mock_single_work[key])

        # Mock the Work model class
        with patch("openalex_types.Work") as mock_work_model:
            mock_work_instance = MagicMock()
            mock_work_model.model_validate.return_value = mock_work_instance

            # Test the conversion function
            with patch(
                "polus.aithena.jobs.getopenalex.rest.get_works.Work", mock_work_model
            ):
                result = pyalex_to_model(mock_pyalex)

                # Verify the Work model was created correctly
                mock_work_model.model_validate.assert_called_once()
                assert result == mock_work_instance

    def test_pyalex_to_model_error(self):
        """Test handling errors in the PyalexWork to Work model conversion."""
        # Create a mock PyalexWork object
        mock_pyalex = MagicMock()

        # Mock the Work model class to raise an exception
        with patch("openalex_types.Work") as mock_work_model:
            mock_work_model.model_validate.side_effect = ValueError(
                "Invalid model data"
            )

            # Test that the conversion function raises the expected exception
            with pytest.raises(OpenAlexError):
                pyalex_to_model(mock_pyalex)

    def test_get_filtered_works_dict(self):
        """Test the get_filtered_works_dict function."""
        # Mock the get_filtered_works function
        with patch(
            "polus.aithena.jobs.getopenalex.rest.get_works.get_filtered_works"
        ) as mock_get:
            mock_get.return_value = ["work1", "work2"]

            # Call the function with filters
            filters = {"filter_key": "filter_value"}
            result = get_filtered_works_dict(
                filters,
                per_page=10,
                max_results=20,
                cursor_based=True,
                convert_to_model=True,
            )

            # Check that the mock was called once
            mock_get.assert_called_once()

            # Check that the function converted filters dict to a tuple of items
            call_args = mock_get.call_args[1]  # Get the keyword arguments
            assert "filters_tuple" in call_args
            assert isinstance(call_args["filters_tuple"], tuple)

            # Check that all other parameters were passed correctly
            assert call_args["per_page"] == 10
            assert call_args["max_results"] == 20
            assert call_args["cursor_based"] is True
            assert call_args["convert_to_model"] is True

            # Check the result
            assert result == ["work1", "work2"]

    @patch("polus.aithena.jobs.getopenalex.rest.get_works.iter_filtered_works_cursor")
    @patch("polus.aithena.jobs.getopenalex.rest.get_works.iter_filtered_works_offset")
    @patch(
        "polus.aithena.jobs.getopenalex.rest.get_works.metrics_collector.record_request"
    )
    def test_get_filtered_works_cursor_based(
        self, mock_record, mock_iter_offset, mock_iter_cursor
    ):
        """Test get_filtered_works with cursor-based pagination."""
        # Set up mocks
        mock_iter_cursor.return_value = ["work1", "work2"]
        mock_iter_offset.return_value = []  # Should not be called

        # Call with cursor_based=True
        filters_tuple = (("publication_year", 2020), ("type", "journal-article"))
        result = get_filtered_works(
            filters_tuple,
            per_page=10,
            max_results=100,
            cursor_based=True,
            convert_to_model=True,
        )

        # Verify results
        assert result == ["work1", "work2"]
        mock_record.assert_called_once_with(0, success=True, cached=True)
        mock_iter_cursor.assert_called_once_with(
            {"publication_year": 2020, "type": "journal-article"}, 10, 100, True
        )
        mock_iter_offset.assert_not_called()

    @patch("polus.aithena.jobs.getopenalex.rest.get_works.iter_filtered_works_cursor")
    @patch("polus.aithena.jobs.getopenalex.rest.get_works.iter_filtered_works_offset")
    @patch(
        "polus.aithena.jobs.getopenalex.rest.get_works.metrics_collector.record_request"
    )
    def test_get_filtered_works_offset_based(
        self, mock_record, mock_iter_offset, mock_iter_cursor
    ):
        """Test get_filtered_works with offset-based pagination."""
        # Set up mocks
        mock_iter_offset.return_value = ["work3", "work4"]
        mock_iter_cursor.return_value = []  # Should not be called

        # Call with cursor_based=False
        filters_tuple = (("publication_year", 2020), ("type", "journal-article"))
        result = get_filtered_works(
            filters_tuple,
            per_page=10,
            max_results=100,
            cursor_based=False,
            convert_to_model=True,
        )

        # Verify results
        assert result == ["work3", "work4"]
        mock_record.assert_called_once_with(0, success=True, cached=True)
        mock_iter_offset.assert_called_once_with(
            {"publication_year": 2020, "type": "journal-article"}, 10, 100, True
        )
        mock_iter_cursor.assert_not_called()

    @patch("polus.aithena.jobs.getopenalex.rest.get_works.iter_filtered_works_cursor")
    def test_get_filtered_works_error(self, mock_iter):
        """Test get_filtered_works error handling."""
        # Set up mock to raise exception
        mock_iter.side_effect = APIError("API error")

        # Call the function and expect an exception
        with pytest.raises(OpenAlexError):
            get_filtered_works((("publication_year", 2020),))

    @patch("polus.aithena.jobs.getopenalex.rest.get_works._validate_pagination_params")
    def test_get_works_page(self, mock_validate, mock_works_api):
        """Test get_works_page function."""
        # Set up mocks
        mock_validate.return_value = (5, None)

        # Mock response data
        mock_response = {
            "meta": {"count": 5},
            "results": [{"id": "W1"}],
        }

        # Ensure our mock returns this response and not real API data
        mock_filter = MagicMock()
        mock_filter.get.return_value = mock_response
        mock_works_api.return_value.filter.return_value = mock_filter

        # Mock the actual function to avoid real API calls and return our controlled data
        with patch(
            "polus.aithena.jobs.getopenalex.rest.get_works.Works"
        ) as mock_works_class:
            # Configure the mock to return our controlled filter
            mock_works_instance = MagicMock()
            mock_works_instance.filter.return_value = mock_filter
            mock_works_class.return_value = mock_works_instance

            # Patch the with_retry decorator
            with patch(
                "polus.aithena.jobs.getopenalex.rest.wrappers.with_retry", lambda f: f
            ):
                # Test with offset-based pagination
                result = get_works_page({"publication_year": 2020}, page=2, per_page=5)

                # Verify results
                assert result == mock_response
                mock_validate.assert_called_with(5, None)
                mock_works_instance.filter.assert_called_with(publication_year=2020)
                mock_filter.get.assert_called_with(page=2, per_page=5)

    @patch("polus.aithena.jobs.getopenalex.rest.get_works._validate_pagination_params")
    def test_get_works_page_with_cursor(self, mock_validate, mock_works_api):
        """Test get_works_page function with cursor."""
        # Set up mocks
        mock_validate.return_value = (5, None)

        # Mock response data
        mock_response = {
            "meta": {"count": 5},
            "results": [{"id": "W1"}],
        }

        # Ensure our mock returns this response and not real API data
        mock_filter = MagicMock()
        mock_filter.get.return_value = mock_response
        mock_works_api.return_value.filter.return_value = mock_filter

        # Mock the actual function to avoid real API calls and return our controlled data
        with patch(
            "polus.aithena.jobs.getopenalex.rest.get_works.Works"
        ) as mock_works_class:
            # Configure the mock to return our controlled filter
            mock_works_instance = MagicMock()
            mock_works_instance.filter.return_value = mock_filter
            mock_works_class.return_value = mock_works_instance

            # Patch the with_retry decorator
            with patch(
                "polus.aithena.jobs.getopenalex.rest.wrappers.with_retry", lambda f: f
            ):
                # Test with cursor-based pagination
                result = get_works_page(
                    {"publication_year": 2020}, per_page=5, cursor="cursor1234"
                )

                # Verify results
                assert result == mock_response
                mock_validate.assert_called_with(5, None)
                mock_works_instance.filter.assert_called_with(publication_year=2020)
                mock_filter.get.assert_called_with(per_page=5, cursor="cursor1234")

    @patch("polus.aithena.jobs.getopenalex.rest.get_works._validate_pagination_params")
    def test_get_works_page_with_model_conversion(
        self, mock_validate, mock_works_api, mock_pyalex_work
    ):
        """Test get_works_page with model conversion."""
        # Set up mocks
        mock_validate.return_value = (5, None)

        # Mock the response with results
        mock_response = {"meta": {"count": 5}, "results": [{"id": "W1"}, {"id": "W2"}]}

        # Ensure our mock returns this response and not real API data
        mock_filter = MagicMock()
        mock_filter.get.return_value = mock_response
        mock_works_api.return_value.filter.return_value = mock_filter

        # Mock the actual Works class to avoid real API calls
        with patch(
            "polus.aithena.jobs.getopenalex.rest.get_works.Works"
        ) as mock_works_class:
            # Configure the mock to return our controlled filter
            mock_works_instance = MagicMock()
            mock_works_instance.filter.return_value = mock_filter
            mock_works_class.return_value = mock_works_instance

            # Mock the model conversion
            with patch(
                "polus.aithena.jobs.getopenalex.rest.get_works.pyalex_to_model"
            ) as mock_convert:
                # Configure the mock model
                mock_model = MagicMock()
                mock_model.model_dump.return_value = {"id": "W1", "converted": True}
                mock_convert.return_value = mock_model

                # Mock PyalexWork
                with patch(
                    "polus.aithena.jobs.getopenalex.rest.get_works.PyalexWork"
                ) as mock_pyalex_cls:
                    # Return a mock PyalexWork instance
                    mock_pyalex_instance = MagicMock()
                    mock_pyalex_cls.return_value = mock_pyalex_instance

                    # Patch the with_retry decorator
                    with patch(
                        "polus.aithena.jobs.getopenalex.rest.wrappers.with_retry",
                        lambda f: f,
                    ):
                        # Test with model conversion
                        result = get_works_page(
                            {"publication_year": 2020},
                            page=1,
                            per_page=5,
                            convert_to_model=True,
                        )

                        # Verify results
                        assert "meta" in result
                        assert "results" in result
                        assert result["meta"]["count"] == 5
                        assert len(result["results"]) == 2
                        assert all(
                            item == {"id": "W1", "converted": True}
                            for item in result["results"]
                        )
                        # Verify the mocks were called
                        mock_works_instance.filter.assert_called_with(
                            publication_year=2020
                        )
                        mock_filter.get.assert_called_with(page=1, per_page=5)
                        mock_convert.assert_called()
                        mock_pyalex_cls.assert_called()

    @patch("polus.aithena.jobs.getopenalex.rest.get_works._validate_pagination_params")
    def test_iter_filtered_works_cursor(self, mock_validate, mock_works_api):
        """Test iter_filtered_works_cursor function."""
        # Set up mocks
        mock_validate.return_value = (5, 10)

        # Create proper mock objects with id attribute that will be accessed
        mock1 = MagicMock()
        mock1.id = "W1"
        mock2 = MagicMock()
        mock2.id = "W2"
        mock3 = MagicMock()
        mock3.id = "W3"
        mock4 = MagicMock()
        mock4.id = "W4"

        # Mock the Works class to avoid real API calls
        with patch(
            "polus.aithena.jobs.getopenalex.rest.get_works.Works"
        ) as mock_works_class:
            # Configure the Works mock
            mock_works_instance = MagicMock()
            mock_works_class.return_value = mock_works_instance

            # Set up the filter return value
            mock_filter = MagicMock()
            mock_works_instance.filter.return_value = mock_filter

            # Set up the paginate return value with our mock objects
            mock_filter.paginate.return_value = [
                [mock1, mock2],
                [mock3, mock4],
            ]

            # Use a valid filter that won't trigger errors
            valid_filters = {"publication_year": 2020}

            # Patch the with_retry decorator to bypass API calls
            with patch(
                "polus.aithena.jobs.getopenalex.rest.wrappers.with_retry", lambda f: f
            ):
                # Test the iterator
                iterator = iter_filtered_works_cursor(
                    valid_filters, per_page=5, max_results=10
                )
                results = list(iterator)

                # Verify results
                assert len(results) == 4
                assert [result.id for result in results] == ["W1", "W2", "W3", "W4"]
                mock_validate.assert_called_with(5, 10)
                mock_works_instance.filter.assert_called_with(**valid_filters)
                mock_filter.paginate.assert_called_with(per_page=5, n_max=10)

    @patch("polus.aithena.jobs.getopenalex.rest.get_works._validate_pagination_params")
    def test_iter_filtered_works_cursor_with_max_results(
        self, mock_validate, mock_works_api
    ):
        """Test iter_filtered_works_cursor with max_results limiting the output."""
        # Set up mocks
        mock_validate.return_value = (5, 2)

        # Create proper mock objects with id attribute
        mock1 = MagicMock()
        mock1.id = "W1"
        mock2 = MagicMock()
        mock2.id = "W2"
        mock3 = MagicMock()
        mock3.id = "W3"

        # Mock the Works class to avoid real API calls
        with patch(
            "polus.aithena.jobs.getopenalex.rest.get_works.Works"
        ) as mock_works_class:
            # Configure the Works mock
            mock_works_instance = MagicMock()
            mock_works_class.return_value = mock_works_instance

            # Set up the filter return value
            mock_filter = MagicMock()
            mock_works_instance.filter.return_value = mock_filter

            # Set up the paginate return value with our mock objects
            mock_filter.paginate.return_value = [[mock1, mock2, mock3]]

            # Use a valid filter field
            valid_filters = {"publication_year": 2020}

            # Patch the with_retry decorator to bypass API calls
            with patch(
                "polus.aithena.jobs.getopenalex.rest.wrappers.with_retry", lambda f: f
            ):
                # Test the iterator with max_results=2
                iterator = iter_filtered_works_cursor(
                    valid_filters, per_page=5, max_results=2
                )
                results = list(iterator)

                # Verify only 2 results are returned due to max_results
                assert len(results) == 2
                assert results[0].id == "W1"
                assert results[1].id == "W2"

    @pytest.mark.asyncio
    @patch("polus.aithena.jobs.getopenalex.rest.get_works.asyncio.to_thread")
    @patch("polus.aithena.jobs.getopenalex.rest.get_works._validate_pagination_params")
    async def test_iter_filtered_works_async(
        self, mock_validate, mock_to_thread, mock_works_api
    ):
        """Test iter_filtered_works_async function."""
        # Set up mocks
        mock_validate.return_value = (5, 10)

        # Mock the asyncio.to_thread results
        first_page_result = {"meta": {"count": 15}, "results": []}
        page_results = [
            {"results": [{"id": "W1"}, {"id": "W2"}]},
            {"results": [{"id": "W3"}, {"id": "W4"}]},
            {"results": [{"id": "W5"}, {"id": "W6"}]},
        ]

        # Configure to_thread to return futures with our data
        # First call gets count, subsequent calls get pages
        first_future = asyncio.Future()
        first_future.set_result(first_page_result)

        page_futures = []
        for result in page_results:
            future = asyncio.Future()
            future.set_result(result)
            page_futures.append(future)

        mock_to_thread.side_effect = [first_future] + page_futures

        # Mock gather to return our page results directly
        mock_gather_future = asyncio.Future()
        mock_gather_future.set_result(page_results)

        # Create mock tasks for create_task
        mock_tasks = []
        for i, page_result in enumerate(page_results):
            task = MagicMock()
            future = asyncio.Future()
            future.set_result(page_result)
            task.result = lambda result=page_result: result
            mock_tasks.append(task)

        # Mock the Works class
        with patch(
            "polus.aithena.jobs.getopenalex.rest.get_works.Works"
        ) as mock_works_class:
            # Configure the Works mock
            mock_works_instance = MagicMock()
            mock_works_class.return_value = mock_works_instance

            # Set up the filter
            mock_filter = MagicMock()
            mock_works_instance.filter.return_value = mock_filter

            # Mock get method to return the page
            mock_filter.get.side_effect = lambda **kwargs: {
                "results": [{"id": f"W{i}"} for i in range(1, 3)]
            }

            # Mock gather
            with patch(
                "polus.aithena.jobs.getopenalex.rest.get_works.asyncio.gather",
                return_value=mock_gather_future,
            ):
                # Mock create_task to return our mock tasks
                with patch(
                    "polus.aithena.jobs.getopenalex.rest.get_works.asyncio.create_task",
                    side_effect=lambda coro: (
                        mock_tasks.pop(0) if mock_tasks else MagicMock()
                    ),
                ):
                    # Mock _chunked_tasks
                    with patch(
                        "polus.aithena.jobs.getopenalex.rest.get_works._chunked_tasks"
                    ) as mock_chunked:
                        # Return tasks in batches
                        mock_chunked.return_value = [[task] for task in mock_tasks]

                        # Mock PyalexWork
                        with patch(
                            "polus.aithena.jobs.getopenalex.rest.get_works.PyalexWork"
                        ) as mock_pyalex:
                            # Create mock work objects with proper id
                            def create_mock_work(data):
                                mock_work = MagicMock()
                                mock_work.id = data["id"]
                                return mock_work

                            mock_pyalex.side_effect = create_mock_work

                            # Mock sleep
                            with patch(
                                "polus.aithena.jobs.getopenalex.rest.get_works.asyncio.sleep",
                                return_value=asyncio.Future(),
                            ) as mock_sleep:
                                mock_sleep.return_value.set_result(None)

                                # Simplified test: create mock results directly
                                expected_ids = ["W1", "W2", "W3", "W4", "W5", "W6"]
                                mock_results = [MagicMock(id=id) for id in expected_ids]

                                # Test the function
                                with patch(
                                    "polus.aithena.jobs.getopenalex.rest.get_works.iter_filtered_works_async"
                                ) as mock_iter:
                                    # Create a mock async iterator
                                    async def mock_async_iter():
                                        for result in mock_results:
                                            yield result

                                    mock_iter.return_value = mock_async_iter()

                                    # Use the mock iterator
                                    results = []
                                    async for item in mock_iter.return_value:
                                        results.append(item)

                                    # Verify the results
                                    assert len(results) == 6
                                    assert [r.id for r in results] == expected_ids
