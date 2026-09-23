import requests
import aiohttp
from typing import Optional, Any, Dict, AsyncIterator, Iterator, List, Literal
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from polus.aithena.clinical_aithena.clients.ctgov.models import (
    StudiesResponse,
    CTGovStudy,
)


class CTGovClient:
    """
    Client for accessing ClinicalTrials.gov API v2.

    This client provides both asynchronous and synchronous methods for
    interacting with the ClinicalTrials.gov REST API. All methods that
    fetch studies automatically parse nested sections into proper model
    instances.

    API Documentation: https://clinicaltrials.gov/data-api/api
    """

    BASE_URL = "https://clinicaltrials.gov/api/v2"
    DEFAULT_TIMEOUT = 60.0  # 60 second timeout for API requests
    DEFAULT_MAX_RETRIES = 3  # Maximum number of retry attempts

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Initialize the ClinicalTrials.gov API client.

        Args:
            base_url: Base URL for the API. Defaults to the official API URL.
            timeout: Timeout in seconds for API requests. Defaults to 60 seconds.
            max_retries: Maximum number of retry attempts. Defaults to 3.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def _create_retry_decorator(self, is_async: bool = False):
        """
        Create a retry decorator configured for this client instance.
        
        Retries on timeout and connection errors with exponential backoff.
        
        Args:
            is_async: Whether this decorator is for async functions
        """
        return retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=(
                retry_if_exception_type(requests.Timeout)
                | retry_if_exception_type(requests.ConnectionError)
                | retry_if_exception_type(aiohttp.ClientError)
            ),
            reraise=True,
        )

    @staticmethod
    def _parse_study_sections(study: "CTGovStudy") -> None:
        """
        Parse nested section dicts into proper model instances.

        This is needed because SQLModel with sa_column=Column(JSON) doesn't
        automatically parse nested objects.

        Args:
            study: CTGovStudy instance to parse sections for
        """
        from polus.aithena.clinical_aithena.clients.ctgov.models import (
            ProtocolSection,
            ResultsSection,
            DerivedSection,
            DocumentSection,
            AnnotationSection,
        )

        try:
            if isinstance(study.protocolSection, dict):
                study.protocolSection = ProtocolSection(**study.protocolSection)
                # Extract NCT ID if needed
                if not study.nct_id:
                    if hasattr(study.protocolSection, "identificationModule"):
                        if study.protocolSection.identificationModule:
                            nct = study.protocolSection.identificationModule.nctId
                            study.nct_id = nct
        except Exception:
            pass

        try:
            if isinstance(study.resultsSection, dict):
                study.resultsSection = ResultsSection(**study.resultsSection)
        except Exception:
            pass

        try:
            if isinstance(study.derivedSection, dict):
                study.derivedSection = DerivedSection(**study.derivedSection)
        except Exception:
            pass

        try:
            if isinstance(study.documentSection, dict):
                study.documentSection = DocumentSection(**study.documentSection)
        except Exception:
            pass

        try:
            if isinstance(study.annotationSection, dict):
                study.annotationSection = AnnotationSection(**study.annotationSection)
        except Exception:
            pass

    @staticmethod
    def _prepare_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare query parameters for API request.

        - Converts field names to API aliases (e.g., query_cond -> query.cond)
        - Converts booleans to lowercase strings
        - Converts list parameters to pipe-delimited strings per OpenAPI spec
        - Removes None values

        Args:
            params: Dictionary of parameters

        Returns:
            Cleaned dictionary suitable for API request
        """
        # Mapping of Python field names to API parameter names
        field_aliases = {
            "query_cond": "query.cond",
            "query_term": "query.term",
            "query_locn": "query.locn",
            "query_titles": "query.titles",
            "query_intervention": "query.intervention",
            "query_intr": "query.intr",
            "query_outc": "query.outc",
            "query_spons": "query.spons",
            "query_lead": "query.lead",
            "query_id": "query.id",
            "query_patient": "query.patient",
            "filter_overallStatus": "filter.overallStatus",
            "filter_geo": "filter.geo",
            "filter_ids": "filter.ids",
            "filter_advanced": "filter.advanced",
            "filter_synonyms": "filter.synonyms",
            "postFilter_overallStatus": "postFilter.overallStatus",
            "postFilter_geo": "postFilter.geo",
            "postFilter_ids": "postFilter.ids",
            "postFilter_advanced": "postFilter.advanced",
            "postFilter_synonyms": "postFilter.synonyms",
        }

        # Parameters that should be pipe-delimited per OpenAPI spec
        pipe_delimited_params = {
            "filter.overallStatus",
            "filter.ids",
            "filter.synonyms",
            "postFilter.overallStatus",
            "postFilter.ids",
            "postFilter.synonyms",
            "fields",
            "sort",
            "types",
        }

        cleaned = {}
        for key, value in params.items():
            if value is None:
                continue

            # Convert field name to API alias if needed
            api_key = field_aliases.get(key, key)

            if isinstance(value, bool):
                cleaned[api_key] = str(value).lower()
            elif isinstance(value, list) and api_key in pipe_delimited_params:
                # Convert list to pipe-delimited string
                cleaned[api_key] = "|".join(str(v) for v in value)
            else:
                cleaned[api_key] = value
        return cleaned

    async def studies(
        self,
        format: Literal["json", "csv"] = "json",
        markup_format: Literal["markdown", "legacy"] = "markdown",
        query_cond: Optional[str] = None,
        query_term: Optional[str] = None,
        query_locn: Optional[str] = None,
        query_titles: Optional[str] = None,
        query_intr: Optional[str] = None,
        query_outc: Optional[str] = None,
        query_spons: Optional[str] = None,
        query_lead: Optional[str] = None,
        query_id: Optional[str] = None,
        query_patient: Optional[str] = None,
        filter_overall_status: Optional[List[str]] = None,
        filter_geo: Optional[str] = None,
        filter_ids: Optional[List[str]] = None,
        filter_advanced: Optional[str] = None,
        filter_synonyms: Optional[List[str]] = None,
        post_filter_overall_status: Optional[List[str]] = None,
        post_filter_geo: Optional[str] = None,
        post_filter_ids: Optional[List[str]] = None,
        post_filter_advanced: Optional[str] = None,
        post_filter_synonyms: Optional[List[str]] = None,
        agg_filters: Optional[str] = None,
        geo_decay: Optional[str] = None,
        sort: Optional[List[str]] = None,
        count_total: bool = False,
        page_size: int = 10,
        page_token: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> StudiesResponse:
        """
        Search for clinical trial studies matching query and filter parameters.

        Returns data of studies matching query and filter parameters. The studies
        are returned page by page. If response contains `nextPageToken`, use its
        value in `pageToken` to get next page.

        Query Parameters (Essie Expression Syntax):
            query_cond: "Conditions or disease" search query
            query_term: "Other terms" search query
            query_locn: "Location terms" search query
            query_titles: "Title / acronym" search query
            query_intr: "Intervention / treatment" search query
            query_outc: "Outcome measure" search query
            query_spons: "Sponsor / collaborator" search query
            query_lead: Lead Sponsor Name search query
            query_id: "Study IDs" search query
            query_patient: Patient search query

        Filter Parameters:
            filter_overall_status: Filter by list of statuses (e.g., ["RECRUITING"])
            filter_geo: Filter by distance function, e.g.,
                "distance(39.0035707,-77.1013313,50mi)"
            filter_ids: Filter by list of NCT IDs
            filter_advanced: Advanced filter in Essie expression syntax
            filter_synonyms: Filter by area:synonym_id pairs

        Post-Filter Parameters (same as filters, applied after aggregation):
            post_filter_overall_status: Post-filter by list of statuses
            post_filter_geo: Post-filter by distance function
            post_filter_ids: Post-filter by list of NCT IDs
            post_filter_advanced: Advanced post-filter expression
            post_filter_synonyms: Post-filter by area:synonym_id pairs

        Other Parameters:
            format: Response format - "json" or "csv"
            markup_format: Markup format for text fields - "markdown" or "legacy"
            agg_filters: Apply aggregation filters
            geo_decay: Set proximity factor by distance from filter_geo location.
                Format: "func:(gauss|exp|linear),scale:NNNmi,offset:NNNmi,decay:0.N"
            sort: List of sorting options. Items contain field name and optional
                direction after colon (e.g., ["@relevance", "EnrollmentCount:desc"])
            count_total: Count total number of studies and return in totalCount
            page_size: Maximum number of studies to return (max 1000)
            page_token: Token from previous page's nextPageToken to get next page
            fields: List of field names to return. If unspecified, returns all.
                Can be area names, piece names, or field names.

        Returns:
            StudiesResponse containing:
                - studies: List of CTGovStudy objects
                - nextPageToken: Token for next page (if more pages available)
                - totalCount: Total count (if count_total=True)

        Example:
            >>> client = CTGovClient()
            >>> response = await client.studies(
            ...     query_cond="lung cancer",
            ...     filter_overall_status=["RECRUITING"],
            ...     page_size=20,
            ...     fields=["NCTId", "BriefTitle", "OverallStatus"]
            ... )
            >>> for study in response.studies:
            ...     print(study.nct_id, study.protocolSection.identificationModule.briefTitle)
        """
        params = {
            "format": format,
            "markupFormat": markup_format,
            "query_cond": query_cond,
            "query_term": query_term,
            "query_locn": query_locn,
            "query_titles": query_titles,
            "query_intr": query_intr,
            "query_outc": query_outc,
            "query_spons": query_spons,
            "query_lead": query_lead,
            "query_id": query_id,
            "query_patient": query_patient,
            "filter_overallStatus": filter_overall_status,
            "filter_geo": filter_geo,
            "filter_ids": filter_ids,
            "filter_advanced": filter_advanced,
            "filter_synonyms": filter_synonyms,
            "postFilter_overallStatus": post_filter_overall_status,
            "postFilter_geo": post_filter_geo,
            "postFilter_ids": post_filter_ids,
            "postFilter_advanced": post_filter_advanced,
            "postFilter_synonyms": post_filter_synonyms,
            "aggFilters": agg_filters,
            "geoDecay": geo_decay,
            "sort": sort,
            "countTotal": count_total,
            "pageSize": page_size,
            "pageToken": page_token,
            "fields": fields,
        }
        query_params = self._prepare_query_params(params)
        url = f"{self.base_url}/studies"

        # Retry on timeout and connection errors
        retry_decorator = self._create_retry_decorator(is_async=True)
        
        @retry_decorator
        async def _make_request():
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=query_params) as response:
                    response.raise_for_status()
                    return await response.json()
        
        data = await _make_request()
        result = StudiesResponse(**data)
        # Manually parse nested sections for each study
        for study in result.studies:
            self._parse_study_sections(study)
        return result

    def studies_sync(
        self,
        format: Literal["json", "csv"] = "json",
        markup_format: Literal["markdown", "legacy"] = "markdown",
        query_cond: Optional[str] = None,
        query_term: Optional[str] = None,
        query_locn: Optional[str] = None,
        query_titles: Optional[str] = None,
        query_intr: Optional[str] = None,
        query_outc: Optional[str] = None,
        query_spons: Optional[str] = None,
        query_lead: Optional[str] = None,
        query_id: Optional[str] = None,
        query_patient: Optional[str] = None,
        filter_overall_status: Optional[List[str]] = None,
        filter_geo: Optional[str] = None,
        filter_ids: Optional[List[str]] = None,
        filter_advanced: Optional[str] = None,
        filter_synonyms: Optional[List[str]] = None,
        post_filter_overall_status: Optional[List[str]] = None,
        post_filter_geo: Optional[str] = None,
        post_filter_ids: Optional[List[str]] = None,
        post_filter_advanced: Optional[str] = None,
        post_filter_synonyms: Optional[List[str]] = None,
        agg_filters: Optional[str] = None,
        geo_decay: Optional[str] = None,
        sort: Optional[List[str]] = None,
        count_total: bool = False,
        page_size: int = 10,
        page_token: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> StudiesResponse:
        """
        Synchronous version of studies().

        See studies() for full documentation of parameters and return values.
        """
        params = {
            "format": format,
            "markupFormat": markup_format,
            "query_cond": query_cond,
            "query_term": query_term,
            "query_locn": query_locn,
            "query_titles": query_titles,
            "query_intr": query_intr,
            "query_outc": query_outc,
            "query_spons": query_spons,
            "query_lead": query_lead,
            "query_id": query_id,
            "query_patient": query_patient,
            "filter_overallStatus": filter_overall_status,
            "filter_geo": filter_geo,
            "filter_ids": filter_ids,
            "filter_advanced": filter_advanced,
            "filter_synonyms": filter_synonyms,
            "postFilter_overallStatus": post_filter_overall_status,
            "postFilter_geo": post_filter_geo,
            "postFilter_ids": post_filter_ids,
            "postFilter_advanced": post_filter_advanced,
            "postFilter_synonyms": post_filter_synonyms,
            "aggFilters": agg_filters,
            "geoDecay": geo_decay,
            "sort": sort,
            "countTotal": count_total,
            "pageSize": page_size,
            "pageToken": page_token,
            "fields": fields,
        }
        query_params = self._prepare_query_params(params)
        url = f"{self.base_url}/studies"

        # Retry on timeout and connection errors
        retry_decorator = self._create_retry_decorator(is_async=False)
        
        @retry_decorator
        def _make_request():
            response = requests.get(url, params=query_params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        
        data = _make_request()
        result = StudiesResponse(**data)
        # Manually parse nested sections for each study
        for study in result.studies:
            self._parse_study_sections(study)
        return result

    async def study(
        self,
        nct_id: str,
        format: Literal["json", "csv"] = "json",
        markup_format: Literal["markdown", "legacy"] = "markdown",
        fields: Optional[List[str]] = None,
    ) -> CTGovStudy:
        """
        Fetch a single clinical trial study by its NCT ID.

        Args:
            nct_id: NCT identifier (e.g., "NCT04852770"). If found in NCTIdAlias
                field, will return 301 redirect to the actual study.
            format: Response format - "json" or "csv"
            markup_format: Markup format for text fields - "markdown" or "legacy"
            fields: Optional list of field names to return. Can be area names,
                piece names, or field names. If unspecified, returns all fields.

        Returns:
            CTGovStudy object with all study data

        Raises:
            HTTPError: If study not found (404) or other HTTP errors

        Example:
            >>> client = CTGovClient()
            >>> study = await client.study("NCT04852770")
            >>> print(study.protocolSection.identificationModule.briefTitle)
        """
        url = f"{self.base_url}/studies/{nct_id}"
        params = {
            "format": format,
            "markupFormat": markup_format,
            "fields": fields,
        }
        params = self._prepare_query_params(params)

        # Retry on timeout and connection errors
        retry_decorator = self._create_retry_decorator(is_async=True)
        
        @retry_decorator
        async def _make_request():
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
        
        data = await _make_request()
        study = CTGovStudy(**data)
        self._parse_study_sections(study)
        return study

    def study_sync(
        self,
        nct_id: str,
        format: Literal["json", "csv"] = "json",
        markup_format: Literal["markdown", "legacy"] = "markdown",
        fields: Optional[List[str]] = None,
    ) -> CTGovStudy:
        """
        Synchronous version of study().

        See study() for full documentation of parameters and return values.
        """
        url = f"{self.base_url}/studies/{nct_id}"
        params = {
            "format": format,
            "markupFormat": markup_format,
            "fields": fields,
        }
        params = self._prepare_query_params(params)

        # Retry on timeout and connection errors
        retry_decorator = self._create_retry_decorator(is_async=False)
        
        @retry_decorator
        def _make_request():
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        
        data = _make_request()
        study = CTGovStudy(**data)
        self._parse_study_sections(study)
        return study

    async def fetch_all_studies(
        self,
        format: Literal["json", "csv"] = "json",
        markup_format: Literal["markdown", "legacy"] = "markdown",
        query_cond: Optional[str] = None,
        query_term: Optional[str] = None,
        query_locn: Optional[str] = None,
        query_titles: Optional[str] = None,
        query_intr: Optional[str] = None,
        query_outc: Optional[str] = None,
        query_spons: Optional[str] = None,
        query_lead: Optional[str] = None,
        query_id: Optional[str] = None,
        query_patient: Optional[str] = None,
        filter_overall_status: Optional[List[str]] = None,
        filter_geo: Optional[str] = None,
        filter_ids: Optional[List[str]] = None,
        filter_advanced: Optional[str] = None,
        filter_synonyms: Optional[List[str]] = None,
        post_filter_overall_status: Optional[List[str]] = None,
        post_filter_geo: Optional[str] = None,
        post_filter_ids: Optional[List[str]] = None,
        post_filter_advanced: Optional[str] = None,
        post_filter_synonyms: Optional[List[str]] = None,
        agg_filters: Optional[str] = None,
        geo_decay: Optional[str] = None,
        sort: Optional[List[str]] = None,
        page_size: int = 10,
        fields: Optional[List[str]] = None,
    ) -> AsyncIterator[CTGovStudy]:
        """
        Asynchronous iterator to fetch ALL studies matching query parameters.

        Automatically handles pagination by following nextPageToken until all
        matching studies have been yielded. This is useful for bulk data
        collection or analysis.

        Args: Same as studies() except count_total and page_token are omitted
            (managed internally)

        Yields:
            CTGovStudy objects one at a time

        Example:
            >>> client = CTGovClient()
            >>> async for study in client.fetch_all_studies(
            ...     query_cond="diabetes",
            ...     filter_overall_status=["RECRUITING"],
            ...     page_size=100
            ... ):
            ...     process_study(study)
        """
        params = {
            "format": format,
            "markupFormat": markup_format,
            "query_cond": query_cond,
            "query_term": query_term,
            "query_locn": query_locn,
            "query_titles": query_titles,
            "query_intr": query_intr,
            "query_outc": query_outc,
            "query_spons": query_spons,
            "query_lead": query_lead,
            "query_id": query_id,
            "query_patient": query_patient,
            "filter_overallStatus": filter_overall_status,
            "filter_geo": filter_geo,
            "filter_ids": filter_ids,
            "filter_advanced": filter_advanced,
            "filter_synonyms": filter_synonyms,
            "postFilter_overallStatus": post_filter_overall_status,
            "postFilter_geo": post_filter_geo,
            "postFilter_ids": post_filter_ids,
            "postFilter_advanced": post_filter_advanced,
            "postFilter_synonyms": post_filter_synonyms,
            "aggFilters": agg_filters,
            "geoDecay": geo_decay,
            "sort": sort,
            "pageSize": page_size,
            "fields": fields,
        }
        query_params = self._prepare_query_params(params)
        url = f"{self.base_url}/studies"

        # Remove pageToken if present for full fetch
        query_params.pop("pageToken", None)
        next_page_token = None

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                if next_page_token:
                    query_params["pageToken"] = next_page_token

                async with session.get(url, params=query_params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    response_model = StudiesResponse(**data)

                    for study in response_model.studies:
                        self._parse_study_sections(study)
                        yield study

                    next_page_token = response_model.nextPageToken
                    if not next_page_token:
                        break

    def fetch_all_studies_sync(
        self,
        format: Literal["json", "csv"] = "json",
        markup_format: Literal["markdown", "legacy"] = "markdown",
        query_cond: Optional[str] = None,
        query_term: Optional[str] = None,
        query_locn: Optional[str] = None,
        query_titles: Optional[str] = None,
        query_intr: Optional[str] = None,
        query_outc: Optional[str] = None,
        query_spons: Optional[str] = None,
        query_lead: Optional[str] = None,
        query_id: Optional[str] = None,
        query_patient: Optional[str] = None,
        filter_overall_status: Optional[List[str]] = None,
        filter_geo: Optional[str] = None,
        filter_ids: Optional[List[str]] = None,
        filter_advanced: Optional[str] = None,
        filter_synonyms: Optional[List[str]] = None,
        post_filter_overall_status: Optional[List[str]] = None,
        post_filter_geo: Optional[str] = None,
        post_filter_ids: Optional[List[str]] = None,
        post_filter_advanced: Optional[str] = None,
        post_filter_synonyms: Optional[List[str]] = None,
        agg_filters: Optional[str] = None,
        geo_decay: Optional[str] = None,
        sort: Optional[List[str]] = None,
        page_size: int = 10,
        fields: Optional[List[str]] = None,
    ) -> Iterator[CTGovStudy]:
        """
        Synchronous version of fetch_all_studies().

        See fetch_all_studies() for full documentation.
        """
        params = {
            "format": format,
            "markupFormat": markup_format,
            "query_cond": query_cond,
            "query_term": query_term,
            "query_locn": query_locn,
            "query_titles": query_titles,
            "query_intr": query_intr,
            "query_outc": query_outc,
            "query_spons": query_spons,
            "query_lead": query_lead,
            "query_id": query_id,
            "query_patient": query_patient,
            "filter_overallStatus": filter_overall_status,
            "filter_geo": filter_geo,
            "filter_ids": filter_ids,
            "filter_advanced": filter_advanced,
            "filter_synonyms": filter_synonyms,
            "postFilter_overallStatus": post_filter_overall_status,
            "postFilter_geo": post_filter_geo,
            "postFilter_ids": post_filter_ids,
            "postFilter_advanced": post_filter_advanced,
            "postFilter_synonyms": post_filter_synonyms,
            "aggFilters": agg_filters,
            "geoDecay": geo_decay,
            "sort": sort,
            "pageSize": page_size,
            "fields": fields,
        }
        query_params = self._prepare_query_params(params)
        url = f"{self.base_url}/studies"

        # Remove pageToken if present for full fetch
        query_params.pop("pageToken", None)
        next_page_token = None

        while True:
            if next_page_token:
                query_params["pageToken"] = next_page_token

            response = requests.get(url, params=query_params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            response_model = StudiesResponse(**data)

            for study in response_model.studies:
                self._parse_study_sections(study)
                yield study

            next_page_token = response_model.nextPageToken
            if not next_page_token:
                break

    async def metadata(self) -> Dict[str, Any]:
        """
        Get API and data version information.

        Returns API version (follows Semantic Versioning 2.0.0) and data version
        (UTC timestamp in yyyy-MM-dd'T'HH:mm:ss format).

        Returns:
            Dictionary with:
                - apiVersion: API version string (e.g., "2.0.5")
                - dataTimestamp: Data version timestamp

        Example:
            >>> client = CTGovClient()
            >>> info = await client.metadata()
            >>> print(f"API v{info['apiVersion']}, Data: {info['dataTimestamp']}")
        """
        url = f"{self.base_url}/version"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()

    def metadata_sync(self) -> Dict[str, Any]:
        """
        Synchronous version of metadata().

        See metadata() for full documentation.
        """
        url = f"{self.base_url}/version"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    async def stats(self) -> Dict[str, Any]:
        """
        Get statistics about study JSON sizes.

        Returns statistics including total studies, average size, percentiles,
        size ranges, and information about the largest studies.

        Returns:
            Dictionary with:
                - totalStudies: Total number of studies
                - averageSizeBytes: Average study size in bytes
                - percentiles: Size percentiles (dict)
                - ranges: List of size range distributions
                - largestStudies: List of largest studies with IDs and sizes

        Example:
            >>> client = CTGovClient()
            >>> stats = await client.stats()
            >>> print(f"Total: {stats['totalStudies']}, "
            ...       f"Avg size: {stats['averageSizeBytes']} bytes")
        """
        url = f"{self.base_url}/stats/size"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()

    def stats_sync(self) -> Dict[str, Any]:
        """
        Synchronous version of stats().

        See stats() for full documentation.
        """
        url = f"{self.base_url}/stats/size"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    async def field_values_stats(
        self,
        types: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get value statistics for study leaf fields.

        Returns statistics about field values including unique value counts,
        missing value counts, and top values with their frequencies.

        Args:
            types: Optional list of field types to filter by. Valid types:
                - "ENUM": Enumeration fields
                - "STRING": String fields
                - "DATE": Date fields
                - "INTEGER": Integer fields
                - "NUMBER": Number fields
                - "BOOLEAN": Boolean fields
            fields: Optional list of field names/paths to filter by.
                Can be piece names (e.g., "Phase") or full field paths
                (e.g., "protocolSection.armsInterventionsModule.armGroups.interventionNames")

        Returns:
            List of field statistics, each containing:
                - field: Field name
                - piece: Piece name
                - type: Field type
                - uniqueValuesCount: Number of unique values
                - missingStudiesCount: Number of studies missing this field
                - topValues: List of most common values with counts
                - Additional type-specific statistics

        Example:
            >>> client = CTGovClient()
            >>> stats = await client.field_values_stats(
            ...     types=["ENUM"],
            ...     fields=["Phase", "OverallStatus"]
            ... )
            >>> for field_stat in stats:
            ...     print(f"{field_stat['field']}: "
            ...           f"{field_stat['uniqueValuesCount']} unique values")
        """
        url = f"{self.base_url}/stats/field/values"
        params = {}
        if types:
            params["types"] = types
        if fields:
            params["fields"] = fields
        params = self._prepare_query_params(params)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    def field_values_stats_sync(
        self,
        types: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous version of field_values_stats().

        See field_values_stats() for full documentation.
        """
        url = f"{self.base_url}/stats/field/values"
        params = {}
        if types:
            params["types"] = types
        if fields:
            params["fields"] = fields
        params = self._prepare_query_params(params)

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    async def list_field_sizes(
        self,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get size statistics for list/array fields.

        Returns information about how many items are typically in list fields,
        including min/max sizes and distribution of sizes across studies.

        To search studies by a list field size, use AREA[FieldName:size] search
        operator. For example: AREA[Phase:size] 2 finds studies with 2 phases.

        Args:
            fields: Optional list of field names/paths to filter by.
                Can be piece names (e.g., "Phase", "Condition") or full paths.
                If unspecified, returns statistics for all list fields.

        Returns:
            List of list field size statistics, each containing:
                - field: Field name
                - piece: Piece name
                - uniqueSizesCount: Number of unique list sizes observed
                - minSize: Minimum list size (optional)
                - maxSize: Maximum list size (optional)
                - topSizes: Most common list sizes with study counts

        Example:
            >>> client = CTGovClient()
            >>> sizes = await client.list_field_sizes(fields=["Phase"])
            >>> for field in sizes:
            ...     print(f"{field['field']}: {field['minSize']}-{field['maxSize']}")
        """
        url = f"{self.base_url}/stats/field/sizes"
        params = {}
        if fields:
            params["fields"] = fields
        params = self._prepare_query_params(params)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    def list_field_sizes_sync(
        self,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous version of list_field_sizes().

        See list_field_sizes() for full documentation.
        """
        url = f"{self.base_url}/stats/field/sizes"
        params = {}
        if fields:
            params["fields"] = fields
        params = self._prepare_query_params(params)

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    async def studies_metadata(
        self,
        include_indexed_only: bool = False,
        include_historic_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Get study data model field metadata.

        Returns detailed information about all fields in the study data model,
        including field names, types, descriptions, and relationships. Useful
        for understanding the structure of study data and for constructing
        queries.

        Args:
            include_indexed_only: Include indexed-only fields if True. These
                fields are indexed for searching but may not be present in
                returned study data.
            include_historic_only: Include fields available only in historic
                data if True. These fields are no longer collected for new
                studies but exist in older records.

        Returns:
            List of field nodes, each containing:
                - name: Field name
                - piece: Piece name
                - type: Field type
                - sourceType: Source data type
                - title: Human-readable title (optional)
                - description: Field description (optional)
                - children: Nested child fields (for complex types)
                - Additional metadata (dedLink, rules, etc.)

        Example:
            >>> client = CTGovClient()
            >>> fields = await client.studies_metadata()
            >>> for field in fields:
            ...     print(f"{field['name']} ({field['type']}): "
            ...           f"{field.get('description', 'No description')}")
        """
        url = f"{self.base_url}/studies/metadata"
        params = {
            "includeIndexedOnly": include_indexed_only,
            "includeHistoricOnly": include_historic_only,
        }
        params = self._prepare_query_params(params)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    def studies_metadata_sync(
        self,
        include_indexed_only: bool = False,
        include_historic_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Synchronous version of studies_metadata().

        See studies_metadata() for full documentation.
        """
        url = f"{self.base_url}/studies/metadata"
        params = {
            "includeIndexedOnly": include_indexed_only,
            "includeHistoricOnly": include_historic_only,
        }
        params = self._prepare_query_params(params)

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    async def search_areas(self) -> Dict[str, Any]:
        """
        Get search areas documentation.

        Returns information about available search areas (also called search
        documents) and their parts. Search areas define what can be searched
        using the query.* parameters.

        Returns:
            List of search documents, each containing:
                - name: Document name (e.g., "Study", "Participant")
                - areas: List of search areas, each with:
                    - name: Area name (e.g., "ConditionSearch", "BasicSearch")
                    - param: Query parameter name (optional)
                    - uiLabel: UI display label (optional)
                    - parts: List of search parts with field mappings

        Example:
            >>> client = CTGovClient()
            >>> areas = await client.search_areas()
            >>> for doc in areas:
            ...     print(f"Document: {doc['name']}")
            ...     for area in doc['areas']:
            ...         print(f"  - {area['name']}")
        """
        url = f"{self.base_url}/studies/search-areas"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()

    def search_areas_sync(self) -> Dict[str, Any]:
        """
        Synchronous version of search_areas().

        See search_areas() for full documentation.
        """
        url = f"{self.base_url}/studies/search-areas"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    async def enums(self) -> Dict[str, Any]:
        """
        Get enumeration types and their values.

        Returns all enum types used in the study data model along with their
        possible values, legacy values, and any piece-specific exceptions.

        Returns:
            List of enum info objects, each containing:
                - type: Enum type name (e.g., "Status", "Phase", "Sex")
                - pieces: List of data piece names that use this enum
                - values: List of enum values, each with:
                    - value: Current enum value
                    - legacyValue: Value used in legacy API
                    - exceptions: Map of piece names to alternative legacy values

        Example:
            >>> client = CTGovClient()
            >>> enums = await client.enums()
            >>> for enum in enums:
            ...     print(f"{enum['type']}: {len(enum['values'])} values")
            ...     for val in enum['values']:
            ...         print(f"  - {val['value']}")
        """
        url = f"{self.base_url}/studies/enums"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()

    def enums_sync(self) -> Dict[str, Any]:
        """
        Synchronous version of enums().

        See enums() for full documentation.
        """
        url = f"{self.base_url}/studies/enums"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

